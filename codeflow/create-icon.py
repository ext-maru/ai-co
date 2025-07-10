#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw

# Create a 128x128 icon
size = 128
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background (blue gradient effect)
draw.rounded_rectangle([0, 0, 127, 127], radius=16, fill=(74, 144, 226, 255))

# Robot body
draw.rounded_rectangle([32, 48, 95, 95], radius=8, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)

# Robot head
draw.rounded_rectangle([40, 24, 87, 55], radius=6, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)

# Eyes
draw.ellipse([48, 32, 56, 40], fill=(74, 144, 226, 255))
draw.ellipse([72, 32, 80, 40], fill=(74, 144, 226, 255))

# Antenna
draw.line([64, 24, 64, 16], fill=(51, 51, 51, 255), width=2)
draw.ellipse([62, 14, 66, 18], fill=(255, 107, 107, 255))

# Arms
draw.rounded_rectangle([20, 56, 31, 79], radius=6, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)
draw.rounded_rectangle([96, 56, 107, 79], radius=6, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)

# Legs
draw.rounded_rectangle([44, 96, 55, 119], radius=6, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)
draw.rounded_rectangle([72, 96, 83, 119], radius=6, fill=(245, 245, 245, 255), outline=(51, 51, 51, 255), width=2)

# Chest panel
draw.rounded_rectangle([44, 60, 83, 79], radius=4, fill=(74, 144, 226, 80))

# Save the image
img.save('images/icon.png')
print("Icon created successfully!")