# This format better documented than some, see:
# http://homepages.cwi.nl/~aeb/go/misc/ugf.html

from gofish.constants import *
from gofish.tree import *

def parse_ugf(ugf):     # Note that the files are often (always?) named .ugi

    root = None

    boardsize = None
    handicap = None

    handicap_stones_set = 0

    coordinate_type = ""

    lines = ugf.split("\n")

    data_section = False

    for line in lines:

        line = line.strip().upper()     # Note this

        if not data_section:

            if line == "[DATA]":
                if handicap is None or boardsize is None:
                    raise ParserFail

                data_section = True

                if boardsize < 1 or boardsize > 19 or handicap < 0:
                    raise ParserFail

                root = Node(parent = None)
                node = root

                if handicap >= 2:
                    root.set_value("HA", handicap)
                    # The stones apparently get set as normal moves in .ugf

            elif line.startswith("HDCP="):
                sval = line.split("=")[1].split(",")[0]  # Think this can't IndexError
                try:
                    handicap = int(sval)
                except:
                    continue

            elif line.startswith("SIZE="):
                sval = line.split("=")[1].split(",")[0]  # Think this can't IndexError
                try:
                    boardsize = int(sval)
                except:
                    continue

            elif line.startswith("COORDINATETYPE="):
                coordinate_type = line.split("=")[1].split(",")[0]  # Think this can't IndexError

        else:
            slist = line.split(",")
            try:
                x_chr = slist[0][0]
                y_chr = slist[0][1]
                colour = slist[1][0]
            except IndexError:
                continue

            try:
                node_chr = slist[2][0]
            except IndexError:
                node_chr = ""

            if colour not in ["B", "W"]:
                continue

            if coordinate_type == "IGS":        # apparently "IGS" format is from the bottom left
                x = ord(x_chr) - 64
                y = (boardsize - (ord(y_chr) - 64)) + 1
            else:
                x = ord(x_chr) - 64
                y = ord(y_chr) - 64

            if x > boardsize or x < 1 or y > boardsize or y < 1:    # Likely a pass, "YA" is often used as a pass
                value = ""
            else:
                try:
                    value = string_from_point(x, y)
                except ValueError:
                    continue

            # In case of the initial handicap placement, don't create a new node...

            if handicap >= 2 and handicap_stones_set != handicap and node_chr == "0" and colour == "B" and node is root:
                handicap_stones_set += 1
                key = "AB"
                node.add_value(key, value)      # add_value not set_value
            else:
                node = Node(parent = node)
                key = colour
                node.set_value(key, value)


    if root is None:
        raise ParserFail

    if len(root.children) == 0:     # We'll assume we failed in this case
        raise ParserFail

    return root
