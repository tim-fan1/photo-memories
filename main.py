#!/usr/bin/env python3

import pygame
import math
from PIL import Image, ImageOps, ImageFont, ImageDraw
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
		self.screen_angle = starting_angle

class App:
	def __init__(self, photos_paths, photos_index_start):
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
			starting_angle=60
		)

		# Load all photos
		self.photos = [pygame.image.load(f"{photos_paths[idx].parent}/{photos_paths[idx].name}").convert()
			for idx in range(0, len(photos_paths))]
		self.photos_index = photos_index_start

		# Other constants needed for the game.
		self.colour_bg = (150, 150, 150)
		self.colour_main = (0, 0, 0)
		self.line_width = 8

		# Related to angular displacement.
		self.mouse_prev_angle = 0
		self.time_prev_angle = 0
		self.accumulated_theta = 0

		# Related to angular velocity.
		self.rewind_velocity = 0
		self.speed = [20, 10, 5, 3, 2, 0, -2, -3, -5, -10, -20]
		self.speed_index = int(len(self.speed) / 2)

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
			# User wants to quit.
			self.running = False
		elif event.type == pygame.MOUSEBUTTONDOWN:
			# User wants to draw.
			self.drawing = True
		elif event.type == pygame.MOUSEBUTTONUP:
			# User wants to stop drawing.
			self.drawing = False
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
			# User wants to fastforward.
			if event.mod & pygame.KMOD_LSHIFT:
				self.speed_index += 1
				if self.speed_index > len(self.speed) - 1: self.speed_index = len(self.speed) - 1
				self.rewind_velocity = self.speed[self.speed_index]
			else:
				self.rewind_velocity = -1.25
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
			# User wants to fastreverse.
			if event.mod & pygame.KMOD_LSHIFT:
				self.speed_index -= 1
				if self.speed_index < 0: self.speed_index = 0
				self.rewind_velocity = self.speed[self.speed_index]
			else:
				self.rewind_velocity = 1.25
		elif event.type == pygame.KEYUP and not event.mod & pygame.KMOD_LSHIFT:
			# User wants to stop rewinding.
			self.rewind_velocity = 0
			self.speed_index = int(len(self.speed) / 2)

	def loop(self):
		# Clear the screen
		self.screen.fill(self.colour_bg)

		# Blit the clock onto bottom half of screen; this is the outer border and pivot centre shapes.
		pygame.draw.circle(
			self.screen, self.colour_main, self.minute_hand.screen_centre, 150, self.line_width)
		pygame.draw.circle(
			self.screen, self.colour_main, self.minute_hand.screen_centre,
			self.line_width, self.line_width)

		# Calculate the change in mouse angle from last frame to this frame.
		pos = pygame.mouse.get_pos()
		x = pos[0] - self.minute_hand.screen_centre[0]
		y = pos[1] - self.minute_hand.screen_centre[1]
		mouse_curr_angle = 0
		if y < 0:
			# Upper two quadrants.
			mouse_curr_angle = abs(math.degrees(math.atan2(y, x)))
		else:
			# Lower two quadrants.
			mouse_curr_angle = 360 - abs(math.degrees(math.atan2(y, x)))
		mouse_delta_angle = mouse_curr_angle - self.mouse_prev_angle

		# And use that to calculate how far the clock moves.
		if self.drawing:
			# User wants to move clock by mouse.
			self.minute_hand.screen_angle += mouse_delta_angle
		else:
			# User wants to move clock by keyboard.
			self.minute_hand.screen_angle += self.rewind_velocity * 5

		# Mouse angle done.
		self.minute_hand.screen_angle %= 360
		self.mouse_prev_angle = mouse_curr_angle

		# Calculate the change in time angle from last frame to this frame.
		time_curr_angle = (90 - self.minute_hand.screen_angle)
		time_curr_angle %= 360
		time_delta_angle = time_curr_angle - self.time_prev_angle

		# TODO: start transition to next/prev photo at time_curr_angle = 270 and end at time_curr_angle = 90

		# A huge change is an indicator of crossing at 12
		if time_delta_angle > 180: time_delta_angle -= 360
		elif time_delta_angle < -180: time_delta_angle += 360

		# But only if is in between the first and second quadrants.
		if self.time_prev_angle > 270 and time_curr_angle < 90 and time_delta_angle > 0:
			# It was a clockwise crossing at 12.
			self.photos_index += 1
			if self.photos_index > len(self.photos) - 1: self.photos_index = len(self.photos) - 1
		elif self.time_prev_angle < 90 and time_curr_angle > 270 and time_delta_angle < 0:
			# It was a counter-clockwise crossing at 12.
			self.photos_index -= 1
			if self.photos_index < 0: self.photos_index = 0

		# Time angle done.
		self.time_prev_angle = time_curr_angle

		# Update the mutable sprite and not the immutable original sprite, and blit it to screen.
		self.minute_hand.sprite = pygame.transform.rotate(
			self.minute_hand.sprite_original, self.minute_hand.screen_angle).convert_alpha()
		self.screen.blit(
			self.minute_hand.sprite,
			self.minute_hand.sprite.get_rect(center=self.minute_hand.screen_centre))

		# And blit the current photo to screen.
		self.screen.blit(
			self.photos[self.photos_index],
			self.photos[self.photos_index].get_rect(
				center=(self.screen_width * 0.50, self.screen_height * 0.33)))

		# Double buffering.
		pygame.display.flip()

