import copy, sys


EMPTY, BLACK, WHITE = 0, 1, 2
pieces = {EMPTY: ".", BLACK: "*", WHITE: "O"}


class OffBoard(Exception):
    pass


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
    s = ""
    s += chr(x + 96)
    s += chr(y + 96)
    return s


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

    def dump(self, highlight):

        if highlight is None:
            highlightx, highlighty = None, None
        else:
            highlightx, highlighty = highlight[0], highlight[1]

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
        assert(colour in [BLACK, WHITE, "B", "W"])

        if colour == "B":
            colour = BLACK
        if colour == "W":
            colour = WHITE

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

    def update_board(self):             # Use the properties to modify the board...

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
                except IndexError:
                    pass
                except OffBoard:
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
                    for point in points_from_points_string(value, self.board.boardsize):
                        x, y = point[0], point[1]
                        try:
                            self.board.state[x][y] = adders[adder]
                        except IndexError:
                            pass

    def update_board_recursive(self):
        self.update_board()
        for n, child in enumerate(self.children):
            if self.is_main_line and n == 0:
                child.is_main_line = True
            child.board = copy.deepcopy(self.board)
            child.moves_made = self.moves_made
            child.update_board_recursive()

    def dump(self):                 # For debugging
        print(";", end="")
        for key, value in self.properties.items():
            try:
                print("{}{}".format(key, value))        # Sometimes fails on Windows to Unicode errors
            except Exception as err:
                print("Exception: {}".format(err))

    def dump_recursive(self):       # For debugging
        self.dump()
        for child in self.children:
            child.dump_recursive()

    def print_comments(self):
        if "C" in self.properties:
            print("[{}] ".format(self.moves_made), end="")
            for value in self.properties["C"]:
                try:
                    print(value.strip())
                except Exception as err:
                    print("Exception: {}".format(err))
                print()

    def what_was_the_move(self):        # Assumes one move at most, which the specs also insist on.
        if "B" in self.properties:
            movestring = self.properties["B"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                if 1 <= x <= self.board.boardsize and 1 <= y <= self.board.boardsize:
                    return (x, y)
            except IndexError:
                pass
        elif "W" in self.properties:
            movestring = self.properties["W"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                if 1 <= x <= self.board.boardsize and 1 <= y <= self.board.boardsize:
                    return (x, y)
            except IndexError:
                pass
        return None

    def sibling_moves(self):    # Don't use this to check for variations - a node might not have any moves
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

    def add_and_return_child(self):
        child = Node(parent = self)     # This automatically appends the child to this node
        child.board = copy.deepcopy(self.board)
        child.moves_made = self.moves_made
        if self.is_main_line and len(self.children) == 1:
            child.is_main_line = True
        return child

    def previous_colour_played(self):
        node = self
        while 1:
            if node.parent == None:
                return None
            node = node.parent
            if "B" in node.properties:
                return BLACK
            if "W" in node.properties:
                return WHITE

def load(filename):

    try:
        with open(filename, encoding="utf8") as infile:
            sgf = infile.read()
    except UnicodeDecodeError:
        print("Opening as UTF-8 failed, trying Latin-1\n")
        with open(filename, encoding="latin1") as infile:
            sgf = infile.read()

    sgf = sgf.strip()
    sgf = sgf.lstrip("(")

    root, __ = load_tree(sgf, None)

    if "SZ" in root.properties:
        size = int(root.properties["SZ"][0])
    else:
        size = 19

    if size > 19 or size < 1:
        print("SZ (board size) was not in range 1:19")
        sys.exit(1)

    root.board = Board(size)
    root.is_main_line = True
    root.update_board_recursive()

    return root


def load_tree(sgf, parent_of_local_root):   # The caller should ensure there is no leading "("

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
            if c == "\\":
                value += sgf[i + 1]
                chars_to_skip = 1
            elif c == "]":
                inside = False
                if key not in node.properties:
                    node.properties[key] = []
                node.properties[key].append(value)
            else:
                value += c
        else:
            if c == "[":
                value = ""
                inside = True
                keycomplete = True
            elif c == "(":
                assert(node is not None)
                __, chars_to_skip = load_tree(sgf[i + 1:], node)    # The child function will append the new tree to the node
            elif c == ")":
                assert(root is not None)
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

    assert(root is not None)
    return root, i + 1          # return characters read


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
