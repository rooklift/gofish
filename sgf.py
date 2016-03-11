import copy
import sys

EMPTY = 0
BLACK = 1
WHITE = 2

pieces = {EMPTY: ".", BLACK: "*", WHITE: "O"}

stars = [
    (4, 4),(10, 4),(16, 4),
    (4,10),(10,10),(16,10),
    (4,16),(10,16),(16,16),
]

class OffBoard(Exception):
    pass


def points_from_points_list(s):     # convert "aa" or "cd:jf" into set of points

    ret = set()

    if len(s) < 2:
        return ret

    left = ord(s[0]) - 96
    top = ord(s[1]) - 96
    right = ord(s[-2]) - 96         # This works regardless of
    bottom = ord(s[-1]) - 96        # the format ("aa" or "cd:jf")

    for x in range(left, right + 1):
        for y in range(top, bottom + 1):
            ret.add((x,y))

    return ret


def adjacent_points(x, y):
    result = set()

    for i, j in [
        (x - 1, y),
        (x + 1, y),
        (x, y - 1),
        (x, y + 1),
    ]:
        if i >= 1 and i <= 19 and j >= 1 and j <= 19:
            result.add((i, j))

    return result


class Board():                  # Internally the arrays are size 20x20, with 0 indexes being ignored (so we can use indexes 1-19)
    def __init__(self):
        self.state = []
        self.stones_checked = set()     # Used when searching for liberties
        for x in range(20):
            ls = list()
            for y in range(20):
                ls.append(0)
            self.state.append(ls)

    def dump(self, highlight):

        if highlight is None:
            highlightx, highlighty = None, None
        else:
            highlightx, highlighty = highlight[0], highlight[1]

        for row in range(1, 20):
            for col in range(0, 20):        # Start from 0 so we have space to print the highlight if it's at col 1

                end = " "
                if row == highlighty:
                    if col + 1 == highlightx:
                        end = "["
                    elif col == highlightx:
                        end = "]"

                if col == 0:                # Remember that the real board starts at 1
                    print(" ", end=end)
                elif self.state[col][row] == EMPTY and (col, row) in stars:
                    print("+", end=end)
                else:
                    print(pieces[self.state[col][row]], end=end)
            print()

    def group_has_liberties(self, x, y):
        assert(x >= 1 and x <= 19 and y >= 1 and y <= 19)
        self.stones_checked = set()
        return self.__group_has_liberties(x, y)

    def __group_has_liberties(self, x, y):
        assert(x >= 1 and x <= 19 and y >= 1 and y <= 19)
        colour = self.state[x][y]
        assert(colour in [BLACK, WHITE])

        self.stones_checked.add((x,y))

        for i, j in adjacent_points(x, y):
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

        if x < 1 or x > 19 or y < 1 or y > 19:
            raise OffBoard

        self.state[x][y] = colour

        for i, j in adjacent_points(x, y):
            if self.state[i][j] == opponent:
                if not self.group_has_liberties(i, j):
                    self.destroy_group(i, j)

        # Check for and deal with suicide:

        if not self.group_has_liberties(x, y):
            self.destroy_group(x, y)

    def destroy_group(self, x, y):
        assert(x >= 1 and x <= 19 and y >= 1 and y <= 19)
        colour = self.state[x][y]
        assert(colour in [BLACK, WHITE])

        self.state[x][y] = EMPTY

        for i, j in adjacent_points(x, y):
            if self.state[i][j] == colour:
                self.destroy_group(i, j)


class Node():
    def __init__(self, parent):
        self.properties = dict()
        self.children = []
        self.board = None
        self.moves_made = 0
        self.parent = parent

        if parent:
            parent.children.append(self)

    def update_board(self):             # Use the properties to modify the board

        # A node "should" have only 1 of "B" or "W"

        if "B" in self.properties:
            movestring = self.properties["B"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                self.board.play_move(BLACK, x, y)
                self.moves_made += 1
            except IndexError:
                pass
            except OffBoard:
                pass

        if "W" in self.properties:
            movestring = self.properties["W"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                self.board.play_move(WHITE, x, y)
                self.moves_made += 1
            except IndexError:
                pass
            except OffBoard:
                pass

        # A node can have all of "AB", "AW" and "AE"
        # Note that adding a stone doesn't count as "playing" it and can
        # result in illegal positions (the specs allow this explicitly)

        if "AB" in self.properties:
            for value in self.properties["AB"]:
                for point in points_from_points_list(value):
                    x, y = point[0], point[1]
                    try:
                        self.board.state[x][y] = BLACK
                    except IndexError:
                        pass
        if "AW" in self.properties:
            for value in self.properties["AW"]:
                for point in points_from_points_list(value):
                    x, y = point[0], point[1]
                    try:
                        self.board.state[x][y] = WHITE
                    except IndexError:
                        pass
        if "AE" in self.properties:
            for value in self.properties["AE"]:
                for point in points_from_points_list(value):
                    x, y = point[0], point[1]
                    try:
                        self.board.state[x][y] = EMPTY
                    except IndexError:
                        pass

    def update_board_recursive(self):
        self.update_board()
        for child in self.children:
            child.board = copy.deepcopy(self.board)
            child.moves_made = self.moves_made
            child.update_board_recursive()

    def dump(self):
        print(";", end="")
        for key, value in self.properties.items():
            try:
                print("{}{}".format(key, value))        # Sometimes fails on Windows to Unicode errors
            except:
                pass

    def dump_recursive(self):
        self.dump()
        for child in self.children:
            child.dump_recursive()

    def print_comments(self):
        if "C" in self.properties:
            print(self.properties["C"][0].strip())
            print()

    def what_was_the_move(self):
        if "B" in self.properties:
            movestring = self.properties["B"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                return (x, y)
            except IndexError:
                pass
        elif "W" in self.properties:
            movestring = self.properties["W"][0]
            try:
                x = ord(movestring[0]) - 96
                y = ord(movestring[1]) - 96
                return (x, y)
            except IndexError:
                pass
        return None


def load(filename):

    with open(filename, encoding="utf8") as infile:
        sgf = infile.read()

    sgf = sgf.strip()
    sgf = sgf.lstrip("(")

    root, __ = load_tree(sgf, None)
    root.board = Board()
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
