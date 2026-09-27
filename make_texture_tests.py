from PIL import Image
import numpy as np

def save_gray(path, size=512, value=128):
    img = np.full((size, size), value, dtype=np.uint8)
    Image.fromarray(img).save(path)

def save_vertical_stripes(path, size=512, stripe_width=16):
    img = np.zeros((size, size), dtype=np.uint8)
    for x in range(size):
        if (x // stripe_width) % 2 == 0:
            img[:, x] = 255
    Image.fromarray(img).save(path)

def save_horizontal_stripes(path, size=512, stripe_width=16):
    img = np.zeros((size, size), dtype=np.uint8)
    for y in range(size):
        if (y // stripe_width) % 2 == 0:
            img[y, :] = 255
    Image.fromarray(img).save(path)

def save_checkerboard(path, size=512, block_size=32):
    img = np.zeros((size, size), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            if ((x // block_size) + (y // block_size)) % 2 == 0:
                img[y, x] = 255
    Image.fromarray(img).save(path)

save_gray("texture_uniform.png")
save_vertical_stripes("texture_vertical.png")
save_horizontal_stripes("texture_horizontal.png")
save_checkerboard("texture_checkerboard.png")

print("Test images created successfully.")