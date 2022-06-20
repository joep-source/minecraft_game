<div align="center">

# Minecraft themed FPS

[![CI](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/joep-source/minecraft_game/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Minecraft themed FPS game on randomly generated island maps, built with Ursina Engine.

</div>

## Motivation :star:

Inspired by an article about Minecraft world generation in Python, I decided to create something similar myself. 
Combining one of my favorite programming languages and videogames together :heart:.
With help from a few articles I discovered techniques such as perlin noise for endless natural map generation, circular gradients to create an island shape, and combining altitude with temperature maps to create different biomes.

But, a 3D map of an island is still a bit boring, so I decided to turn it into 3D game.
Python may not be your first choice, but I wanted to see how far I could push this. 
At the time of writing, [Ursina Engine](https://www.ursinaengine.org/) is one of the best and easiest to use 3D game engines, among the little competition.

## Getting started :video_game:

Installation:
- clone repository
- `pipenv shell`
- `pipenv sync`

Play:
- `python play.py`

### Tested setups
- Ubuntu with Python 3.8.
- Windows with Python 3.8.

### Troubleshooting
- Issue: `UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.` <br>
  Solutions:
    - `pip install pyqt5`
    - `sudo apt-get install python3-tk` (Unix systems)

## Sources :books:
- [Ursina Engine](https://www.ursinaengine.org/).
- Article [Replicating Minecraft World Generation in Python](https://towardsdatascience.com/replicating-minecraft-world-generation-in-python-1b491bc9b9a4) by Bilal Himite.
- Article [Generating Digital Worlds Using Perlin Noise](https://medium.com/nerd-for-tech/generating-digital-worlds-using-perlin-noise-5d11237c29e9) by Robert MacWha.
- Article [Making maps with noise functions](https://www.redblobgames.com/maps/terrain-from-noise/) by Red Blob Games.
- Created block textures with [Tynker](https://www.tynker.com/minecraft).
- 3D enemy object [Necromancer](https://skfb.ly/6RprX) by omargabagu.

## License :label:
MIT
