# The challenge of this is making a nice GUI while not having races where (e.g.) a new board
# is created while the engine is thinking. I use the simplest solution of disallowing all
# human action while we await the engine's next move.

import os, queue, subprocess, sys, threading
import tkinter, tkinter.filedialog, tkinter.messagebox

import gofish
from gofish import BLACK, WHITE

colour_lookup = {BLACK: "black", WHITE: "white"}

WIDTH, HEIGHT = 621, 621
GAP = 31

MOTD = """
  Fohristiwhirl's GTP relay.
"""

# --------------------------------------------------------------------------------------
# Various utility functions...

def load_graphics():
    directory = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(directory)    # Set working dir to be same as infile.

    # PhotoImages have a tendency to get garbage-collected even when they're needed.
    # Avoid this by making them globals, so there's always a reference to them.

    global spriteTexture
    try:
        spriteTexture = tkinter.PhotoImage(file = "gfx/texture_override.gif")
    except:
        spriteTexture = tkinter.PhotoImage(file = "gfx/texture.gif")

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

# --------------------------------------------------------------------------------------

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

def title_bar_string(node):
    wwtm = node.what_was_the_move()
    mwp = node.move_was_pass()

    if wwtm is None and not mwp:
        if node.parent:
            title = "Empty node"
        else:
            title = "Root node"
    else:
        title = "Move {}".format(node.moves_made)
    if node.parent:
        if len(node.parent.children) > 1:
            index = node.parent.children.index(node)
            title += " [{} of {} variations]".format(index + 1, len(node.parent.children))
    if mwp:
        title += " (pass)"
    elif wwtm:
        x, y = wwtm
        title += " ({})".format(gofish.english_string_from_point(x, y, node.board.boardsize))
    return title

# --------------------------------------------------------------------------------------

def send_command(command, verbose = True):

    if len(command) == 0 or command[-1] != "\n":
        command += "\n"

    if verbose:
        print(command, end="")

    process.stdin.write(bytearray(command, encoding="ascii"))
    process.stdin.flush()

def get_reply(verbose = True):

    response = ""

    while 1:
        newlinebytes = process.stdout.readline()
        newline = str(newlinebytes, encoding="ascii")
        newline = newline.replace("\r\n", "\n")             # is there a better way to deal with this Windows nonsense?

        response += newline

        if len(response) >= 2:
            if response[-2:] == "\n\n":
                response = response.strip()
                if verbose:
                    print(response)
                return response

def send_and_get(command):
    send_command(command)
    response = get_reply()
    return response

# This will get run in a thread, communicating with the rest of the program via queues...

def relay():
    while 1:
        command = engine_in_queue.get()

        send_command(command)
        response = get_reply()

        engine_out_queue.put(response)

# --------------------------------------------------------------------------------------

