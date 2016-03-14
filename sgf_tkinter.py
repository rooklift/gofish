import os, sys
import tkinter, tkinter.filedialog, tkinter.messagebox

import sgf

WIDTH, HEIGHT = 621, 621
GAP = 31


def load_graphics():
    directory = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(directory)    # Set working dir to be same as infile.

    # PhotoImages have a tendency to get garbage-collected even when they're needed.
    # Avoid this by making them globals, so there's always a reference to them.

    global spriteTexture; spriteTexture = tkinter.PhotoImage(file = "gfx/texture.gif")
    global spriteBlack; spriteBlack = tkinter.PhotoImage(file = "gfx/black.gif")
    global spriteWhite; spriteWhite = tkinter.PhotoImage(file = "gfx/white.gif")
    global spriteHoshi; spriteHoshi = tkinter.PhotoImage(file = "gfx/hoshi.gif")
    global spriteMove; spriteMove = tkinter.PhotoImage(file = "gfx/move.gif")
    global spriteVar; spriteVar = tkinter.PhotoImage(file = "gfx/var.gif")
    global spriteTriangle; spriteTriangle = tkinter.PhotoImage(file = "gfx/triangle.gif")
    global spriteCircle; spriteCircle = tkinter.PhotoImage(file = "gfx/circle.gif")
    global spriteSquare; spriteSquare = tkinter.PhotoImage(file = "gfx/square.gif")
    global spriteMark; spriteMark = tkinter.PhotoImage(file = "gfx/mark.gif")

    global markup_dict; markup_dict = {"TR": spriteTriangle, "CR": spriteCircle, "SQ": spriteSquare, "MA": spriteMark}


def screen_pos_from_board_pos(x, y, boardsize):
    gridsize = GAP * (boardsize - 1) + 1
    margin = (WIDTH - gridsize) // 2
    ret_x = (x - 1) * GAP + margin
    ret_y = (y - 1) * GAP + margin
    return ret_x, ret_y


def board_pos_from_screen_pos(x, y, boardsize):        # Inverse of the above
    gridsize = GAP * (boardsize - 1) + 1
    margin = (WIDTH - gridsize) // 2
    ret_x = round((x - margin) / GAP + 1)
    ret_y = round((y - margin) / GAP + 1)
    return ret_x, ret_y


def draw_node(window, canvas, node):
    canvas.delete(tkinter.ALL)              # DESTROY all!
    boardsize = node.board.boardsize

    # Draw the texture...

    canvas.create_image(0, 0, anchor = tkinter.NW, image = spriteTexture)

    # Draw the hoshi points...

    for x in range(3, boardsize - 1):
        for y in range(boardsize - 1):
            if sgf.is_star_point(x, y, boardsize):
                screen_x, screen_y = screen_pos_from_board_pos(x, y, boardsize)
                canvas.create_image(screen_x, screen_y, image = spriteHoshi)

    # Draw the lines...

    for n in range(1, boardsize + 1):
        start_x, start_y = screen_pos_from_board_pos(n, 1, boardsize)
        end_x, end_y = screen_pos_from_board_pos(n, boardsize, boardsize)
        canvas.create_line(start_x, start_y, end_x, end_y)
        canvas.create_line(start_y, start_x, end_y, end_x)

    # Draw the stones...

    for x in range(1, node.board.boardsize + 1):
        for y in range(1, node.board.boardsize + 1):
            screen_x, screen_y = screen_pos_from_board_pos(x, y, node.board.boardsize)
            if node.board.state[x][y] == sgf.BLACK:
                canvas.create_image(screen_x, screen_y, image = spriteBlack)
            elif node.board.state[x][y] == sgf.WHITE:
                canvas.create_image(screen_x, screen_y, image = spriteWhite)

    # Draw a mark at the current move, if there is one...

    move = node.what_was_the_move()
    if move is not None:
        screen_x, screen_y = screen_pos_from_board_pos(move[0], move[1], node.board.boardsize)
        canvas.create_image(screen_x, screen_y, image = spriteMove)

    # Draw a mark at variations, if there are any...

    for sib_move in node.sibling_moves():
        screen_x, screen_y = screen_pos_from_board_pos(sib_move[0], sib_move[1], node.board.boardsize)
        canvas.create_image(screen_x, screen_y, image = spriteVar)

    # Draw the commonly used marks...

    for mark in markup_dict:
        if mark in node.properties:
            points = set()
            for value in node.properties[mark]:
                points |= sgf.points_from_points_string(value, node.board.boardsize)
            for point in points:
                screen_x, screen_y = screen_pos_from_board_pos(point[0], point[1], node.board.boardsize)
                canvas.create_image(screen_x, screen_y, image = markup_dict[mark])


