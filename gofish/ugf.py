# This format better documented than some, see:
# http://homepages.cwi.nl/~aeb/go/misc/ugf.html

from gofish.constants import *
from gofish.tree import *

def parse_ugf(ugf):     # Note that the files are often (always?) named .ugi

    root = Node(parent = None)
    node = root

    boardsize = None
    handicap = None

    handicap_stones_set = 0

    coordinate_type = ""

    lines = ugf.split("\n")

    section = None

    for line in lines:

        line = line.strip()

        try:
            if line[0] == "[" and line[-1] == "]":

                section = line.upper()

                if section == "[DATA]":

                    # Since we're entering the data section, we need to ensure we have
                    # gotten sane info from the header; check this now...

                    if handicap is None or boardsize is None:
                        raise ParserFail
                    if boardsize < 1 or boardsize > 19 or handicap < 0:
                        raise ParserFail

                continue

        except IndexError:
            pass

        if section == "[HEADER]":

            if line.upper().startswith("HDCP="):
                try:
                    handicap_str = line.split("=")[1].split(",")[0]
                    handicap = int(handicap_str)
                    if handicap >= 2:
                        root.set_value("HA", handicap)      # The actual stones are placed in the data section

                    komi_str = line.split("=")[1].split(",")[1]
                    komi = float(komi_str)
                    root.set_value("KM", komi)
                except:
                    continue

            elif line.upper().startswith("SIZE="):
                size_str = line.split("=")[1]
                try:
                    boardsize = int(size_str)
                    root.set_value("SZ", boardsize)
                except:
                    continue

            elif line.upper().startswith("COORDINATETYPE="):
                coordinate_type = line.split("=")[1].upper()

            # Note that the properties that aren't being converted to int/float need to use the .safe_commit() method...

            elif line.upper().startswith("PLAYERB="):
                root.safe_commit("PB", line[8:])

            elif line.upper().startswith("PLAYERW="):
                root.safe_commit("PW", line[8:])

            elif line.upper().startswith("PLACE="):
                root.safe_commit("PC", line[6:])

            elif line.upper().startswith("TITLE="):
                root.safe_commit("GN", line[6:])

            # Determine the winner...

            elif line.upper().startswith("WINNER=B"):
                root.set_value("RE", "B+")

            elif line.upper().startswith("WINNER=W"):
                root.set_value("RE", "W+")

        elif section == "[DATA]":

            line = line.upper()

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

    if len(root.children) == 0:     # We'll assume we failed in this case
        raise ParserFail

    return root
