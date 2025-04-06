import gzip
import os

import matplotlib.pyplot as plt
import numpy as np

def gz_file_to_ndarray(path: str) -> np.ndarray:
    with gzip.open(path, "rb") as file:
        header = file.read(4 * 3)
        shape = tuple(int.from_bytes(header[i:i + 4], "little") for i in range(0, len(header), 4))
        data = file.read()
    return np.frombuffer(data, dtype=np.float32).reshape(shape).copy()

file_path = os.path.dirname(os.path.abspath(__file__))
image_orientation_depth_rgb = gz_file_to_ndarray(os.path.join(file_path, "render.bin.gz"))
print("Image Orientation-Depth RGB shape:", image_orientation_depth_rgb.shape)

# image_orientation_depth_rgb = np.flip(image_orientation_depth_rgb, axis=0)

# max_rgb = image_orientation_depth_rgb[:, :, 2:].max()
# image_orientation_depth_rgb[:, :, 2:] /= max_rgb

# gamma = 2.2
# image_orientation_depth_rgb[:, :, 2:] = np.power(image_orientation_depth_rgb[:, :, 2:], 1.0 / gamma)

plt.imshow(image_orientation_depth_rgb[:, :, 2:])
plt.title("Preview of RGB Channels")
plt.axis("off")
plt.show()

