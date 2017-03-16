# .gib is a file format used by the Tygem server, it's undocumented.
# I know nothing about how it specifies board size or variations.
# I've inferred from other source code how it does handicaps.

import re

from gofish.constants import *
from gofish.tree import *
from gofish.utils import *

def gib_make_result(grlt, zipsu):

    easycases = {3: "B+R", 4: "W+R", 7: "B+T", 8: "W+T"}

    if grlt in easycases:
        return easycases[grlt]

    if grlt in [0, 1]:
        if grlt == 0:
            winner = "B"
        else:
            winner = "W"
        margin = (zipsu / 10)
        return "{}+{}".format(winner, margin)

    return ""


def gib_get_result(line, grlt_regex, zipsu_regex):
    try:
        grlt = int(re.search(grlt_regex, line).group(1))
        zipsu = int(re.search(zipsu_regex, line).group(1))
    except:
        return ""
    return gib_make_result(grlt, zipsu)


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

        if line.startswith("\\[GAMEINFOMAIN="):

            if "RE" not in root.properties:
                result = gib_get_result(line, r"GRLT:(\d+),", r"ZIPSU:(\d+),")
                if result:
                    root.set_value("RE", result)

            if "KM" not in root.properties:
                try:
                    komi = int(re.search(r"GONGJE:(\d+),", line).group(1)) / 10
                    if komi:
                        root.set_value("KM", komi)
                except:
                    pass

        if line.startswith("\\[GAMETAG="):

            if "DT" not in root.properties:
                try:
                    match = re.search(r"C(\d\d\d\d):(\d\d):(\d\d)", line)
                    date = "{}-{}-{}".format(match.group(1), match.group(2), match.group(3))
                    root.set_value("DT", date)
                except:
                    pass

            if "RE" not in root.properties:
                result = gib_get_result(line, r",W(\d+),", r",Z(\d+),")
                if result:
                    root.set_value("RE", result)

            if "KM" not in root.properties:
                try:
                    komi = int(re.search(r",G(\d+),", line).group(1)) / 10
                    if komi:
                        root.set_value("KM", komi)
                except:
                    pass

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
