from enum import Enum
from matplotlib import colors


class Bioms(Enum):
    SEA = "blue"
    LAKE = "royalblue"
    DESERT = "wheat"
    PLANE = "limegreen"
    HILL = "darkgreen"
    MOUNTAIN = "silver"
    MOUNTAIN_SNOW = "white"
    WATER = "white"


class BiomeBlock:
    biome: str
    height: float
    heat: float
    world_height: int

    def __init__(self, height, heat):
        self.height = height
        self.heat = heat
        self.set_biome()
        self.world_height = int(self.height * 10)

    def set_biome(self):
        if self.height == 0:
            self.biome = Bioms.SEA
        elif self.height < 0.1:
            self.height = 0.1
            self.biome = Bioms.LAKE
        elif self.height < 0.5:
            if self.heat > 0.6:
                self.biome = Bioms.DESERT
            else:
                self.biome = Bioms.PLANE
        elif self.height < 0.6:
            self.biome = Bioms.PLANE
        elif self.height < 0.8:
            self.biome = Bioms.HILL
        elif self.height > 0.95 and self.heat > 0.6:
            self.biome = Bioms.MOUNTAIN_SNOW
        else:
            self.biome = Bioms.MOUNTAIN

    def color(self, multiply=None):
        colour = colors.to_rgb(self.biome.value)
        if multiply:
            colour = [c * multiply for c in colour]
        return colour
