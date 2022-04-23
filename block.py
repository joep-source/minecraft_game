import math
from enum import Enum

from matplotlib import colors


class Biomes(str, Enum):
    SEA = "blue"
    LAKE = "royalblue"
    DESERT = "wheat"
    SAVANNA = "yellowgreen"
    PLANE = "limegreen"
    HILL = "darkgreen"
    MOUNTAIN = "silver"
    MOUNTAIN_SNOW = "white"


class BiomeBlock:
    biome: str
    world_height: int

    def __init__(self, height, heat):
        self.set_biome(height, heat)
        self.set_world_height(height)

    def set_world_height(self, height):
        height = math.pow(height, 4)  # mountain steepness
        height = int(height * 40)  # general hight curve
        self.world_height = height

    def set_biome(self, height, heat):
        if height == 0:
            self.biome = Biomes.SEA
        elif height < 0.1:
            self.biome = Biomes.LAKE
        elif height < 0.5:
            if heat > 0.6:
                self.biome = Biomes.DESERT
            elif heat > 0.4:
                self.biome = Biomes.SAVANNA
            else:
                self.biome = Biomes.PLANE
        elif height < 0.65:
            self.biome = Biomes.PLANE
        elif height < 0.8:
            self.biome = Biomes.HILL
        elif height > 0.95 and heat > 0.6:
            self.biome = Biomes.MOUNTAIN_SNOW
        else:
            self.biome = Biomes.MOUNTAIN

    def color(self, multiply=None):
        colour = colors.to_rgb(self.biome.value)
        if multiply:
            colour = [c * multiply for c in colour]
        return colour