# All the key handlers are in the same form:
#
# def handle_key_NAME(node):
#     <do stuff>
#     return node
#
# where NAME is an uppercase version of the event.keysym, see:
# http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/key-names.html
#
# One can make a new key handler just by creating it, no other work is needed anywhere


def handle_key_DOWN(node):
    try:
        node = node.children[0]
        node.print_comments()
    except IndexError:
        pass
    return node

def handle_key_RIGHT(node):
    return handle_key_DOWN(node)

def handle_key_UP(node):
    if node.parent:
        node = node.parent
    return node

def handle_key_LEFT(node):
    return handle_key_UP(node)

def handle_key_NEXT(node):          # PageDown
    for n in range(10):
        try:
            node = node.children[0]
            node.print_comments()
        except IndexError:
            break
    return node

def handle_key_PRIOR(node):         # PageUp
    for n in range(10):
        if node.parent:
            node = node.parent
        else:
            break
    return node

def handle_key_TAB(node):
    if node.parent:
        if len(node.parent.children) > 1:
            index = node.parent.children.index(node)
            if index < len(node.parent.children) - 1:
                index += 1
            else:
                index = 0
            node = node.parent.children[index]
            node.print_comments()
    return node

def handle_key_BACKSPACE(node):         # Return to the main line
    while 1:
        if node.is_main_line:
            break
        if node.parent is None:
            break
        node = node.parent
    return node

def handle_key_HOME(node):
    return node.get_root_node()

def handle_key_END(node):
    return node.get_end_node()

def handle_key_DELETE(node):
    if node.parent:
        if tkinter.messagebox.askokcancel("Delete?", "Delete this node and all of its children?"):
            child = node
            node = node.parent
            node.children.remove(child)
            node.fix_main_line_status_recursive()
    return node

def handle_key_D(node):
    node.debug()
    return node

# Other handlers...

def opener(node):
    infilename = tkinter.filedialog.askopenfilename()
    if infilename:
        try:
            node = sgf.load(infilename)
            print("<--- Loaded: {}\n".format(infilename))
            node.dump(include_comments = False)
            print()
            node.print_comments()
        except FileNotFoundError:
            print("error while loading: file not found")
        except sgf.BoardTooBig:
            print("error while loading: SZ (board size) was not in range 1:19")
        except sgf.ParserFail:
            print("error while loading: parser failed (invalid SGF?)")
    return node

def saver(node):
    outfilename = tkinter.filedialog.asksaveasfilename(defaultextension=".sgf")
    if outfilename:
        sgf.save_file(outfilename, node)
        print("---> Saved: {}\n".format(outfilename))
    return node

def mouseclick_handler(node, x, y):
    result = node.try_move(x, y)
    if result:
        node = result
    return node



def main():
    try:
        node = sgf.load(sys.argv[1])
        print("<--- Loaded: {}\n".format(sys.argv[1]))
        node.dump(include_comments = False)
        print()
        node.print_comments()
    except (IndexError, FileNotFoundError):
        node = sgf.new_tree(19)

    # We define some functions to call the handlers with the argument they
    # really need ("node") and then draw the window; also updating the
    # almost-local variable "node" from the return value of the handler

    def call_keypress_handler(event):
        nonlocal node
        try:
            function_name = "handle_key_" + event.keysym.upper()
            node = globals()[function_name](node)
        except:
            pass
        draw_node(window, canvas, node)

    def call_mouseclick_handler(event):
        nonlocal node
        x, y = board_pos_from_screen_pos(event.x, event.y, node.board.boardsize)
        node = mouseclick_handler(node, x, y)
        draw_node(window, canvas, node)

    def call_opener(event):
        nonlocal node
        node = opener(node)
        draw_node(window, canvas, node)

    def call_saver(event):
        nonlocal node
        node = saver(node)
        draw_node(window, canvas, node)

    window = tkinter.Tk()
    window.resizable(width = False, height = False)
    window.geometry('{}x{}'.format(WIDTH, HEIGHT))

    load_graphics()

    canvas = tkinter.Canvas(window, width = WIDTH, height = HEIGHT)

    canvas.bind("<Key>", call_keypress_handler)
    canvas.bind("<Button-1>", call_mouseclick_handler)
    canvas.bind("<Control-o>", call_opener)
    canvas.bind("<Control-s>", call_saver)

    canvas.pack()
    canvas.focus_set()

    draw_node(window, canvas, node)
    window.mainloop()


if __name__ == "__main__":
    main()
