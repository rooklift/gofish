import os, pygame, sys
from pygame.locals import *
import sgf

if len(sys.argv) != 2:
	os.exit(1)

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

spriteGoban = pygame.image.load("gfx/texture.jpg")
spriteGrid = pygame.image.load("gfx/grid.png")
spriteHoshi = pygame.image.load("gfx/hoshi.png")
spriteBlack = pygame.image.load("gfx/black.png")
spriteWhite = pygame.image.load("gfx/white.png")
spriteMove = pygame.image.load("gfx/move.png")
spriteVar =  pygame.image.load("gfx/var.png")
spriteTriangle = pygame.image.load("gfx/triangle.png")
spriteCircle = pygame.image.load("gfx/circle.png")
spriteSquare = pygame.image.load("gfx/square.png")
spriteMark = pygame.image.load("gfx/mark.png")

markup_dict = {"TR": spriteTriangle, "CR": spriteCircle, "SQ": spriteSquare, "MA": spriteMark}

# Initialise the window...

virtue = pygame.display.set_mode((WIDTH, HEIGHT))

# Input device states...

keyboard = dict()

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

# Patch up the board with the grid and hoshi points drawn...

blit_without_adjust(spriteGoban, spriteGrid, 0, 0)
for star in sgf.STAR_POINTS:
	blit(spriteGoban, spriteHoshi, star[0] * GAP, star[1] * GAP)

# Game...

node = sgf.load(sys.argv[1])
node.print_comments()

while 1:

	# Update keyboard states...

	for event in pygame.event.get():
		if event.type == QUIT:
			cleanexit()
		if event.type == KEYDOWN:
			keyboard[event.key] = 1
		if event.type == KEYUP:
			keyboard[event.key] = 0

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

	# Set the title...

	title = "Move {}".format(node.moves_made)
	if node.parent:
		if len(node.parent.children) > 1:
			index = node.parent.children.index(node)
			title += " ({} of {} variations)".format(index + 1, len(node.parent.children))
	pygame.display.set_caption(title)

	# Draw the board...

	blit_without_adjust(virtue, spriteGoban, 0, 0)

	# Draw the stones...

	for x in range(1, 20):
		for y in range(1, 20):
			if node.board.state[x][y] == sgf.BLACK:
				blit(virtue, spriteBlack, GAP * x, GAP * y)
			elif node.board.state[x][y] == sgf.WHITE:
				blit(virtue, spriteWhite, GAP * x, GAP * y)

	# Draw a mark at the current move, if there is one...

	move = node.what_was_the_move()
	if move is not None:
		mark_x = move[0]
		mark_y = move[1]
		blit(virtue, spriteMove, GAP * mark_x, GAP * mark_y)

	# Draw a mark at variations, if there are any...

	for sib_move in node.sibling_moves():
		mark_x = sib_move[0]
		mark_y = sib_move[1]
		blit(virtue, spriteVar, GAP * mark_x, GAP * mark_y)

	# Draw the commonly used marks...

	for mark in markup_dict:
		if mark in node.properties:
			points = set()
			for value in node.properties[mark]:
				points |= sgf.points_from_points_list(value)
			for point in points:
				mark_x = point[0]
				mark_y = point[1]
				blit(virtue, markup_dict[mark], GAP * mark_x, GAP * mark_y)

	# Update and wait...

	pygame.display.update()
	fpsClock.tick(30)
