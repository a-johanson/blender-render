import gzip

import numpy as np


def ndarray_to_gz_file(a: np.ndarray, path: str):
    with gzip.open(path, "wb") as file:
        header = b"".join(k.to_bytes(4, "little") for k in a.shape)
        file.write(header + a.tobytes())
