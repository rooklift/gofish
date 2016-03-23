import os, sys
import tkinter, tkinter.filedialog, tkinter.messagebox

import gofish
from gofish import BLACK, WHITE

WIDTH, HEIGHT = 621, 621
GAP = 31

MOTD = """
  Fohristiwhirl's SGF readwriter. Keys:

  -- LOAD / SAVE: Ctrl-O, Ctrl-S

  -- NAVIGATE: Arrows, Home, End, PageUp, PageDown
  -- SWITCH TO SIBLING: Tab
  -- RETURN TO MAIN LINE: Backspace
  -- DESTROY NODE: Delete

  -- MAKE MOVE: Mouse Button
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
# Currently everything that returns a value is outside the class...

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

class SGF_Board(tkinter.Canvas):
    def __init__(self, owner, filename, *args, **kwargs):
        tkinter.Canvas.__init__(self, owner, *args, **kwargs)

        self.owner = owner

        self.bind("<Key>", self.call_keypress_handler)
        self.bind("<Button-1>", self.mouseclick_handler)
        self.bind("<Control-o>", self.opener)
        self.bind("<Control-s>", self.saver)

        self.node = gofish.new_tree(19)        # Do this now in case the load fails

        self.directory = os.path.dirname(os.path.realpath(sys.argv[0]))

        if filename is not None:
            self.open_file(filename)

        self.node_changed()

    def open_file(self, infilename):
        try:
            self.node = gofish.load(infilename)
            try:
                print("<--- Loaded: {}\n".format(infilename))
            except:
                print("<--- Loaded: --- Exception when trying to print filename ---")
            self.node.dump(include_comments = False)
            print()
            self.directory = os.path.dirname(os.path.realpath(infilename))
        except FileNotFoundError:
            print("error while loading: file not found")
        except gofish.BadBoardSize:
            print("error while loading: SZ (board size) was not in range 1:19")
        except gofish.ParserFail:
            print("error while loading: parser failed (invalid SGF?)")

    def draw_node(self):
        self.delete(tkinter.ALL)              # DESTROY all!
        boardsize = self.node.board.boardsize

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

    def node_changed(self):
        self.draw_node()
        commentwindow.node_changed(self.node)
        infowindow.node_changed(self.node)
        self.owner.wm_title(title_bar_string(self.node))

    # --------------------------------------------------------------------------------------
    # All the key handlers are in the same form:
    #
    # def handle_key_NAME(self):
    #     <do stuff>
    #
    # where NAME is an uppercase version of the event.keysym, see:
    # http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/key-names.html
    #
    # One can make a new key handler just by creating it, no other work is needed anywhere

    def call_keypress_handler(self, event):
        try:
            function_call = "self.handle_key_{}()".format(event.keysym.upper())
            eval(function_call)
        except AttributeError:
            pass

    # ----- (the above makes the following work) -----

    def handle_key_DOWN(self):
        try:
            self.node = self.node.children[0]
            self.node_changed()
        except IndexError:
            pass

    def handle_key_RIGHT(self):
        self.handle_key_DOWN()

    def handle_key_UP(self):
        if self.node.parent:
            self.node = self.node.parent
            self.node_changed()

    def handle_key_LEFT(self):
        self.handle_key_UP()

    def handle_key_NEXT(self):          # PageDown
        for n in range(10):
            try:
                self.node = self.node.children[0]
            except IndexError:
                break
        self.node_changed()

    def handle_key_PRIOR(self):         # PageUp
        for n in range(10):
            if self.node.parent:
                self.node = self.node.parent
            else:
                break
        self.node_changed()

    def handle_key_TAB(self):
        if self.node.parent:
            if len(self.node.parent.children) > 1:
                index = self.node.parent.children.index(self.node)
                if index < len(self.node.parent.children) - 1:
                    index += 1
                else:
                    index = 0
                self.node = self.node.parent.children[index]
                self.node_changed()

    def handle_key_BACKSPACE(self):         # Return to the main line
        while 1:
            if self.node.is_main_line:
                break
            if self.node.parent is None:
                break
            self.node = self.node.parent
        self.node_changed()

    def handle_key_HOME(self):
        self.node = self.node.get_root_node()
        self.node_changed()

    def handle_key_END(self):
        self.node = self.node.get_end_node()
        self.node_changed()

    def handle_key_DELETE(self):
        if len(self.node.children) > 0:
            ok = tkinter.messagebox.askokcancel("Delete?", "Delete this node and all of its children?")
        else:
            ok = True
        if ok:
            if self.node.parent:
                child = self.node
                self.node = self.node.parent
                self.node.children.remove(child)
                self.node.fix_main_line_status_recursive()
                self.node_changed()
            else:
                self.node = gofish.new_tree(19)
                self.node_changed()

    def handle_key_P(self):
        self.node = self.node.make_pass()
        self.node_changed()

    def handle_key_D(self):
        self.node.debug()

    # Other handlers...

    def opener(self, event = None):
        infilename = tkinter.filedialog.askopenfilename(initialdir = self.directory)
        if infilename:
            self.open_file(infilename)      # this also sets self.directory to match the location
            self.node_changed()

    def saver(self, event = None):
        outfilename = tkinter.filedialog.asksaveasfilename(defaultextension = ".sgf", initialdir = self.directory)
        if outfilename:
            commentwindow.commit_text()             # tell the comment window that it must commit the comment
            infowindow.commit_info()                # likewise for the info window
            gofish.save_file(outfilename, self.node)
            try:
                print("---> Saved: {}\n".format(outfilename))
            except:
                print("---> Saved: --- Exception when trying to print filename ---")
            self.directory = os.path.dirname(os.path.realpath(outfilename))

    def mouseclick_handler(self, event):
        x, y = board_pos_from_screen_pos(event.x, event.y, self.node.board.boardsize)
        result = self.node.try_move(x, y)
        if result:
            self.node = result
            self.node_changed()

    def new_board(self, size):
        # if self.node.parent or len(self.node.children) > 0:
        #     ok = tkinter.messagebox.askokcancel("New board?", "Really start a new board? Unsaved changes will be lost!")
        # else:
        #     ok = True
        # if ok:
            self.node = gofish.new_tree(size)
            self.node_changed()

# ---------------------------------------------------------------------------------------

class CommentWindow(tkinter.Toplevel):

    def __init__(self, *args, **kwargs):

        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.title("Comments")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self.text_widget = tkinter.Text(self, width = 60, height = 10, bg = "#F0F0F0", wrap = tkinter.WORD)
        self.scrollbar = tkinter.Scrollbar(self)

        self.text_widget.pack(side = tkinter.LEFT, fill = tkinter.Y)
        self.scrollbar.pack(side = tkinter.RIGHT, fill = tkinter.Y)

        self.resizable(width = False, height = False)

        self.text_widget.config(yscrollcommand = self.scrollbar.set)
        self.scrollbar.config(command = self.text_widget.yview)

        self.node = gofish.Node(None)  # This is just a dummy node until we get a real one.

    def node_changed(self, newnode):

        if newnode is self.node:
            return

        self.commit_text()
        self.node = newnode

        s = self.node.get_unescaped_concat("C")

        self.text_widget.delete(1.0, tkinter.END)
        self.text_widget.insert(tkinter.END, s)

    def commit_text(self):
        s = self.text_widget.get(1.0, tkinter.END).strip()
        self.node.safe_commit("C", s)


class InfoWindow(tkinter.Toplevel):
    def __init__(self, *args, **kwargs):

        tkinter.Toplevel.__init__(self, *args, **kwargs)
        self.title("Game Info")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.resizable(width = False, height = False)

        self.root = gofish.Node(None)  # This is just a dummy node until we get a real one.

        self.widgets = dict()   # key (e.g. "KM") ---> Entry widget

        # Top section: player names and ranks...

        tkinter.Label(self, text = " Player Black ").grid(column = 0, row = 0)
        tkinter.Label(self, text = " Player White ").grid(column = 0, row = 1)
        tkinter.Label(self, text = " Rank ").grid(column = 2, row = 0)
        tkinter.Label(self, text = " Rank ").grid(column = 2, row = 1)

        self.widgets["PB"] = tkinter.Entry(self, width = 30)
        self.widgets["PW"] = tkinter.Entry(self, width = 30)
        self.widgets["BR"] = tkinter.Entry(self, width = 10)
        self.widgets["WR"] = tkinter.Entry(self, width = 10)

        self.widgets["PB"].grid(column = 1, row = 0)
        self.widgets["PW"].grid(column = 1, row = 1)
        self.widgets["BR"].grid(column = 3, row = 0)
        self.widgets["WR"].grid(column = 3, row = 1)

        tkinter.Label(self, text="").grid(column = 0, columnspan = 4, row = 2)

        # Mid section: various metadata...

        tkinter.Label(self, text = "Event").grid(column = 0, row = 3)
        tkinter.Label(self, text = "Game").grid(column = 0, row = 4)
        tkinter.Label(self, text = "Place").grid(column = 0, row = 5)
        tkinter.Label(self, text = "Date").grid(column = 0, row = 6)

        self.widgets["EV"] = tkinter.Entry(self, width = 30)
        self.widgets["GN"] = tkinter.Entry(self, width = 30)
        self.widgets["PC"] = tkinter.Entry(self, width = 30)
        self.widgets["DT"] = tkinter.Entry(self, width = 30)

        self.widgets["EV"].grid(column = 1, row = 3)
        self.widgets["GN"].grid(column = 1, row = 4)
        self.widgets["PC"].grid(column = 1, row = 5)
        self.widgets["DT"].grid(column = 1, row = 6)

        tkinter.Label(self, text="").grid(column = 0, columnspan = 4, row = 7)

        # Bottom section: result...

        tkinter.Label(self, text = "Komi").grid(column = 0, row = 8)
        tkinter.Label(self, text = "Result").grid(column = 0, row = 9)

        self.widgets["KM"] = tkinter.Entry(self, width = 30)
        self.widgets["RE"] = tkinter.Entry(self, width = 30)

        self.widgets["KM"].grid(column = 1, row = 8)
        self.widgets["RE"].grid(column = 1, row = 9)


    def node_changed(self, node):

        # For simplicity, this widget gets notified every time the viewer's node changes,
        # regardless of whether the root is still the same. So we need to check for that.

        newroot = node.get_root_node()
        if newroot is self.root:
            return

        self.commit_info()
        self.root = newroot

        for key in self.widgets:                            # e.g. key is "RE" or "KM" etc...
            text = self.root.get_unescaped_concat(key)      # pull the value from the root node
            self.widgets[key].delete(0, tkinter.END)
            self.widgets[key].insert(tkinter.END, text)     # and set the widget to it

    def commit_info(self):

        for key in self.widgets:                            # e.g. key is "RE" or "KM" etc...
            text = self.widgets[key].get().strip()          # pull the value from the widget
            self.root.safe_commit(key, text)                # and set the root node accordingly


class HelpWindow(tkinter.Toplevel):
    def __init__(self, *args, **kwargs):

        tkinter.Toplevel.__init__(self, *args, **kwargs)

        self.resizable(width = False, height = False)

        self.title("Help")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        tkinter.Label(self, text = MOTD, justify = tkinter.LEFT).grid(row = 0, column = 0)
        tkinter.Label(self, text = "  ").grid(row = 0, column = 1)


class Root(tkinter.Tk):
    def __init__(self, *args, **kwargs):

        tkinter.Tk.__init__(self, *args, **kwargs)
        self.resizable(width = False, height = False)

        load_graphics()

        if len(sys.argv) > 1:
            filename = sys.argv[1]
        else:
            filename = None

        self.protocol("WM_DELETE_WINDOW", self.quit)

        global commentwindow
        commentwindow = CommentWindow()
        commentwindow.withdraw()    # comment window starts hidden

        global infowindow
        infowindow = InfoWindow()
        infowindow.withdraw()       # info window starts hidden

        global helpwindow
        helpwindow = HelpWindow()
        helpwindow.withdraw()       # help window starts hidden

        global board
        board = SGF_Board(self, filename, width = WIDTH, height = HEIGHT, bd = 0, highlightthickness = 0)

        menubar = tkinter.Menu(self)

        new_board_menu = tkinter.Menu(menubar, tearoff = 0)
        new_board_menu.add_command(label="19x19", command = lambda : board.new_board(19))
        new_board_menu.add_command(label="17x17", command = lambda : board.new_board(17))
        new_board_menu.add_command(label="15x15", command = lambda : board.new_board(15))
        new_board_menu.add_command(label="13x13", command = lambda : board.new_board(13))
        new_board_menu.add_command(label="11x11", command = lambda : board.new_board(11))
        new_board_menu.add_command(label="9x9", command = lambda : board.new_board(9))

        menubar.add_cascade(label = "New", menu = new_board_menu)

        menubar.add_command(label = "Load", command = board.opener)
        menubar.add_command(label = "Save", command = board.saver)
        menubar.add_command(label = "Comments", command = commentwindow.deiconify)
        menubar.add_command(label = "Info", command = infowindow.deiconify)
        menubar.add_command(label = "Help", command = helpwindow.deiconify)

        self.config(menu = menubar)

        board.pack()
        board.focus_set()


if __name__ == "__main__":
    print(MOTD)

    app = Root()
    app.mainloop()
