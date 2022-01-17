import numpy as np
import random
import noise

from block import BiomeBlock

NOISE_HEIGHT = {
    "octaves": 4,
    "persistence": 0.2,
    "lacunarity": 7,
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


def world_init(size=1024, seed=1):
    def _gen_noise(x, y, seed=seed, **params):
        return noise.snoise3(x / size, y / size, z=seed, **params)

    heigths = normalize(
        [[(_gen_noise(x, y, **NOISE_HEIGHT)) for x in range(size)] for y in range(size)]
    )
    heats = normalize(
        [[(_gen_noise(x, y, **NOISE_HEAT)) for x in range(size)] for y in range(size)]
    )

    world_map = np.array(
        [
            [BiomeBlock(height=heigths[x, y], heat=heats[x, y]) for y in range(size)]
            for x in range(size)
        ]
    )
    return world_map


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    size = 100
    print("Generating world map")
    world_map = world_init(size)

    print("Show world map")
    world_map_biome = [
        [world_map[x, y].color() for x in range(size)] for y in range(size)
    ]
    plt.figure(figsize=(8, 6))
    img = plt.imshow(world_map_biome)
    plt.colorbar(img, orientation="vertical")
    plt.show()
