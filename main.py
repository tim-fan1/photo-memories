# 

import pygame
import math

class Sprite(pygame.sprite.Sprite):
	def __init__(self, spritesheet, colour_key, center, left, top, width, height):
		super().__init__()
		self.sprite_original = pygame.Surface((width, height)).convert_alpha()
		self.sprite_original.set_colorkey(colour_key)
		self.sprite_original.blit(spritesheet, (0,0), (left, top, width, height))
		self.center = center

		# Transformations on the sprite will replace this, not the original
		self.sprite = self.sprite_original

class App:
	def __init__(self):
		# Initiate the pygame module and create the main display
		pygame.init()
		self.screen_width, self.screen_height = 640, 1000
		self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

		# Load the main spritesheet
		self.colour_key = (255, 255, 255)
		self.colour_bg = (150, 150, 150)
		self.colour_main = (0, 0, 0)
		self.line_width = 8
		self.spritesheet = pygame.image.load("spritesheet.png")

		# Load the main sprites
		self.minute_hand = Sprite(self.spritesheet, self.colour_key, 
			(self.screen_width * 0.50, self.screen_height * 0.75), 
			0, 124, 256, 8)

		# Let's start running the game!!
		self.running = True
		self.drawing = False

		# For maintaining the frame rate of game loop
		self.fps = pygame.time.Clock()

		# Do the game loop
		while self.running:
			for event in pygame.event.get():
				self.on_event(event)
			self.on_loop()
			self.fps.tick(60)
		pygame.quit()

	def on_event(self, event):
		if event.type == pygame.QUIT:
			# User wants to quit
			self.running = False
		if event.type == pygame.MOUSEBUTTONDOWN:
			# User wants to draw, but are they clicking on the clock?
			self.drawing = True
			pass
		if event.type == pygame.MOUSEBUTTONUP:
			# User wants to stop drawing
			self.drawing = False
			pass

	def on_loop(self):
		# Clear the screen
		self.screen.fill(self.colour_bg)

		# Blit the clock onto bottom half of screen; the outer border, the pivot centre, and the minute hand
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.center, 150, self.line_width)
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.center, self.line_width, self.line_width)

		# Update the sprite
		if self.drawing:
			pos = pygame.mouse.get_pos()
			x = pos[0] - self.minute_hand.center[0]
			y = -(pos[1] - self.minute_hand.center[1])
			angle = math.degrees(math.atan2(y, x))

			self.minute_hand.sprite = pygame.transform.rotate(self.minute_hand.sprite_original, angle).convert_alpha()

		# Render the sprite
		self.screen.blit(self.minute_hand.sprite, self.minute_hand.sprite.get_rect(center = self.minute_hand.center))

		# TODO: Blit the photo onto top half of screen

		# Render
		pygame.display.flip()

if __name__ == "__main__":
	app = App()
