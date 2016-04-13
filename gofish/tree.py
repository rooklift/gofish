import copy

from gofish.constants import *
from gofish.utils import *

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

    def play_move(self, colour, x, y):      # No legality checks, as per SGF standard
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

    def update_from_node(self, node):

        # Use the node's properties to modify the board. For various reasons, this
        # might actually be used on a board that's already been so modified, but
        # that should be completely harmless.

        # A node "should" have only 1 of "B" or "W", and only 1 value in the list.
        # The result will be wrong if the specs are violated. Whatever.

        movers = {"B": BLACK, "W": WHITE}

        for mover in movers:
            if mover in node.properties:
                movestring = node.properties[mover][0]
                try:
                    x = ord(movestring[0]) - 96
                    y = ord(movestring[1]) - 96
                    self.play_move(movers[mover], x, y)
                except (IndexError, OffBoard):
                    pass

        # A node can have all of "AB", "AW" and "AE" (but should not also have "B" or "W").
        # Note that adding a stone doesn't count as "playing" it and can
        # result in illegal positions (the specs allow this explicitly)

        adders = {"AB": BLACK, "AW": WHITE, "AE": EMPTY}

        for adder in adders:
            if adder in node.properties:
                for value in node.properties[adder]:
                    for point in points_from_points_string(value, self.boardsize):    # only returns points inside the board boundaries
                        x, y = point[0], point[1]
                        self.state[x][y] = adders[adder]


class Node():
    def __init__(self, parent):
        self.properties = dict()
        self.children = []
        self.__board = None
        self.moves_made = 0
        self.is_main_line = False
        self.parent = parent

        if parent:
            parent.children.append(self)

    @property
    def board(self):
        if not self.__board:
            self.__board = self.build_board()
        return self.__board

    @board.setter
    def board(self, board):
        self.__board = board

    def moves_in_this_node(self):
        ret = 0
        for mover in ["B", "W"]:
            if mover in self.properties:
                ret += 1
        return ret

    def update(self, update_board = True):              # Use the properties to modify the node
        if update_board:
            self.board.update_from_node(self)
        self.moves_made += self.moves_in_this_node()

    def update_recursive(self, update_board = True):    # Only goes recursive if 2 or more children
        node = self
        while 1:
            node.update(update_board)
            if len(node.children) == 0:
                return
            elif len(node.children) == 1:               # i.e. just iterate where possible
                node.copy_state_to_child(node.children[0], copy_board = update_board)
                node = node.children[0]
                continue
            else:
                for child in node.children:
                    node.copy_state_to_child(child, copy_board = update_board)
                    child.update_recursive(update_board)
                return

    def fix_main_line_status(self):
        if self.parent is None or (self.parent.is_main_line and self is self.parent.children[0]):
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

    def copy_state_to_child(self, child, copy_board = True):
        if len(self.children) > 0:                  # there's no guarantee the child has actually been appended, hence this test
            if child is self.children[0]:
                if self.is_main_line:
                    child.is_main_line = True

        if copy_board:
            child.board = copy.deepcopy(self.board)     # not needed when loading a file; the board is generated the first time it's needed

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

    def what_was_the_move(self):        # Assumes one move at most, which the specs also insist on. A pass causes None to be returned.
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

    def children_moves(self):
        moves = set()
        for node in self.children:
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
            if "PL" in node.properties:
                if node.properties["PL"][0] in ["b", "B"]:     # file explicitly says black plays next, so we pretend white played last
                    return WHITE
                if node.properties["PL"][0] in ["w", "W"]:
                    return BLACK
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

    def make_empty_child(self, append = True):
        if append:
            child = Node(parent = self)             # This automatically appends the child to this node
        else:
            child = Node(parent = None)

        self.copy_state_to_child(child)
        return child

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

        # Colour can generally be auto-determined by what colour the last move was...

        if colour == None:
            colour = WHITE if self.last_colour_played() == BLACK else BLACK      # If it was None we get BLACK
        else:
            assert(colour in [BLACK, WHITE])

        # if the move already exists, just return the (first) relevant child...

        for child in self.children:
            if child.what_was_the_move() == (x, y):
                if child.move_colour() == colour:
                    return child

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
        # is present in the node, or if the node has any children).

        if x < 1 or x > self.board.boardsize or y < 1 or y > self.board.boardsize:
            raise OffBoard

        if len(self.children) > 0:      # Can't add stones this way when the node has children (should we be able to?)
            raise WrongNode

        if "B" in self.properties or "W" in self.properties:
            raise WrongNode

        # AB, AW and AE are all mutually exclusive, so we go through some rigmarol to ensure this...

        ab_set = set()
        aw_set = set()
        ae_set = set()

        all_point_sets = {"AB": ab_set, "AW": aw_set, "AE": ae_set}

        for key, point_set in all_point_sets.items():

            if key in self.properties:
                for value in self.properties[key]:
                    point_set |= points_from_points_string(value, self.board.boardsize)

            point_set.discard((x,y))                # This implements the mutual exclusion mentioned above

            if colour == WHITE and key == "AW":
                point_set.add((x,y))
            if colour == BLACK and key == "AB":
                point_set.add((x,y))
            if colour == EMPTY and key == "AE":
                point_set.add((x,y))

            self.properties.pop(key, None)          # Delete property from the Node; will maybe be recreated later...

        for key, point_set in all_point_sets.items():
            for point in point_set:
                s = string_from_point(point[0], point[1])
                self.add_value(key, s)

        self.update()

    def unlink_recursive(self):

        # Recursively remove all references (parents, children) in self and child nodes,
        # to allow garbage collection to work.

        node = self

        while 1:
            node.parent = None
            if len(node.children) == 0:
                return
            elif len(node.children) == 1:           # i.e. just iterate where possible
                child = node.children[0]
                node.children = []
                node = child
                continue
            else:
                for child in node.children:
                    child.unlink_recursive()
                node.children = []
                return

    def node_path(self):            # Return the path of nodes that leads to this node

        path = []
        node = self

        while 1:
            path.append(node)
            if node.parent:
                node = node.parent
            else:
                break

        return list(reversed(path))

    def build_board(self):   # Create a board by iterating from a known board, possibly the root

        path = self.node_path()

        if "SZ" not in path[0].properties:
            raise NoBoardSize

        size = int(path[0].properties["SZ"][0])

        if size < 1 or size > 19:
            raise BadBoardSize

        # Find the latest node with a board:

        board = None
        for n in range(len(path) - 1, -1, -1):
            node = path[n]
            if node.__board is not None:
                board = copy.deepcopy(node.__board)
                break
        if not board:
            board = Board(size)
            n = 0

        for i in range(n, len(path)):
            node = path[i]
            board.update_from_node(node)
            if node is not self:
                if node.__board is None:
                    node.__board = copy.deepcopy(board)   # Cache the nodes while we're at it

        return board

    def clear_markup(self):
        allkeys = []
        for key in self.properties:
            allkeys.append(key)     # We do this so the dict doesn't change size during the following:
        for key in allkeys:
            if key not in ["AB", "AW", "B", "W", "FF", "GM", "CA", "SZ", "KM", "RE", "EV", "GN", "PC", "DT", "PB", "PW"]:
                self.properties.pop(key)

    def clear_markup_recursive(self):
        node = self
        while 1:
            node.clear_markup()
            if len(node.children) == 0:
                return
            elif len(node.children) == 1:           # i.e. just iterate where possible
                node = node.children[0]
                continue
            else:
                for child in node.children:
                    child.clear_markup_recursive()
                return


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
