import pygame
import math
from PIL import Image, ImageOps
from pathlib import Path
from pillow_heif import register_heif_opener

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
	def __init__(self, photos):
		self.ii = 0

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
			crop_rect=pygame.Rect(0, 124, 256, 8)
		)

		print(len(photos))

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
			fps.tick(10)
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

		# Update the minute_hand sprite's rotation based on mouse position.
		if self.drawing:
			pos = pygame.mouse.get_pos()
			x = pos[0] - self.minute_hand.screen_centre[0]
			y = -(pos[1] - self.minute_hand.screen_centre[1])
			angle = math.degrees(math.atan2(y, x))

			self.minute_hand.sprite = pygame.transform.rotate(self.minute_hand.sprite_original, angle).convert_alpha()

		# Render the minute_hand sprite.
		self.screen.blit(self.minute_hand.sprite, self.minute_hand.sprite.get_rect(center=self.minute_hand.screen_centre))

		# Hack: Blit the pygame image self.photos[i]
		# TODO: self.ii is dependent on how many turns user has made of the clock hand.
		self.ii += 1
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
	# For reading HEIC files.
	register_heif_opener()

	# First, clear existing ./photos folder.
	photos = Path("./photos").glob("*")
	for photo in photos:
		photo.unlink()

	# Rename all ./originals to be their EXIF date taken 
	# timestamp, placing into the cleared ./photos.
	originals = Path("./originals").glob("*")
	for original in originals:
		rename_photo_date_taken(original)

	# So that sorting ./photos by name is sorting photos by date taken.
	photos = list(Path("./photos").glob("*"))
	photos.sort()

	# # This is proof!
	# for photo in photos:
	# 	show_photo(photo)

	# Run game with this set of photos.
	App(photos)
