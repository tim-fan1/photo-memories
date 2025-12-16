#!/usr/bin/env python3

import pygame
import math
from PIL import Image, ImageOps
from pathlib import Path
from pillow_heif import register_heif_opener

class Sprite():
	def __init__(self, spritesheet, colour_key, screen_centre, crop_rect, starting_angle):
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

		# Counterclockwise rotation about self.screen_centre and the positive x-axis.
		self.curr_angle = starting_angle

class App:
	def __init__(self, photos):
		# TODO: A reminder that this is a bad name for index and yeah...
		self.ii = 0
		self.mouse_prev_angle = 0

		# Initiate the pygame module and create the main display.
		pygame.init()
		self.screen_width, self.screen_height = 640, 1000
		self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

		# Load the main spritesheet, which has an opaque background of white.
		spritesheet = pygame.image.load("spritesheet.png").convert()
		spritesheet_colour_key = (255, 255, 255)

		# Load the main sprites.
		self.minute_hand = Sprite(
			spritesheet=spritesheet, 
			colour_key= spritesheet_colour_key,
			screen_centre=(self.screen_width * 0.50, self.screen_height * 0.8), 
			crop_rect=pygame.Rect(0, 124, 256, 8),
			starting_angle=90
		)

		# Load all photos
		self.photos = [pygame.image.load(f"{photos[idx].parent}/{photos[idx].name}").convert() for idx in range(0, len(photos))]

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
		elif event.type == pygame.MOUSEBUTTONDOWN:
			# User wants to draw
			self.drawing = True
		elif event.type == pygame.MOUSEBUTTONUP:
			# User wants to stop drawing
			self.drawing = False

	def loop(self):
		# Clear the screen
		self.screen.fill(self.colour_bg)

		# Blit the clock onto bottom half of screen; this is the outer border and pivot centre shapes.
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.screen_centre, 150, self.line_width)
		pygame.draw.circle(self.screen, self.colour_main, self.minute_hand.screen_centre, self.line_width, self.line_width)

		# Graphical coordinates have (0,0) at the top-left corner, but 
		# Cartesian coordinates have (0,0) at the bottom-left corner, is
		# how I would explain the times by negative one here.
		pos = pygame.mouse.get_pos()
		x = pos[0] - self.minute_hand.screen_centre[0]
		y = pos[1] - self.minute_hand.screen_centre[1]
		mouse_curr_angle = (-1) * math.degrees(math.atan2(y, x))

		# While pygame.transform.rotate moves counterclockwise in angle,
		# clocks move clockwise in time. So moving the clock forward in time
		# is actually moving its angular displacement backward in angle.
		if self.drawing: self.minute_hand.curr_angle -= (self.mouse_prev_angle - mouse_curr_angle)

		# TODO: Remove since this is a fix just for this current proof of concept, where 
		# self.ii is tied to the value of curr_angle, and is very possible for this to 
		# overflow underflow +-360 so that self.ii indexes out of bounds of self.photos.
		self.minute_hand.curr_angle %= 360

		# Update for next frame.
		self.mouse_prev_angle = mouse_curr_angle

		# Update the mutable sprite and not the immutable original sprite.
		#
		# IMPORTANT: note that the amount of rotation is exactly minute_hand.curr_angle. This is because the original 
		# sprite is a horizontal line lying on the positive x-axis. In other words, if the original sprite was a vertical 
		# line facing upward (Cartesian positive y-axis, Graphical negative y-axis) then the sprite should be first rotated 
		# -90 degrees so that it is lying flat on the postive x-axis, and then rotated by minute_hand.curr_angle.
		self.minute_hand.sprite = pygame.transform.rotate(self.minute_hand.sprite_original, self.minute_hand.curr_angle).convert_alpha()

		# Blit the updated minute_hand sprite onto screen.
		self.screen.blit(self.minute_hand.sprite, self.minute_hand.sprite.get_rect(center=self.minute_hand.screen_centre))

		# Hack: Blit the pygame image self.photos[i]
		# TODO: self.ii should be incremented when user has made three turns 1080 degrees of the clock hand.
		#
		# Let's focus on this for now. A reliable curr_angle would make everything more reliable.
		#
		# Current version though, is a good mode of control, like a fastforward fastbackward; maybe triggered 
		# upon shift + mousedown. But it doesn't work properly with current math; need minute_hand.curr_angle 
		# to be more reliable as an index into self.photos that follows time; solution is not the modulus by 360!!
		#
		# Negative one is again because the index into self.photos is how forward
		# in time the clock is, which is how backward in angle the hand is.
		self.ii = int((-1) * self.minute_hand.curr_angle / 360 * len(self.photos))

		# print(f"theta: {self.theta:.4f}\tcurr_angle: {self.minute_hand.curr_angle:.4f}\tii: {self.ii}")
		self.screen.blit(self.photos[self.ii], self.photos[self.ii].get_rect(center=(self.screen_width * 0.50, self.screen_height * 0.33)))

		# Double buffering.
		pygame.display.flip()

def rename_photo_date_taken(original):
	try:
		with Image.open(original) as img:
			# Resize original image and place it into ./photos, renaming it to its 
			# EXIF timestamp, so that the output ./photos folder is alphabetically 
			# sorted by date taken.
			img_exif = img.getexif()
			if img_exif is None or 306 not in img_exif:
				raise ValueError(f"{original} does not have EXIF timestamp")
			size = (600, 600)
			ImageOps.pad(img, size, color="#ffffff").save(
				f"./photos/{img_exif[306]}.jpg", # img_exif[306] is DateTime
				exif = img_exif, 
				format = "JPEG"
			)
	except Exception as error:
		# Remove original with error
		print(f"Error: {error}")
		original.unlink()

def show_photo(photo):
	try:
		with Image.open(photo) as img:
			img.show()
	except Exception as error:
		print(f"Error: {error}")

if __name__ == "__main__":
	# Handler for reading the iPhone HEIC files stored in ./originals.
	# ./photos used for the game should be JPEG's that don't need this;
	# in case they are HEIC files they will still be read successfully.
	register_heif_opener()

	reset = input("Do you want to clear the existing ./photos and replace with new ./originals? (Y/N) ")

	if reset.strip().upper() == "Y":
		# To reset, first clear existing ./photos folder.
		photos = Path("./photos").glob("*")
		for photo in photos:
			photo.unlink()

		# Then rename all ./originals to be their EXIF date 
		# taken timestamp, placing into the cleared ./photos.
		originals = Path("./originals").glob("*")
		for original in originals:
			rename_photo_date_taken(original)

	# So that sorting ./photos by name is sorting photos by date taken.
	# In other words if user chose not to reset, the game will assume the 
	# existing ./photos is already sorted alphabetically by date taken.
	photos = list(Path("./photos").glob("*"))
	photos.sort()

	# # This is proof!
	# for photo in photos:
	# 	show_photo(photo)

	# Run game with this set of photos.
	App(photos)