class GTP_GUI(tkinter.Canvas):

    def __init__(self, owner, *args, **kwargs):
        tkinter.Canvas.__init__(self, owner, *args, **kwargs)
        self.owner = owner
        self.bind("<Button-1>", self.mouseclick_handler)
        self.bind("<Key>", self.call_keypress_handler)
        self.bind("<Control-s>", self.saver)

        self.awaiting_move = False
        self.human_colour = BLACK
        self.engine_colour = WHITE

        self.reset(19)

        self.engine_msg_poller()


    def reset(self, size):

        if self.awaiting_move:
            return

        self.node = gofish.new_tree(size)

        for cmd in ["boardsize {}".format(self.node.board.boardsize), "clear_board", "komi 0"]:
            send_command(cmd)
            get_reply()

        if self.human_colour == BLACK:
            statusbar.config(text = "Your move ({})".format(colour_lookup[self.human_colour]))
        else:
            command = "genmove {}".format(colour_lookup[self.engine_colour])
            engine_in_queue.put(command)
            self.need_to_wait()

        self.draw_node()


    def handicap(self, h):
        if self.awaiting_move:
            return

        self.node = gofish.new_tree(self.node.board.boardsize)

        for cmd in ["boardsize {}".format(self.node.board.boardsize), "clear_board", "komi 0"]:
            send_command(cmd)
            get_reply()

        send_command("fixed_handicap {}".format(h))
        response = get_reply()

        if response[0] == "?":
            self.reset(self.node.board.boardsize)
            return

        self.node.set_value("HA", h)

        english_points_list = response[1:].strip().split()
        for p in english_points_list:
            x, y = gofish.point_from_english_string(p, self.node.board.boardsize)
            self.node.add_stone(BLACK, x, y)

        if self.human_colour == WHITE:      # The reverse of normal; white goes first
            statusbar.config(text = "Your move ({})".format(colour_lookup[self.human_colour]))
        else:
            command = "genmove {}".format(colour_lookup[self.engine_colour])
            engine_in_queue.put(command)
            self.need_to_wait()

        self.draw_node()


    def mouseclick_handler(self, event):

        if not self.awaiting_move:

            x, y = board_pos_from_screen_pos(event.x, event.y, self.node.board.boardsize)
            result = self.node.try_move(x, y, colour = self.human_colour)

            if result:
                self.node = result

                command = "play {} {}".format(colour_lookup[self.human_colour], gofish.english_string_from_point(x, y, self.node.board.boardsize))
                send_and_get(command)

                command = "genmove {}".format(colour_lookup[self.engine_colour])
                engine_in_queue.put(command)

                self.need_to_wait()

                self.draw_node()


    def engine_msg_poller(self):
        self.after(100, self.engine_msg_poller)     # Add a callback here in 100 ms
        self.engine_move_handler()

    # We just use the poller to get engine moves. Everything else doesn't use the
    # other thread to send and receive. Everything else will just block while
    # waiting for a response.

    def engine_move_handler(self):
        try:
            message = engine_out_queue.get(block = False)
        except queue.Empty:
            return
        if message[0] != "=":
            print("ERROR: {}".format(message))
            return

        if not self.awaiting_move:
            print("ERROR: got '{}' while NOT expecting move".format(message))
            return

        resign_flag = False

        message = message[1:].strip()

        if len(message) in [2,3]:
            point = gofish.point_from_english_string(message, self.node.board.boardsize)
            if point is None:
                print("ERROR: got '{}' while expecting move".format(message))
                return
            else:
                x, y = point
            result = self.node.try_move(x, y, colour = self.engine_colour)
            if result is None:
                print("ERROR: got illegal move {}".format(message))
                return
        elif message.upper() == "PASS":
            result = self.node.make_pass()
        elif message.upper() == "RESIGN":
            result = self.node.make_pass()
            resign_flag = True
        else:
            print("ERROR: got '{}' while expecting move".format(message))
            return

        self.done_waiting()

        self.node = result

        self.draw_node()

        if resign_flag:
            self.owner.wm_title("Engine resigned")      # do this after the draw_node() so the title bar is set
            statusbar.config(text = "Engine resigned")
        else:
            self.maybe_get_final_score()                # likewise


    def swap_colours(self):
        if self.awaiting_move:
            return

        self.human_colour, self.engine_colour = self.engine_colour, self.human_colour

        command = "genmove {}".format(colour_lookup[self.engine_colour])
        engine_in_queue.put(command)

        self.need_to_wait()


    def need_to_wait(self):     # Basically, prevent the user from doing anything
        menubar.entryconfig("New", state = "disabled")
        menubar.entryconfig("Handicap", state = "disabled")
        menubar.entryconfig("Pass", state = "disabled")
        menubar.entryconfig("Swap colours", state = "disabled")
        statusbar.config(text = "Awaiting move from engine")
        self.awaiting_move = True


    def done_waiting(self):
        menubar.entryconfig("New", state = "normal")
        menubar.entryconfig("Handicap", state = "normal")
        menubar.entryconfig("Pass", state = "normal")
        menubar.entryconfig("Swap colours", state = "normal")
        statusbar.config(text = "Your move ({})".format(colour_lookup[self.human_colour]))
        self.awaiting_move = False


    def maybe_get_final_score(self):
        if self.node.move_was_pass():
            if self.node.parent:
                if self.node.parent.move_was_pass():
                    statusbar.config(text = "Asking engine for score")
                    statusbar.update_idletasks()
                    msg = send_and_get("final_score")
                    self.owner.wm_title("Score: " + msg[1:].strip())
                    statusbar.config(text = "Score: " + msg[1:].strip())


    def draw_node(self):
        self.delete(tkinter.ALL)              # DESTROY all!
        boardsize = self.node.board.boardsize

        # Set the title bar of the owning window

        self.owner.wm_title(title_bar_string(self.node))

        # Draw the texture...

        self.create_image(0, 0, anchor = tkinter.NW, image = spriteTexture)

        # Draw the hoshi points...

        for x in range(3, boardsize - 1):
            for y in range(boardsize - 1):
                if gofish.is_star_point(x, y, boardsize):
                    screen_x, screen_y = screen_pos_from_board_pos(x, y, boardsize)
                    self.create_image(screen_x, screen_y, image = spriteHoshi)

        # Draw the lines...

        for n in range(1, boardsize + 1):
            start_a, start_b = screen_pos_from_board_pos(n, 1, boardsize)
            end_a, end_b = screen_pos_from_board_pos(n, boardsize, boardsize)

            end_b += 1

            self.create_line(start_a, start_b, end_a, end_b)
            self.create_line(start_b, start_a, end_b, end_a)

        # Draw the stones...

        for x in range(1, self.node.board.boardsize + 1):
            for y in range(1, self.node.board.boardsize + 1):
                screen_x, screen_y = screen_pos_from_board_pos(x, y, self.node.board.boardsize)
                if self.node.board.state[x][y] == BLACK:
                    self.create_image(screen_x, screen_y, image = spriteBlack)
                elif self.node.board.state[x][y] == WHITE:
                    self.create_image(screen_x, screen_y, image = spriteWhite)

        # Draw a mark at the current move, if there is one...

        move = self.node.what_was_the_move()
        if move is not None:
            screen_x, screen_y = screen_pos_from_board_pos(move[0], move[1], self.node.board.boardsize)
            self.create_image(screen_x, screen_y, image = spriteMove)

        # Draw a mark at variations, if there are any...

        for sib_move in self.node.sibling_moves():
            screen_x, screen_y = screen_pos_from_board_pos(sib_move[0], sib_move[1], self.node.board.boardsize)
            self.create_image(screen_x, screen_y, image = spriteVar)

        # Draw the commonly used marks...

        for mark in markup_dict:
            if mark in self.node.properties:
                points = set()
                for value in self.node.properties[mark]:
                    points |= gofish.points_from_points_string(value, self.node.board.boardsize)
                for point in points:
                    screen_x, screen_y = screen_pos_from_board_pos(point[0], point[1], self.node.board.boardsize)
                    self.create_image(screen_x, screen_y, image = markup_dict[mark])


    def saver(self, event):
        outfilename = tkinter.filedialog.asksaveasfilename(defaultextension=".sgf")
        if outfilename:
            gofish.save_file(outfilename, self.node)
            try:
                print("---> Saved: {}\n".format(outfilename))
            except:
                print("---> Saved: --- Exception when trying to print filename ---")
        self.draw_node()


    def call_keypress_handler(self, event):
        try:
            function_call = "self.handle_key_{}()".format(event.keysym.upper())
            eval(function_call)
        except AttributeError:
            pass

    def handle_key_P(self):

        if not self.awaiting_move:

            self.node = self.node.make_pass()

            colour_lookup = {BLACK: "black", WHITE: "white"}

            command = "play {} pass".format(colour_lookup[self.human_colour])
            send_and_get(command)

            command = "genmove {}".format(colour_lookup[self.engine_colour])
            engine_in_queue.put(command)

            self.need_to_wait()

            self.draw_node()

