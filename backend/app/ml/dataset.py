import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from typing import List, Dict, Tuple
from PIL import Image


class SonarTileDataset(Dataset):
    def __init__(self, tiles: List[Dict], transform=None, tile_size: int = 512):
        self.tiles = tiles
        self.tile_size = tile_size
        self.transform = transform or self._default_transform()

    def __len__(self) -> int:
        return len(self.tiles)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict]:
        tile_info = self.tiles[idx]
        tile_data = tile_info['tile']

        if isinstance(tile_data, np.ndarray):
            if len(tile_data.shape) == 2:
                tile_data = np.stack([tile_data] * 3, axis=-1)
            elif tile_data.shape[2] == 4:
                tile_data = tile_data[:, :, :3]
            pil_image = Image.fromarray(tile_data.astype(np.uint8))
        else:
            pil_image = tile_data

        tensor = self.transform(pil_image)

        original_h = tile_info.get('original_h', self.tile_size)
        original_w = tile_info.get('original_w', self.tile_size)
        
        metadata = {
            'tile_x': tile_info['tile_x'],
            'tile_y': tile_info['tile_y'],
            'pixel_x': tile_info['pixel_x'],
            'pixel_y': tile_info['pixel_y'],
            'original_h': original_h,
            'original_w': original_w
        }

        return tensor, metadata

    def _default_transform(self) -> transforms.Compose:
        return transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])


def create_dataloader(
    tiles: List[Dict],
    batch_size: int = 16,
    num_workers: int = 4,
    pin_memory: bool = True,
    tile_size: int = 512
) -> DataLoader:
    dataset = SonarTileDataset(tiles, tile_size=tile_size)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers if torch.cuda.is_available() else 0,
        pin_memory=pin_memory and torch.cuda.is_available(),
        prefetch_factor=2 if torch.cuda.is_available() else None
    )
