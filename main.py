# 

import pygame
import math

class Sprite():
	def __init__(self, spritesheet, colour_key, screen_centre, crop_rect):
		# Creating the sprite involves cropping the spritesheet based on crop_rect
		# and placing that onto a surface of the same size, copying each pixel from 
		# cropped sheet to the surface pixel-by pixel. 
		self.sprite_original = pygame.Surface((crop_rect.width, crop_rect.height)).convert_alpha()

		# Avoid copying the colour_key pixels -- the background colour of the opaque spritesheet -- to the 
		# surface by setting the colour key of the surface to be colour_key before copying; so that only 
		# non background pixels are blitted to the surface.
		self.sprite_original.set_colorkey(colour_key)
		self.sprite_original.blit(spritesheet, (0,0), crop_rect)

		# Hack: Where the sprite's centre should be drawn onto the screen surface...
		self.screen_centre = screen_centre

		# Transformations on the sprite will replace this, not the original.
		self.sprite = self.sprite_original

class App:
	def __init__(self):
		# Initiate the pygame module and create the main display.
		pygame.init()
		screen_width, screen_height = 640, 1000
		self.screen = pygame.display.set_mode((screen_width, screen_height))

		# Load the main spritesheet, which has an opaque background of white.
		spritesheet = pygame.image.load("spritesheet.png").convert()
		spritesheet_colour_key = (255, 255, 255)

		# Load the main sprites.
		self.minute_hand = Sprite(
			spritesheet = spritesheet, 
			colour_key =  spritesheet_colour_key,
			screen_centre = (screen_width * 0.50, screen_height * 0.75), 
			crop_rect = pygame.Rect(0, 124, 256, 8)
		)

		# Other colours needed for the game.
		self.colour_bg = (150, 150, 150)
		self.colour_main = (0, 0, 0)
		self.line_width = 8

		# Let's start running the game!!
		self.running = True
		self.drawing = False

		# For maintaining the frame rate of game loop
		fps = pygame.time.Clock()

		# Do the game loop
		while self.running:
			for event in pygame.event.get():
				self.event(event)
			self.loop()
			fps.tick(60)
		pygame.quit()

	def event(self, event):
		if event.type == pygame.QUIT:
			# User wants to quit
			self.running = False
		if event.type == pygame.MOUSEBUTTONDOWN:
			# User wants to draw
			self.drawing = True
			pass
		if event.type == pygame.MOUSEBUTTONUP:
			# User wants to stop drawing
			self.drawing = False
			pass

	def loop(self):
		# Clear the screen
		self.screen.fill(self.colour_bg)

		# Blit the clock onto bottom half of screen; this is the outer border and pivot centre shapes.
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.screen_centre, 150, self.line_width)
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.screen_centre, self.line_width, self.line_width)

		# Update the minute_hand sprite's rotation based on mouse position.
		if self.drawing:
			pos = pygame.mouse.get_pos()
			x = pos[0] - self.minute_hand.screen_centre[0]
			y = -(pos[1] - self.minute_hand.screen_centre[1])
			angle = math.degrees(math.atan2(y, x))

			self.minute_hand.sprite = pygame.transform.rotate(self.minute_hand.sprite_original, angle).convert_alpha()

		# Render the minute_hand sprite.
		self.screen.blit(self.minute_hand.sprite, self.minute_hand.sprite.get_rect(center = self.minute_hand.screen_centre))

		# TODO: Blit the photo onto top half of screen

		# Double buffering.
		pygame.display.flip()

if __name__ == "__main__":
	app = App()