# ---------------------------------------------------------------------------------------


class Root(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        load_graphics()

        self.resizable(width = False, height = False)

        global statusbar
        statusbar = tkinter.Label(self, text="test", bd = 0, anchor = tkinter.W)
        statusbar.pack(side = tkinter.BOTTOM, fill = tkinter.X)

        board = GTP_GUI(self, width = WIDTH, height = HEIGHT, bd = 0, highlightthickness = 0)
        board.pack()
        board.focus_set()

        global menubar
        menubar = tkinter.Menu(self)

        new_board_menu = tkinter.Menu(menubar, tearoff = 0)
        new_board_menu.add_command(label = "19x19", command = lambda : board.reset(19))
        new_board_menu.add_command(label = "17x17", command = lambda : board.reset(17))
        new_board_menu.add_command(label = "15x15", command = lambda : board.reset(15))
        new_board_menu.add_command(label = "13x13", command = lambda : board.reset(13))
        new_board_menu.add_command(label = "11x11", command = lambda : board.reset(11))
        new_board_menu.add_command(label =  "9x9" , command = lambda : board.reset( 9))

        handicap_menu = tkinter.Menu(menubar, tearoff = 0)
        handicap_menu.add_command(label = "9", command = lambda : board.handicap(9))
        handicap_menu.add_command(label = "8", command = lambda : board.handicap(8))
        handicap_menu.add_command(label = "7", command = lambda : board.handicap(7))
        handicap_menu.add_command(label = "6", command = lambda : board.handicap(6))
        handicap_menu.add_command(label = "5", command = lambda : board.handicap(5))
        handicap_menu.add_command(label = "4", command = lambda : board.handicap(4))
        handicap_menu.add_command(label = "3", command = lambda : board.handicap(3))
        handicap_menu.add_command(label = "2", command = lambda : board.handicap(2))

        menubar.add_cascade(label = "New", menu = new_board_menu)
        menubar.add_cascade(label = "Handicap", menu = handicap_menu)
        menubar.add_command(label = "Pass", command = board.handle_key_P)
        menubar.add_command(label = "Swap colours", command = board.swap_colours)

        self.config(menu = menubar)

        self.wm_title("Fohristiwhirl's GTP relay")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Need an argument: the engine to run (it may also require more arguments)")
        sys.exit(1)

    global process
    process = subprocess.Popen(args = sys.argv[1:], stdin = subprocess.PIPE, stdout = subprocess.PIPE)    #, stderr = subprocess.DEVNULL)

    global engine_in_queue
    engine_in_queue = queue.Queue()

    global engine_out_queue
    engine_out_queue = queue.Queue()

    print(MOTD)

    threading.Thread(target = relay, daemon = True).start()    # The relay actually talks to the engine
    app = Root()
    app.mainloop()
