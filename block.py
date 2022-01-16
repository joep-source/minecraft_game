from enum import Enum
from matplotlib import colors


class Bioms(Enum):
    LAKE = "royalblue"
    DESERT = "wheat"
    PLANE = "limegreen"
    HILL = "darkgreen"
    MOUNTAIN = "silver"
    WATER = "white"


class BiomeBlock:
    biome: str
    height: int
    heat: float

    def __init__(self, height, heat):
        self.height = height
        self.heat = heat
        self.set_biome()

    def set_biome(self):
        if self.height < 0.3:
            self.biome = Bioms.LAKE
        elif self.height < 0.5:
            if self.heat < 0.25:
                self.biome = Bioms.DESERT
            else:
                self.biome = Bioms.PLANE
        elif self.height < 0.6:
            self.biome = Bioms.PLANE
        elif self.height < 0.8:
            self.biome = Bioms.HILL
        else:
            self.biome = Bioms.MOUNTAIN

    def color(self, multiply=None):
        colour = colors.to_rgb(self.biome.value)
        if multiply:
            colour = [c * multiply for c in colour]
        return colour
