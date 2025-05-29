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
image_depth_orientation_value = gz_file_to_ndarray(os.path.join(file_path, "render_dov.bin.gz"))
print("Image Depth-Orientation-Value shape:", image_depth_orientation_value.shape)


fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(image_depth_orientation_value[:, :, 0])
axes[0].set_title("Depth Channel")
axes[0].axis("off")

axes[1].imshow(image_depth_orientation_value[:, :, 1])
axes[1].set_title("Orientation Channel")
axes[1].axis("off")

axes[2].imshow(image_depth_orientation_value[:, :, 2])
axes[2].set_title("Value Channel")
axes[2].axis("off")

plt.tight_layout()
plt.show()
