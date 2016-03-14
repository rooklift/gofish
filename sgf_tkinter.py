import os, sys
import tkinter, tkinter.filedialog, tkinter.messagebox

import sgf

WIDTH, HEIGHT = 621, 621
GAP = 31


def load_graphics():

    # PhotoImages have a tendency to get garbage-collected even when they're needed.
    # Avoid this by making them globals.

    directory = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(directory)    # Set working dir to be same as infile.

    global spriteTexture; spriteTexture = tkinter.PhotoImage(file = "gfx/texture.gif")
    global spriteBlack; spriteBlack = tkinter.PhotoImage(file = "gfx/black.gif")
    global spriteWhite; spriteWhite = tkinter.PhotoImage(file = "gfx/white.gif")
    global spriteHoshi; spriteHoshi = tkinter.PhotoImage(file = "gfx/hoshi.gif")

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


def draw_node(canvas, node):
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


def keypress_handler(event, canvas, node):

    if event.keysym in ["Down", "Right"]:
        try:
            node = node.children[0]
            node.print_comments()
            node.board.dump()
        except IndexError:
            pass
    if event.keysym in ["Up", "Left"]:
        if node.parent:
            node = node.parent
            node.board.dump()

    draw_node(canvas, node)
    return node


def mouseclick_handler(event, canvas, node):
    print("clicked at", board_pos_from_screen_pos(event.x, event.y, node.board.boardsize))
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

    def call_keypress_handler(event):
        nonlocal node
        node = keypress_handler(event, canvas, node)

    def call_mouseclick_handler(event):
        nonlocal node
        node = mouseclick_handler(event, canvas, node)

    window = tkinter.Tk()
    window.resizable(width = False, height = False)
    window.geometry('{}x{}'.format(WIDTH, HEIGHT))

    load_graphics()

    canvas = tkinter.Canvas(window, width = WIDTH, height = HEIGHT)

    canvas.bind("<Key>", call_keypress_handler)
    canvas.bind("<Button-1>", call_mouseclick_handler)

    canvas.pack()
    canvas.focus_set()

    draw_node(canvas, node)
    window.mainloop()


if __name__ == "__main__":
    main()
