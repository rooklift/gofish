import copy, sys


EMPTY, BLACK, WHITE = 0, 1, 2


class OffBoard(Exception): pass
class BadBoardSize(Exception): pass
class ParserFail(Exception): pass
class WrongNode(Exception): pass


handicap_points_19 = {
    0: [],
    1: [],
    2: [(16,4), (4,16)],
    3: [(16,4), (4,16), (16,16)],
    4: [(16,4), (4,16), (16,16), (4, 4)],
    5: [(16,4), (4,16), (16,16), (4, 4), (10, 10)],
    6: [(16,4), (4,16), (16,16), (4, 4), (4, 10), (16, 10)],
    7: [(16,4), (4,16), (16,16), (4, 4), (4, 10), (16, 10), (10, 10)],
    8: [(16,4), (4,16), (16,16), (4, 4), (4, 10), (16, 10), (10, 4), (10, 16)],
    9: [(16,4), (4,16), (16,16), (4, 4), (4, 10), (16, 10), (10, 4), (10, 16), (10, 10)]
}


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


def points_from_points_string(s, boardsize):     # convert "aa" or "cd:jf" into set of points

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


def string_from_point(x, y):
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


def save_file(filename, node):
    node = node.get_root_node()
    with open(filename, "w", encoding="utf-8") as outfile:
        write_tree(outfile, node)


def write_tree(outfile, node):      # Relies on values already being correctly backslash-escaped
    outfile.write("(")
    while 1:
        outfile.write(";")
        for key in node.properties:
            outfile.write(key)
            for value in node.properties[key]:
                outfile.write("[{}]".format(value))
        if len(node.children) > 1:
            for child in node.children:
                write_tree(outfile, child)
            break
        elif len(node.children) == 1:
            node = node.children[0]
            continue
        else:
            break
    outfile.write(")\n")
    return


class Board():                          # Internally the arrays are 1 too big, with 0 indexes being ignored (so we can use indexes 1 to 19)
    def __init__(self, boardsize):
        self.boardsize = boardsize
        self.stones_checked = set()     # Used when searching for liberties
        self.state = []
        for x in range(self.boardsize + 1):
            ls = list()
            for y in range(self.boardsize + 1):
                ls.append(0)
            self.state.append(ls)

    def dump(self, highlight = None):

        if highlight is None:
            highlightx, highlighty = None, None
        else:
            highlightx, highlighty = highlight[0], highlight[1]

        pieces = {EMPTY: ".", BLACK: "*", WHITE: "O"}

        for row in range(1, self.boardsize + 1):
            for col in range(0, self.boardsize + 1):        # Start from 0 so we have space to print the highlight if it's at col 1

                end = " "
                if row == highlighty:
                    if col + 1 == highlightx:
                        end = "["
                    elif col == highlightx:
                        end = "]"

                if col == 0:                # Remember that the real board starts at 1
                    print(" ", end=end)
                elif self.state[col][row] == EMPTY and is_star_point(col, row, self.boardsize):
                    print("+", end=end)
                else:
                    print(pieces[self.state[col][row]], end=end)
            print()

    def group_has_liberties(self, x, y):
        assert(x >= 1 and x <= self.boardsize and y >= 1 and y <= self.boardsize)
        self.stones_checked = set()
        return self.__group_has_liberties(x, y)

    def __group_has_liberties(self, x, y):
        assert(x >= 1 and x <= self.boardsize and y >= 1 and y <= self.boardsize)
        colour = self.state[x][y]
        assert(colour in [BLACK, WHITE])

        self.stones_checked.add((x,y))

        for i, j in adjacent_points(x, y, self.boardsize):
            if self.state[i][j] == EMPTY:
                return True
            if self.state[i][j] == colour:
                if (i,j) not in self.stones_checked:
                    if self.__group_has_liberties(i, j):
                        return True
        return False

    def play_move(self, colour, x, y):
        assert(colour in [BLACK, WHITE])

        opponent = BLACK if colour == WHITE else WHITE

        if x < 1 or x > self.boardsize or y < 1 or y > self.boardsize:
            raise OffBoard

        self.state[x][y] = colour

        for i, j in adjacent_points(x, y, self.boardsize):
            if self.state[i][j] == opponent:
                if not self.group_has_liberties(i, j):
                    self.destroy_group(i, j)

        # Check for and deal with suicide:

        if not self.group_has_liberties(x, y):
            self.destroy_group(x, y)

    def destroy_group(self, x, y):
        assert(x >= 1 and x <= self.boardsize and y >= 1 and y <= self.boardsize)
        colour = self.state[x][y]
        assert(colour in [BLACK, WHITE])

        self.state[x][y] = EMPTY

        for i, j in adjacent_points(x, y, self.boardsize):
            if self.state[i][j] == colour:
                self.destroy_group(i, j)


