import copy
import sys

EMPTY = 0
BLACK = 1
WHITE = 2

pieces = {EMPTY: ".", BLACK: "*", WHITE: "O"}

stars = [
     (4,4), (4,10), (4,16),
    (10,4),(10,10),(10,16),
    (16,4),(16,10),(16,16),
]


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
        self.stones_checked = set()
        return self.__group_has_liberties(x, y)

    def __group_has_liberties(self, x, y):

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

        self.state[x][y] = colour

        for i, j in adjacent_points(x, y):
            if self.state[i][j] == opponent:
                if not self.group_has_liberties(i, j):
                    self.destroy_group(i, j)

        # Check for and deal with suicide:

        if not self.group_has_liberties(x, y):
            self.destroy_group(x, y)

    def destroy_group(self, x, y):
        colour = self.state[x][y]
        assert(colour in [BLACK, WHITE])
        assert(x >= 1 and x <= 19 and y >= 1 and y <= 19)

        self.state[x][y] = EMPTY

        for i, j in adjacent_points(x, y):
            if self.state[i][j] == colour:
                self.destroy_group(i, j)

class Node():
    def __init__(self):
        self.properties = dict()
        self.children = []
        self.board = None
        self.parent = None

    def update_board(self):
        if "B" in self.properties:
            movestring = self.properties["B"][0]
            x = ord(movestring[0]) - 96
            y = ord(movestring[1]) - 96
            self.board.play_move(BLACK, x, y)
        elif "W" in self.properties:
            movestring = self.properties["W"][0]
            x = ord(movestring[0]) - 96
            y = ord(movestring[1]) - 96
            self.board.play_move(WHITE, x, y)

    def update_board_recursive(self):
        self.update_board()
        for child in self.children:
            child.board = copy.deepcopy(self.board)
            child.update_board_recursive()

    def dump(self):
        print(";", end="")
        for key, value in self.properties.items():
            print("{}{}".format(key, value))

    def dump_recursive(self):
        self.dump()
        for child in self.children:
            child.dump_recursive()

    def what_was_the_move(self):
        if "B" in self.properties:
            movestring = self.properties["B"][0]
            x = ord(movestring[0]) - 96
            y = ord(movestring[1]) - 96
            return (x, y)
        elif "W" in self.properties:
            movestring = self.properties["W"][0]
            x = ord(movestring[0]) - 96
            y = ord(movestring[1]) - 96
            return (x, y)
        return None

    def add_properties(self, s):    # s is some string like "B[cn]LB[dn:A][po:B]C[dada: other ideas are 'A' (d6) or 'B' (q5)]"

        inside = False
        key = ""
        value = ""
        key_complete = False

        for c in s:

            if c == "[":
                inside = True
                value = ""
                if key not in self.properties:
                    self.properties[key] = []

            elif c == "]":
                inside = False
                self.properties[key].append(value)

            else:
                if not inside:
                    if not c.isspace():
                        if key_complete:    # So we need to start a new key, we finished learning the old one
                            key = ""
                            key_complete = False
                        key += c
                else:
                    value += c
                    key_complete = True


def load(filename):

    with open(filename) as infile:
        sgf = infile.read()

    main_line = sgf.strip("()")     # This isn't at all a valid way of getting the main line if there are variations, FIXME
    strings = main_line.split(";")

    root = Node()
    root.board = Board()

    last_node = root

    for s in strings:
        if s.isspace() or s == "":
            continue
        new_node = Node()
        new_node.add_properties(s)
        new_node.parent = last_node
        last_node.children.append(new_node)
        last_node = new_node

    root.update_board_recursive()

    try:
        node = root.children[0]
    except IndexError:
        node = root

    return node


def main():

    filename = sys.argv[1]
    node = load(filename)

    print("\n  Simple minded SGF reader. Press return to jump through the moves.")

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
