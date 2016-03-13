import os, pygame, sys
from pygame.locals import *
import tkinter
import tkinter.filedialog
import sgf

tkinter.Tk().withdraw()		# tkinter is just used for its file dialog; suppress its window

WIDTH, HEIGHT = 621, 621
GAP = 31

# Initialise...

pygame.mixer.pre_init(frequency=22050, size=-16, channels=16, buffer=512)		# Reduces audio lag
pygame.init()
pygame.mixer.init()

fpsClock = pygame.time.Clock()

# Load resources...

directory = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(directory)	# Set working dir to be same as infile.

spriteHoshi = pygame.image.load("gfx/hoshi.png")
spriteBlack = pygame.image.load("gfx/black.png")
spriteWhite = pygame.image.load("gfx/white.png")
spriteMove = pygame.image.load("gfx/move.png")
spriteVar = pygame.image.load("gfx/var.png")
spriteTriangle = pygame.image.load("gfx/triangle.png")
spriteCircle = pygame.image.load("gfx/circle.png")
spriteSquare = pygame.image.load("gfx/square.png")
spriteMark = pygame.image.load("gfx/mark.png")

markup_dict = {"TR": spriteTriangle, "CR": spriteCircle, "SQ": spriteSquare, "MA": spriteMark}

# Initialise the window...

virtue = pygame.display.set_mode((WIDTH, HEIGHT))

# Input device states...

keyboard = dict()
mousebuttons = dict()
mousex = 1
mousey = 1

# Utility functions...

def cleanexit():
	pygame.quit()
	sys.exit()

def blit(target, source, x, y):

	w = source.get_width()
	h = source.get_height()

	topleftx = x - w / 2
	toplefty = y - h / 2

	if w % 2:
		topleftx += 1
	if h % 2:
		toplefty += 1

	target.blit(source, (topleftx, toplefty))

def blit_without_adjust(target, source, x, y):
	target.blit(source, (x, y))


# --------------------------------------------------------------------------------------------------------------------


def screen_pos_from_board_pos(x, y, boardsize):
	gridsize = GAP * (boardsize - 1) + 1
	margin = (WIDTH - gridsize) // 2
	ret_x = (x - 1) * GAP + margin
	ret_y = (y - 1) * GAP + margin
	return ret_x, ret_y


def board_pos_from_screen_pos(x, y, boardsize):		# Inverse of the above
	gridsize = GAP * (boardsize - 1) + 1
	margin = (WIDTH - gridsize) // 2
	ret_x = round((x - margin) / GAP + 1)
	ret_y = round((y - margin) / GAP + 1)
	return ret_x, ret_y


def draw_node(screen, node):

	# Draw the board...

	blit_without_adjust(screen, spriteGoban, 0, 0)

	# Draw the stones...

	for x in range(1, node.board.boardsize + 1):
		for y in range(1, node.board.boardsize + 1):
			screen_x, screen_y = screen_pos_from_board_pos(x, y, node.board.boardsize)
			if node.board.state[x][y] == sgf.BLACK:
				blit(screen, spriteBlack, screen_x, screen_y)
			elif node.board.state[x][y] == sgf.WHITE:
				blit(screen, spriteWhite, screen_x, screen_y)

	# Draw a mark at the current move, if there is one...

	move = node.what_was_the_move()
	if move is not None:
		screen_x, screen_y = screen_pos_from_board_pos(move[0], move[1], node.board.boardsize)
		blit(screen, spriteMove, screen_x, screen_y)

	# Draw a mark at variations, if there are any...

	for sib_move in node.sibling_moves():
		screen_x, screen_y = screen_pos_from_board_pos(sib_move[0], sib_move[1], node.board.boardsize)
		blit(screen, spriteVar, screen_x, screen_y)

	# Draw the commonly used marks...

	for mark in markup_dict:
		if mark in node.properties:
			points = set()
			for value in node.properties[mark]:
				points |= sgf.points_from_points_string(value, node.board.boardsize)
			for point in points:
				screen_x, screen_y = screen_pos_from_board_pos(point[0], point[1], node.board.boardsize)
				blit(screen, markup_dict[mark], screen_x, screen_y)