class Node():
    def __init__(self, parent):
        self.properties = dict()
        self.children = []
        self.board = None
        self.moves_made = 0
        self.is_main_line = False
        self.parent = parent

        if parent:
            parent.children.append(self)

    def update(self):             # Use the properties to modify the board...

        # A node "should" have only 1 of "B" or "W", and only 1 value in the list.
        # The result will be wrong if the specs are violated. Whatever.

        movers = {"B": BLACK, "W": WHITE}

        for mover in movers:
            if mover in self.properties:
                movestring = self.properties[mover][0]
                try:
                    x = ord(movestring[0]) - 96
                    y = ord(movestring[1]) - 96
                    self.board.play_move(movers[mover], x, y)
                except (IndexError, OffBoard):
                    pass
                self.moves_made += 1        # Consider off-board / passing moves as moves for counting purposes
                                            # (incidentally, old SGF sometimes uses an off-board move to mean pass)

        # A node can have all of "AB", "AW" and "AE"
        # Note that adding a stone doesn't count as "playing" it and can
        # result in illegal positions (the specs allow this explicitly)

        adders = {"AB": BLACK, "AW": WHITE, "AE": EMPTY}

        for adder in adders:
            if adder in self.properties:
                for value in self.properties[adder]:
                    for point in points_from_points_string(value, self.board.boardsize):    # only returns points inside the board boundaries
                        x, y = point[0], point[1]
                        self.board.state[x][y] = adders[adder]

    def update_recursive(self):                     # Only goes recursive if 2 or more children
        node = self
        while 1:
            node.update()
            if len(node.children) == 0:
                return
            elif len(node.children) == 1:           # i.e. just iterate where possible
                node.copy_state_to_child(node.children[0])
                node = node.children[0]
                continue
            else:
                for child in node.children:
                    node.copy_state_to_child(child)
                    child.update_recursive()
                return

    def fix_main_line_status(self):
        if self.parent is None or self.parent.is_main_line:
            self.is_main_line = True
        else:
            self.is_main_line = False

    def fix_main_line_status_recursive(self):       # Only goes recursive if 2 or more children
        node = self
        while 1:
            node.fix_main_line_status()
            if len(node.children) == 0:
                return
            elif len(node.children) == 1:           # i.e. just iterate where possible
                node = node.children[0]
                continue
            else:
                for child in node.children:
                    child.fix_main_line_status_recursive()
                return

    def copy_state_to_child(self, child):
        if len(self.children) > 0:
            if child is self.children[0]:
                if self.is_main_line:
                    child.is_main_line = True

        child.board = copy.deepcopy(self.board)
        child.moves_made = self.moves_made

    def dump(self, include_comments = True):
        for key in sorted(self.properties):
            values = self.properties[key]
            if include_comments or key != "C":
                print("  {}".format(key), end="")
                for value in values:
                    try:
                        print("[{}]".format(value), end="")        # Sometimes fails on Windows to Unicode errors
                    except:
                        print("[ --- Exception when trying to print value --- ]", end="")
                print()

    def print_comments(self):
        s = self.get_unescaped_concat("C")
        if s:
            print("[{}] ".format(self.moves_made), end="")
            for ch in s:
                try:
                    print(ch, end="")
                except:
                    print("?", end="")
            print("\n")

    def get_unescaped_concat(self, key):
        s = ""
        if key in self.properties:
            for value in self.properties[key]:
                escape_mode = False
                for ch in value:
                    if escape_mode:
                        escape_mode = False
                    elif ch == "\\":
                        escape_mode = True
                        continue
                    s += ch
        return s

    def safe_commit(self, key, value):      # Note: destroys the key if value is ""
        safe_s = safe_string(value)
        if safe_s:
            self.properties[key] = [safe_s]
        else:
            try:
                self.properties.pop(key)
            except KeyError:
                pass

    def what_was_the_move(self):        # Assumes one move at most, which the specs also insist on.
        for key in ["B", "W"]:
            if key in self.properties:
                movestring = self.properties[key][0]
                try:
                    x = ord(movestring[0]) - 96
                    y = ord(movestring[1]) - 96
                    if 1 <= x <= self.board.boardsize and 1 <= y <= self.board.boardsize:
                        return (x, y)
                except IndexError:
                    pass
        return None

    def move_was_pass(self):
        for key in ["B", "W"]:
            if key in self.properties:
                movestring = self.properties[key][0]
                if len(movestring) < 2:                     # e.g. W[]
                    return True
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                if x < 1 or x > self.board.boardsize or y < 1 or y > self.board.boardsize:      # e.g. W[tt]
                    return True
        return False

    def sibling_moves(self):        # Don't use this to check for variations - a node might not have any moves
        p = self.parent
        if p is None:
            return set()
        if len(p.children) == 1:
            return set()
        moves = set()
        index = p.children.index(self)
        for n, node in enumerate(p.children):
            if n != index:
                move = node.what_was_the_move()
                if move is not None:
                    moves.add(move)
        return moves

    def sibling_count(self):
        if self.parent is None:
            return 0
        else:
            return len(self.parent.children) - 1

    def get_end_node(self):         # Iterate down the (local) main line and return the end node
        node = self
        while 1:
            if len(node.children) > 0:
                node = node.children[0]
            else:
                break
        return node

    def get_root_node(self):        # Iterate up to the root and return it
        node = self
        while 1:
            if node.parent:
                node = node.parent
            else:
                break
        return node

    def add_value(self, key, value):        # Note that, if improperly used, could lead to odd nodes like ;B[ab][cd]
        if key not in self.properties:
            self.properties[key] = []
        if str(value) not in self.properties[key]:
            self.properties[key].append(str(value))

    def set_value(self, key, value):        # Like the above, but only allows the node to have 1 value for this key
        self.properties[key] = [str(value)]

    def debug(self):
        self.board.dump()
        print()
        self.dump()
        print()
        print("  -- self:         {}".format(self))
        print("  -- parent:       {}".format(self.parent))
        print("  -- siblings:     {}".format(self.sibling_count()))
        print("  -- children:     {}".format(len(self.children)))
        print("  -- is main line: {}".format(self.is_main_line))
        print("  -- moves made:   {}".format(self.moves_made))
        print()

    def last_colour_played(self):   # Return the most recent colour played in this node or any ancestor
        node = self
        while 1:
            if "B" in node.properties:
                return BLACK
            if "W" in node.properties:
                return WHITE
            if "AB" in node.properties and "AW" not in node.properties:
                return BLACK
            if "AW" in node.properties and "AB" not in node.properties:
                return WHITE
            if node.parent == None:
                return None
            node = node.parent

    def move_colour(self):
        if "B" in self.properties:
            return BLACK
        elif "W" in self.properties:
            return WHITE
        else:
            return None

    def make_child_from_move(self, colour, x, y, append = True):
        assert(colour in [BLACK, WHITE])

        if x < 1 or x > self.board.boardsize or y < 1 or y > self.board.boardsize:
            raise OffBoard

        if append:
            child = Node(parent = self)             # This automatically appends the child to this node
        else:
            child = Node(parent = None)

        self.copy_state_to_child(child)

        key = "W" if colour == WHITE else "B"
        child.set_value(key, string_from_point(x, y))
        child.update()
        return child

    def try_move(self, x, y, colour = None):        # Try the move... if it's legal, create and return the child; else return None
                                                    # Don't use this while reading SGF, as even illegal moves should be allowed there

        if x < 1 or x > self.board.boardsize or y < 1 or y > self.board.boardsize:
            return None
        if self.board.state[x][y] != EMPTY:
            return None

        # if the move already exists, just return the (first) relevant child...

        for child in self.children:
            if child.what_was_the_move() == (x, y):
                return child

        # Colour can generally be auto-determined by what colour the last move was...

        if colour == None:
            colour = WHITE if self.last_colour_played() == BLACK else BLACK      # If it was None we get BLACK
        else:
            assert(colour in [BLACK, WHITE])

        # Check for legality...

        testchild = self.make_child_from_move(colour, x, y, append = False)  # Won't get appended to this node as a real child
        if self.parent:
            if testchild.board.state == self.parent.board.state:     # Ko
                return None
        if testchild.board.state[x][y] == EMPTY:     # Suicide
            return None

        # Make real child and return...

        child = self.make_child_from_move(colour, x, y)
        return child

    def make_pass(self):

        # Colour is auto-determined by what colour the last move was...

        colour = WHITE if self.last_colour_played() == BLACK else BLACK      # If it was None we get BLACK

        # if the pass already exists, just return the (first) relevant child...

        for child in self.children:
            if child.move_colour() == colour:
                if child.move_was_pass():
                    return child

        key = "W" if colour == WHITE else "B"

        child = Node(parent = self)
        self.copy_state_to_child(child)
        child.set_value(key, "")
        child.update()
        return child

    def add_stone(self, colour, x, y):

        # This is intended to be used on the root node to add handicap stones or setup
        # for a problem. Otherwise it will generally raise an exception (e.g. if a move
        # is present in the node, which it usually will be).

        assert(colour in [BLACK, WHITE])

        if x < 1 or x > self.board.boardsize or y < 1 or y > self.board.boardsize:
            raise OffBoard

        if len(self.children) > 0:      # Can't add stones this way when the node has children (should we be able to?)
            raise WrongNode

        if "B" in self.properties or "W" in self.properties:
            raise WrongNode

        key = "AW" if colour == WHITE else "AB"
        s = string_from_point(x, y)

        self.add_value(key, s)
        self.update()


