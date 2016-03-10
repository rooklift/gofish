import os, pygame, sys
from pygame.locals import *
import sgf

if len(sys.argv) != 2:
	os.exit(1)


WIDTH, HEIGHT = 601, 601

# Initialise...

pygame.mixer.pre_init(frequency=22050, size=-16, channels=16, buffer=512)		# Reduces audio lag
pygame.init()
pygame.mixer.init()

fpsClock = pygame.time.Clock()

# Load resources...

directory = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(directory)	# Set working dir to be same as infile.

spriteGoban = pygame.image.load("gfx/goban.png")
spriteBlack = pygame.image.load("gfx/black.png")
spriteWhite = pygame.image.load("gfx/white.png")

# Initialise the window...

virtue = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame SGF (use arrow keys)")

# Input device states...

keyboard = dict()

# Utility functions...

def cleanexit():
	pygame.quit()
	sys.exit()

def blit(target, source, x, y):
	topleftx = x - source.get_width() / 2
	toplefty = y - source.get_height() / 2
	target.blit(source, (topleftx, toplefty))

def blit_without_adjust(target, source, x, y):
	target.blit(source, (x, y))

# Game...

node = sgf.load(sys.argv[1])

while 1:

	# Update keyboard states...

	for event in pygame.event.get():

		if event.type == QUIT:
			cleanexit()

		if event.type == KEYDOWN:
			keyboard[event.key] = 1
		if event.type == KEYUP:
			keyboard[event.key] = 0

	blit_without_adjust(virtue, spriteGoban, 0, 0)

	for x in range(20):
		for y in range(20):
			if node.board.state[x][y] == sgf.BLACK:
				blit(virtue, spriteBlack, 30 * x, 30 * y)
			elif node.board.state[x][y] == sgf.WHITE:
				blit(virtue, spriteWhite, 30 * x, 30 * y)

	if keyboard.get(K_DOWN, 0):
		keyboard[K_DOWN] = 0
		try:
			node = node.children[0]
		except:
			pass

	if keyboard.get(K_UP, 0):
		keyboard[K_UP] = 0
		if node.parent:
			node = node.parent

	if keyboard.get(K_RIGHT, 0):
		keyboard[K_RIGHT] = 0
		for n in range(10):
			try:
				node = node.children[0]
			except:
				pass

	if keyboard.get(K_LEFT, 0):
		keyboard[K_LEFT] = 0
		for n in range(10):
			if node.parent:
				node = node.parent

	pygame.display.update()
	fpsClock.tick(30)