def make_spriteGoban(boardsize):

	global spriteGoban
	spriteGoban = pygame.image.load("gfx/texture.jpg")

	# Patch up spriteGoban with the grid and hoshi points drawn...

	for n in range(1, boardsize + 1):
		start = screen_pos_from_board_pos(n, 1, boardsize)
		end = screen_pos_from_board_pos(n, boardsize, boardsize)
		pygame.draw.line(spriteGoban, pygame.Color(0, 0, 0), start, end)

	for n in range(1, boardsize + 1):
		start = screen_pos_from_board_pos(1, n, boardsize)
		end = screen_pos_from_board_pos(boardsize, n, boardsize)
		pygame.draw.line(spriteGoban, pygame.Color(0, 0, 0), start, end)

	for x in range(3, boardsize - 1):
		for y in range(boardsize - 1):
			if sgf.is_star_point(x, y, boardsize):
				screen_x, screen_y = screen_pos_from_board_pos(x, y, boardsize)
				blit(spriteGoban, spriteHoshi, screen_x, screen_y)


def main():

	print()

	# Load the game...

	if len(sys.argv) > 1:
		node = sgf.load(sys.argv[1])
		node.print_comments()
	else:
		node = sgf.new_tree(19)

	make_spriteGoban(node.board.boardsize)

	while 1:

		# Handle events (update keyboard / mousebutton dicts, etc)

		for event in pygame.event.get():
			if event.type == KEYDOWN:
				keyboard[event.key] = 1
			if event.type == KEYUP:
				keyboard[event.key] = 0
			if event.type == MOUSEBUTTONDOWN:		# Note: there are multiple mouse buttons
				mousebuttons[event.button] = 1
			if event.type == MOUSEBUTTONUP:
				mousebuttons[event.button] = 0
			if event.type == MOUSEMOTION:
				mousex, mousey = event.pos

			if event.type == QUIT:
				cleanexit()

		# Handle input if a key is down. Set the key to be up to avoid repetitions...

		if keyboard.get(K_DOWN, 0) or keyboard.get(K_RIGHT, 0):
			keyboard[K_DOWN] = 0
			keyboard[K_RIGHT] = 0
			try:
				node = node.children[0]
				node.print_comments()
			except IndexError:
				pass

		if keyboard.get(K_UP, 0) or keyboard.get(K_LEFT, 0):
			keyboard[K_UP] = 0
			keyboard[K_LEFT] = 0
			if node.parent:
				node = node.parent

		if keyboard.get(K_PAGEDOWN, 0):
			keyboard[K_PAGEDOWN] = 0
			for n in range(10):
				try:
					node = node.children[0]
					node.print_comments()
				except IndexError:
					break

		if keyboard.get(K_PAGEUP, 0):
			keyboard[K_PAGEUP] = 0
			for n in range(10):
				if node.parent:
					node = node.parent
				else:
					break

		if keyboard.get(K_TAB, 0):
			keyboard[K_TAB] = 0
			if node.parent:
				if len(node.parent.children) > 1:
					index = node.parent.children.index(node)
					if index < len(node.parent.children) - 1:
						index += 1
					else:
						index = 0
					node = node.parent.children[index]
					node.print_comments()

		if keyboard.get(K_BACKSPACE, 0):		# Return to the main line
			keyboard[K_BACKSPACE] = 0
			while 1:
				if node.is_main_line:
					break
				if node.parent is None:
					break
				node = node.parent

		if keyboard.get(K_HOME, 0):
			keyboard[K_HOME] = 0
			node = node.get_root_node()

		if keyboard.get(K_END, 0):
			keyboard[K_END] = 0
			node = node.get_end_node()

		if keyboard.get(K_d, 0):
			keyboard[K_d] = 0
			node.debug()

		if keyboard.get(K_s, 0):
			keyboard[K_s] = 0
			outfilename = tkinter.filedialog.asksaveasfilename(defaultextension=".sgf")
			if outfilename:
				sgf.save_file(outfilename, node)

		if keyboard.get(K_l, 0):
			keyboard[K_l] = 0
			infilename = tkinter.filedialog.askopenfilename()
			if infilename:
				try:
					node = sgf.load(infilename)
					make_spriteGoban(node.board.boardsize)
				except FileNotFoundError:
					print("error while loading: file not found")
				except sgf.BoardTooBig:
					print("error while loading: SZ (board size) was not in range 1:19")

		# Mouse clicks either add a new move, or descend to the child node if it's already there...

		if mousebuttons.get(1, 0):
			mousebuttons[1] = 0
			x, y = board_pos_from_screen_pos(mousex, mousey, node.board.boardsize)
			result = node.try_move(x, y)
			if result:
				node = result

		# Set the title...

		title = "Move {}".format(node.moves_made)
		if node.parent:
			if len(node.parent.children) > 1:
				index = node.parent.children.index(node)
				title += " ({} of {} variations)".format(index + 1, len(node.parent.children))
		pygame.display.set_caption(title)

		# Draw the node...

		draw_node(virtue, node)

		# Update and wait...

		pygame.display.update()
		fpsClock.tick(30)


if __name__ == "__main__":
	main()