def new_tree(size):             # Returns a ready-to-use tree with board
    if size > 19 or size < 1:
        raise BadBoardSize

    root = Node(parent = None)
    root.board = Board(size)
    root.is_main_line = True
    root.set_value("FF", 4)
    root.set_value("GM", 1)
    root.set_value("CA", "UTF-8")
    root.set_value("SZ", size)
    return root


def load(filename):

    try:
        with open(filename, encoding="utf8") as infile:
            contents = infile.read()
    except UnicodeDecodeError:
        print("Opening as UTF-8 failed, trying Latin-1\n")
        with open(filename, encoding="latin1") as infile:       # I think this can't actually fail, but it might corrupt
            contents = infile.read()

    # FileNotFoundError is just allowed to bubble up

    try:
        root = parse_sgf(contents)
    except ParserFail:
        if filename[-4:].lower() == ".gib":
            print("Parsing as SGF failed, trying to parse as GIB")
            root = parse_gib(contents)      # This itself can also raise ParserFail
        elif filename[-4:].lower() == ".ngf":
            print("Parsing as SGF failed, trying to parse as NGF")
            root = parse_ngf(contents)      # This itself can also raise ParserFail
        else:
            raise

    root.set_value("FF", 4)
    root.set_value("GM", 1)
    root.set_value("CA", "UTF-8")   # Force UTF-8

    if "SZ" in root.properties:
        size = int(root.properties["SZ"][0])
    else:
        size = 19
        root.set_value("SZ", "19")

    if size > 19 or size < 1:
        raise BadBoardSize

    # The parsers just set up SGF keys and values in the nodes, but don't touch the board or other info like
    # main line status and move count. We do that now:

    root.board = Board(size)
    root.is_main_line = True
    root.update_recursive()

    return root


