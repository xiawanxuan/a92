import numpy as np
from typing import List, Dict, Tuple
from PIL import Image
import io
from ..core.config import settings


class TileService:
    def __init__(self, tile_size: int = 512, overlap: int = 0):
        self.tile_size = tile_size
        self.overlap = overlap
        self.stride = tile_size - overlap

    def calculate_tiling(self, width: int, height: int) -> Tuple[int, int, int]:
        num_tiles_x = (width + self.stride - 1) // self.stride
        num_tiles_y = (height + self.stride - 1) // self.stride
        total_tiles = num_tiles_x * num_tiles_y
        return num_tiles_x, num_tiles_y, total_tiles

    def slice_image(self, image: np.ndarray) -> List[Dict]:
        h, w = image.shape[:2]
        tiles = []

        for tile_y in range(0, h, self.stride):
            for tile_x in range(0, w, self.stride):
                y_end = min(tile_y + self.tile_size, h)
                x_end = min(tile_x + self.tile_size, w)
                tile = image[tile_y:y_end, tile_x:x_end]

                if tile.shape[0] < self.tile_size or tile.shape[1] < self.tile_size:
                    padded = np.zeros(
                        (self.tile_size, self.tile_size, image.shape[2]) if len(image.shape) == 3
                        else (self.tile_size, self.tile_size),
                        dtype=image.dtype
                    )
                    padded[:tile.shape[0], :tile.shape[1]] = tile
                    tile = padded

                tiles.append({
                    'tile': tile,
                    'tile_x': tile_x // self.stride,
                    'tile_y': tile_y // self.stride,
                    'pixel_x': tile_x,
                    'pixel_y': tile_y
                })
        return tiles

    def get_tile_coordinates(self, tile_x: int, tile_y: int) -> Tuple[int, int, int, int]:
        x = tile_x * self.stride
        y = tile_y * self.stride
        return x, y, x + self.tile_size, y + self.tile_size

    def extract_tile_from_image(self, image: np.ndarray, tile_x: int, tile_y: int) -> np.ndarray:
        h, w = image.shape[:2]
        x, y, x_end, y_end = self.get_tile_coordinates(tile_x, tile_y)

        x_end = min(x_end, w)
        y_end = min(y_end, h)

        tile = image[y:y_end, x:x_end]

        if tile.shape[0] < self.tile_size or tile.shape[1] < self.tile_size:
            padded = np.zeros(
                (self.tile_size, self.tile_size, image.shape[2]) if len(image.shape) == 3
                else (self.tile_size, self.tile_size),
                dtype=image.dtype
            )
            padded[:tile.shape[0], :tile.shape[1]] = tile
            tile = padded

        return tile

    def generate_dzi_tile(self, image: np.ndarray, z: int, x: int, y: int, tile_size: int = 256) -> bytes:
        max_level = int(np.ceil(np.log2(max(image.shape[0], image.shape[1]))))
        if z > max_level:
            raise ValueError(f"Zoom level {z} exceeds max level {max_level}")

        scale = 2 ** (max_level - z)
        scaled_width = int(np.ceil(image.shape[1] / scale))
        scaled_height = int(np.ceil(image.shape[0] / scale))

        x_start = x * tile_size
        y_start = y * tile_size
        x_end = min(x_start + tile_size, scaled_width)
        y_end = min(y_start + tile_size, scaled_height)

        if x_start >= scaled_width or y_start >= scaled_height:
            raise ValueError("Tile coordinates out of bounds")

        src_x_start = x_start * scale
        src_y_start = y_start * scale
        src_x_end = min(x_end * scale, image.shape[1])
        src_y_end = min(y_end * scale, image.shape[0])

        tile_data = image[src_y_start:src_y_end, src_x_start:src_x_end]

        pil_image = Image.fromarray(tile_data)
        pil_image = pil_image.resize((x_end - x_start, y_end - y_start), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        pil_image.save(output, format='JPEG', quality=90)
        return output.getvalue()

    def get_dzi_properties(self, width: int, height: int, tile_size: int = 256) -> Dict:
        max_level = int(np.ceil(np.log2(max(width, height))))
        return {
            'width': width,
            'height': height,
            'tile_size': tile_size,
            'max_level': max_level,
            'overlap': 0,
            'format': 'jpg'
        }
