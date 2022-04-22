from typing import Any, List, Tuple
import random

import numpy as np
from matplotlib import colors
import noise

from block import BiomeBlock

Map2D = Any  # format List[List[BiomeBlockType]] as numpy array

NOISE_HEIGHT = {
    "octaves": 4,
    "persistence": 0.2,
    "lacunarity": 7,
}

NOISE_HEIGHT_ISLAND = {
    "octaves": 2,
    "persistence": 0.5,
    "lacunarity": 4,
}

NOISE_HEAT = {
    "octaves": 1,
    "persistence": 0.5,
    "lacunarity": 2,
}


def normalize(data: np.ndarray) -> np.ndarray:
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def random_seed(between=[10000, 99999]) -> int:
    seed = random.randint(between[0], between[1])
    print(f"seed {seed}")
    return seed


def create_circulair_map_mask(size: int) -> Map2D:
    """Map with rounded edges"""
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    mask = np.sqrt((x) ** 2 + (y) ** 2)
    mask = normalize(mask)
    # Flatten outer circle by setting values above 0.8 to 0.8
    mask = np.minimum(mask, 0.8, mask)
    mask = normalize(mask)
    mask *= -1
    return mask


def combine_maps(map1: Map2D, map2: Map2D) -> Map2D:
    map1 += map2
    map1 = np.maximum(map1, 0, map1)  # Set values below 0 to 0
    return normalize(np.array(map1))


def to_blocks_map(heigth_map: Map2D, heat_map: Map2D) -> Map2D:
    blocks = [
        BiomeBlock(height=heigth, heat=heat)
        for heigth, heat in zip(np.nditer(heigth_map), np.nditer(heat_map))
    ]
    return np.array(blocks).reshape(heigth_map.shape)


def generate_world_map(size: int, seed: int = 1, island: bool = True) -> Map2D:
    def _gen_noise(x, y, seed, **params):
        return noise.snoise3(x / size, y / size, z=seed, **params)

    def _gen_noise_map(shape, seed, **params):
        noises = [_gen_noise(y, x, seed, **params) for y, x in np.ndindex(shape)]
        return normalize(np.array(noises).reshape(world_shape))

    world_shape = (size, size)
    noise_heigt = NOISE_HEIGHT_ISLAND if island else NOISE_HEIGHT
    heigth_map = _gen_noise_map(world_shape, seed, **noise_heigt)
    if island:
        heigth_map = combine_maps(heigth_map, create_circulair_map_mask(size))
    heat_map = _gen_noise_map(world_shape, seed, **NOISE_HEAT)
    world_map = to_blocks_map(heigth_map, heat_map)
    return world_map


def world_map_colors(world_map: Map2D, border=True) -> List[List[Tuple[float, float, float]]]:
    def _gen_border(map2d, size, color):
        return np.pad(map2d, pad_width=size, mode="constant", constant_values=color)

    get_biome_value = lambda block: block.biome.value
    world_map = np.vectorize(get_biome_value)(world_map)

    if border:
        world_map = _gen_border(world_map, 1, "black")
        world_map = _gen_border(world_map, 5, "gold")
        world_map = _gen_border(world_map, 2, "black")

    block_colors = [colors.to_rgb(str(block)) for block in np.nditer(world_map)]
    world_map_colors = np.array(block_colors).reshape(world_map.shape + (3,))
    return world_map_colors.tolist()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    print("Generating world map")
    world_map = generate_world_map(size=300, seed=random_seed())

    print("Show world map")
    world_map_biome = world_map_colors(world_map, border=True)

    plt.figure(figsize=(2.5, 2.5), frameon=False)
    plt.axis("off")
    img = plt.imshow(world_map_biome)
    plt.show()
