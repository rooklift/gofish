# .gib is a file format used by the Tygem server, it's undocumented.
# I know nothing about how it specifies board size or variations.
# I've inferred from other source code how it does handicaps.

from gofish.constants import *
from gofish.tree import *
from gofish.utils import *

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

        if line.startswith("\\[GAMERESULT="):
            score = None
            strings = line.split()
            for s in strings:           # This is very crude
                try:
                    score = float(s)
                except:
                    pass
            if "white" in line.lower() and "black" not in line.lower():
                if "resignation" in line.lower():
                    root.set_value("RE", "W+R")
                elif score:
                    root.set_value("RE", "W+{}".format(score))
                else:
                    root.set_value("RE", "W+")
            if "black" in line.lower() and "white" not in line.lower():
                if "resignation" in line.lower():
                    root.set_value("RE", "B+R")
                elif score:
                    root.set_value("RE", "B+{}".format(score))
                else:
                    root.set_value("RE", "B+")

        if line.startswith("\\[GAMECONDITION="):
            if "black 6.5 dum" in line.lower():     # Just hard-coding the typical case; we should maybe extract komi by regex
                root.set_value("KM", 6.5)
            elif "black 7.5 dum" in line.lower():   # Perhaps komi becomes 7.5 in the future...
                root.set_value("KM", 7.5)
            elif "black 0.5 dum" in line.lower():   # Do these exist on Tygem?
                root.set_value("KM", 0.5)

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
                stones = handicap_points(19, handicap, tygem = True)
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
