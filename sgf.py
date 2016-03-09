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

class Board():                  # Internally the arrays are size 20x20, with 0 indexes being ignored (so we can use indexes 1-19)
    def __init__(self):
        self.state = []
        for x in range(20):
            ls = list()
            for y in range(20):
                ls.append(0)
            self.state.append(ls)

    def dump(self):
        for row in range(1, 20):
            for col in range(1, 20):

                if self.state[col][row] == EMPTY and (col, row) in stars:
                    print("+", end=" ")
                else:
                    print(pieces[self.state[col][row]], end=" ")
            print()


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
            self.board.state[x][y] = BLACK
        elif "W" in self.properties:
            movestring = self.properties["W"][0]
            x = ord(movestring[0]) - 96
            y = ord(movestring[1]) - 96
            self.board.state[x][y] = WHITE

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


def main():
    filename = sys.argv[1]
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

    print("\nSimple minded SGF reader. Press return to jump through the moves.")

    while 1:
        input()
        node.board.dump()
        try:
            node = node.children[0]
        except IndexError:
            break


if __name__ == "__main__":
    main()
