# .gib is a file format used by the Tygem server, it's undocumented.
# I know nothing about how it specifies board size or variations.
# I've inferred from other source code how it does handicaps.

from gofish.constants import *
from gofish.tree import *

def parse_gib(gib):

    root = Node(parent = None)
    node = root

    lines = gib.split("\n")

    for line in lines:
        line = line.strip()

        if line.startswith("\\[GAMEBLACKNAME=") and line.endswith("\\]"):
            s = line[16:-2]
            root.safe_commit("PB", s)

        if line.startswith("\\[GAMEWHITENAME=") and line.endswith("\\]"):
            s = line[16:-2]
            root.safe_commit("PW", s)

        if line[0:3] == "INI":

            if node is not root:
                raise ParserFail

            setup = line.split()

            try:
                handicap = int(setup[3])
            except IndexError:
                continue

            if handicap < 0 or handicap > 9:
                raise ParserFail

            if handicap >= 2:
                node.set_value("HA", handicap)
                stones = handicap_points_19[handicap]
                for point in stones:
                    node.add_value("AB", string_from_point(point[0], point[1]))

        if line[0:3] == "STO":

            move = line.split()

            key = "B" if move[3] == "1" else "W"

            # Although one source claims the coordinate system numbers from the bottom left in range 0 to 18,
            # various other pieces of evidence lead me to believe it numbers from the top left (like SGF).
            # In particular, I tested some .gib files on http://gokifu.com

            try:
                x = int(move[4]) + 1
                y = int(move[5]) + 1
            except IndexError:
                continue

            try:
                value = string_from_point(x, y)
            except ValueError:
                continue

            node = Node(parent = node)
            node.set_value(key, value)

    if len(root.children) == 0:     # We'll assume we failed in this case
        raise ParserFail

    return root
