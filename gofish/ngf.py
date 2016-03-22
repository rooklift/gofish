# Another poorly documented file format

from gofish.constants import *
from gofish.tree import *

def parse_ngf(ngf):

    ngf = ngf.strip()
    lines = ngf.split("\n")

    try:
        boardsize = int(lines[1])
        handicap = int(lines[5])
    except (IndexError, ValueError):
        raise ParserFail

    if boardsize < 1 or boardsize > 19 or handicap < 0 or handicap > 9:
        raise ParserFail

    if boardsize < 19 and handicap:     # Can't be bothered
        raise ParserFail

    root = Node(parent = None)
    node = root

    if handicap >= 2:
        node.set_value("HA", handicap)
        stones = handicap_points_19[handicap]
        for point in stones:
            node.add_value("AB", string_from_point(point[0], point[1]))

    for line in lines:
        line = line.strip().upper()

        if len(line) >= 7:
            if line[0:2] == "PM":
                if line[4] in ["B", "W"]:

                    key = line[4]

                    # Not at all sure, but assuming coordinates from top left.

                    # Also, coordinates are from 1-19, but with "B" representing
                    # the digit 1. (Presumably "A" would represent 0.)

                    x = ord(line[5]) - 65
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
