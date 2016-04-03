def is_star_point(x, y, boardsize):
    good_x, good_y = False, False

    if boardsize >= 15 or x == y:
        if x == (boardsize + 1) / 2:
            good_x = True
        if y == (boardsize + 1) / 2:
            good_y = True

    if boardsize >= 12:
        if x == 4 or x + 4 == boardsize + 1:
            good_x = True
        if y == 4 or y + 4 == boardsize + 1:
            good_y = True
    else:
        if x == 3 or x + 3 == boardsize + 1:
            good_x = True
        if y == 3 or y + 3 == boardsize + 1:
            good_y = True

    if good_x and good_y:
        return True
    else:
        return False


def points_from_points_string(s, boardsize):        # convert SGF "aa" or "cd:jf" into set of points
    ret = set()

    if len(s) < 2:
        return ret

    left = ord(s[0]) - 96
    top = ord(s[1]) - 96
    right = ord(s[-2]) - 96         # This works regardless of
    bottom = ord(s[-1]) - 96        # the format ("aa" or "cd:jf")

    if left > right:
        left, right = right, left
    if top > bottom:
        top, bottom = bottom, top

    for x in range(left, right + 1):
        for y in range(top, bottom + 1):
            if 1 <= x <= boardsize and 1 <= y <= boardsize:
                ret.add((x,y))

    return ret


def string_from_point(x, y):                        # convert x, y into SGF coordinate e.g. "pd"
    if x < 1 or x > 26 or y < 1 or y > 26:
        raise ValueError
    s = ""
    s += chr(x + 96)
    s += chr(y + 96)
    return s


def english_string_from_point(x, y, boardsize):     # 16, 4     --->    Q16  (skips I, numbers from bottom)
    xlookup = " ABCDEFGHJKLMNOPQRSTUVWXYZ"
    s = ""
    s += xlookup[x]
    s += str((boardsize - y) + 1)
    return s


def point_from_english_string(s, boardsize):        # Q16       --->    16, 4
    if len(s) not in [2,3]:
        return None

    s = s.upper()

    xlookup = " ABCDEFGHJKLMNOPQRSTUVWXYZ"

    try:
        x = xlookup.index(s[0])
    except:
        return None

    try:
        y = boardsize - int(s[1:]) + 1
    except:
        return None

    if 1 <= x <= boardsize and 1 <= y <= boardsize:
        return x, y
    else:
        return None


def adjacent_points(x, y, boardsize):
    result = set()

    for i, j in [
        (x - 1, y),
        (x + 1, y),
        (x, y - 1),
        (x, y + 1),
    ]:
        if i >= 1 and i <= boardsize and j >= 1 and j <= boardsize:
            result.add((i, j))

    return result


def safe_string(s):     # "safe" meaning safely escaped \ and ] characters
    s = str(s)
    safe_s = ""
    for ch in s:
        if ch in ["\\", "]"]:
            safe_s += "\\"
        safe_s += ch
    return safe_s


def handicap_points(boardsize, handicap, tygem = False):

    points = set()

    if boardsize < 4:
        return points

    if handicap > 9:
        handicap = 9

    if boardsize < 13:
        d = 2
    else:
        d = 3

    if handicap >= 2:
        points.add((boardsize - d, 1 + d))
        points.add((1 + d, boardsize - d))

    # Experiments suggest Tygem puts its 3rd handicap stone in the top left

    if handicap >= 3:
        if tygem:
            points.add((1 + d, 1 + d))
        else:
            points.add((boardsize - d, boardsize - d))

    if handicap >= 4:
        if tygem:
            points.add((boardsize - d, boardsize - d))
        else:
            points.add((1 + d, 1 + d))

    if boardsize % 2 == 0:      # No handicap > 4 on even sided boards
        return points

    mid = (boardsize + 1) // 2

    if handicap in [5, 7, 9]:
        points.add((mid, mid))

    if handicap >= 6:
        points.add((1 + d, mid))
        points.add((boardsize - d, mid))

    if handicap >= 8:
        points.add((mid, 1 + d))
        points.add((mid, boardsize - d))

    return points
