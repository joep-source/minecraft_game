import numpy as np
import random
from matplotlib import colors
import noise

from block import BiomeBlock

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


def normalize(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def random_seed(between=[10000, 99999]):
    seed = random.randint(between[0], between[1])
    print(f"seed {seed}")
    return seed


def create_mask_map(size=1024):
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    mask = np.sqrt((x) ** 2 + (y) ** 2)
    mask = normalize(mask)
    # Flatten outer circle
    mask = [
        [mask[x, y] if mask[x, y] < 0.8 else 0.8 for x in range(size)]
        for y in range(size)
    ]
    mask = normalize(np.array(mask))
    mask *= -1
    return mask


def combine_maps(map1, map2, size=1024):
    map1 += map2
    map1 = [
        [map1[x, y] if map1[x, y] >= 0 else 0 for x in range(size)] for y in range(size)
    ]
    return normalize(np.array(map1))


def world_map_create(heigth_map, heat_map, size=1024):
    world_map = [
        [BiomeBlock(height=heigth_map[x, y], heat=heat_map[x, y]) for y in range(size)]
        for x in range(size)
    ]
    return np.array(world_map)


def world_init(size=1024, seed=1, island=True):
    def _gen_noise(x, y, seed=seed, **params):
        return noise.snoise3(x / size, y / size, z=seed, **params)

    noise_heigt = NOISE_HEIGHT_ISLAND if island else NOISE_HEIGHT
    heigth_map = normalize(
        [[(_gen_noise(x, y, **noise_heigt)) for x in range(size)] for y in range(size)]
    )
    if island:
        heigth_map = combine_maps(heigth_map, create_mask_map(size=size), size=size)

    heat_map = normalize(
        [[(_gen_noise(x, y, **NOISE_HEAT)) for x in range(size)] for y in range(size)]
    )

    world_map = world_map_create(heigth_map, heat_map, size=size)
    return world_map


def world_map_colors(world_map, size, border=True):
    def _gen_border(map2d, size, color):
        return np.pad(map2d, pad_width=size, mode="constant", constant_values=color)

    world_map = np.array(
        [[world_map[x, y].biome.value for x in range(size)] for y in range(size)]
    )
    if border:
        world_map = _gen_border(world_map, 1, "black")
        world_map = _gen_border(world_map, 5, "gold")
        world_map = _gen_border(world_map, 2, "black")

    size = len(world_map)
    world_map = np.array(
        [[colors.to_rgb(world_map[x, y]) for x in range(size)] for y in range(size)]
    )
    return world_map


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    size = 300
    print("Generating world map")
    world_map = world_init(size, seed=random_seed())

    print("Show world map")
    world_map_biome = world_map_colors(world_map, size)

    plt.figure(figsize=(2.5, 2.5), frameon=False)
    plt.axis("off")
    img = plt.imshow(world_map_biome)
    plt.show()