def parse_sgf(sgf):
    sgf = sgf.strip()
    sgf = sgf.lstrip("(")       # the load_sgf_tree() function assumes the leading "(" has already been read and discarded

    root, __ = load_sgf_tree(sgf, None)
    return root


def load_sgf_tree(sgf, parent_of_local_root):   # The caller should ensure there is no leading "("

    root = None
    node = None

    inside = False      # Are we inside a value? i.e. in C[foo] the value is foo
    value = ""
    key = ""
    keycomplete = False
    chars_to_skip = 0

    for i, c in enumerate(sgf):

        if chars_to_skip:
            chars_to_skip -= 1
            continue

        if inside:
            if c == "\\":               # Escape characters are saved
                value += "\\"
                try:
                    value += sgf[i + 1]
                except IndexError:
                    raise ParserFail
                chars_to_skip = 1
            elif c == "]":
                inside = False
                if node is None:
                    raise ParserFail
                node.add_value(key, value)
            else:
                value += c
        else:
            if c == "[":
                value = ""
                inside = True
                keycomplete = True
            elif c == "(":
                if node is None:
                    raise ParserFail
                __, chars_to_skip = load_sgf_tree(sgf[i + 1:], node)    # The child function will append the new tree to the node
            elif c == ")":
                if root is None:
                    raise ParserFail
                return root, i + 1          # return characters read
            elif c == ";":
                if node is None:
                    newnode = Node(parent = parent_of_local_root)
                    root = newnode
                    node = newnode
                else:
                    newnode = Node(parent = node)
                    node = newnode
            else:
                if not c.isspace():
                    if keycomplete:
                        key = ""
                        keycomplete = False
                    key += c

    if root is None:
        raise ParserFail

    return root, i + 1          # return characters read


def parse_gib(gib):             # .gib is a file format used by the Tygem server, it's undocumented.
                                # I know nothing about how it specifies board size or variations.
                                # I've inferred from other source code how it does handicaps.

    root = Node(parent = None)
    node = root

    lines = gib.split("\n")

    for line in lines:
        line = line.strip()

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


def parse_ngf(ngf):             # Another poorly documented file format

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


def main():

    filename = sys.argv[1]
    node = load(filename)

    print("\n  SGF main line viewer. Press return to jump through the moves.")

    while 1:
        input()
        m = node.what_was_the_move()
        node.board.dump(highlight = m)
        try:
            node = node.children[0]
        except IndexError:
            break

    print("\n  End of game... press return to quit.")
    input()


if __name__ == "__main__":
    main()