def rename_photo_date_taken(original):
	try:
		with Image.open(original).convert("RGBA") as img:
			# Get date taken.
			date = ["day", "month", "year"]
			new_name = ""

			# From the EXIF datetime.
			img_exif = img.getexif()
			if img_exif is None or 306 not in img_exif:
				# Though if no EXIF datetime, maybe the name of the file can save us.
				old_name = original.name.split("_")
				if old_name[0] != "PXL":
					raise ValueError(f"{original} does not have EXIF timestamp")
				date[0] = old_name[1][0:4] # 1997
				date[1] = old_name[1][4:6] # 01
				date[2] = old_name[1][6:8] # 01
				new_name = f"./photos/{date[0]}:{date[1]}:{date[2]} {old_name[2]}.png"
			else: 
				# There is an EXIF datetime.
				date = img_exif[306].split(" ")[0].split(":")
				new_name = f"./photos/{img_exif[306]}.png"

			# Resize original image to fit within the final size.
			size = (600, 600)
			img = ImageOps.exif_transpose(img)
			img = ImageOps.contain(img, size)

			# Add the date taken as a graphic onto top left corner.
			text = Image.new("RGBA", img.size, (255, 255, 255, 0))
			font = ImageFont.truetype("font.ttf", size=32)
			draw = ImageDraw.Draw(text)
			draw.text((10, 0), f"{int(date[2])}. {int(date[1])}. {int(date[0])}", 
				font=font, fill=(255, 255, 255, 225))
			img = Image.alpha_composite(img, text)

			# Pad rest of size with white.
			img = ImageOps.pad(img, size, color="#ffffff")

			# Save copy to ./photos under new name
			img.save(new_name, format = "PNG")
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
		originals = list(Path("./originals").glob("*"))
		for index, original in enumerate(originals):
			rename_photo_date_taken(original)
			print(f"({index + 1}/{len(originals)})")

	# So that sorting ./photos by name is sorting photos by date taken.
	# In other words if user chose not to reset, the game will assume the 
	# existing ./photos is already sorted alphabetically by date taken.
	photos = list(Path("./photos").glob("*"))
	photos.sort()

	# # This is proof!
	# for photo in photos:
	# 	show_photo(photo)

	# Run game with this set of photos, starting from first photo.
	App(photos_paths=photos, photos_index_start=0)
