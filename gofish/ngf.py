# Another poorly documented file format

from gofish.constants import *
from gofish.tree import *
from gofish.utils import *

def parse_ngf(ngf):

    ngf = ngf.strip()
    lines = ngf.split("\n")

    try:
        boardsize = int(lines[1])
        handicap = int(lines[5])
        pw = lines[2].split()[0]
        pb = lines[3].split()[0]
        rawdate = lines[8][0:8]
        komi = float(lines[7])

        if handicap == 0 and int(komi) == komi:
            komi += 0.5

    except (IndexError, ValueError):
        boardsize = 19
        handicap = 0
        pw = ""
        pb = ""
        rawdate = ""
        komi = 0

    if handicap < 0 or handicap > 9:
        raise ParserFail

    root = Node(parent = None)
    node = root

    # Set root values...

    root.set_value("SZ", boardsize)

    if handicap >= 2:
        root.set_value("HA", handicap)
        stones = handicap_points(boardsize, handicap)
        for point in stones:
            root.add_value("AB", string_from_point(point[0], point[1]))

    if komi:
        root.set_value("KM", komi)

    if len(rawdate) == 8:
        ok = True
        for n in range(8):
            if rawdate[n] not in "0123456789":
                ok = False
        if ok:
            date = rawdate[0:4] + "-" + rawdate[4:6] + "-" + rawdate[6:8]
            root.set_value("DT", date)

    if pw:
        root.safe_commit("PW", pw)
    if pb:
        root.safe_commit("PB", pb)

    # Main parser...

    for line in lines:
        line = line.strip().upper()

        if len(line) >= 7:
            if line[0:2] == "PM":
                if line[4] in ["B", "W"]:

                    key = line[4]

                    # Not at all sure, but assuming coordinates from top left.

                    # Also, coordinates are from 1-19, but with "B" representing
                    # the digit 1. (Presumably "A" would represent 0.)

                    x = ord(line[5]) - 65       # Therefore 65 is correct
                    y = ord(line[6]) - 65

                    try:
                        value = string_from_point(x, y)
                    except ValueError:
                        continue

                    node = Node(parent = node)
                    node.set_value(key, value)

    if len(root.children) == 0:     # We'll assume we failed in this case
        raise ParserFail

    return root
