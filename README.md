<div align="center">

# Minecraft themed FPS

A Minecraft themed FPS game on randomly generated island maps, built with Python and Ursina Engine.

[![CI](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/joep-source/minecraft_game/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## Play locally :video_game:

<img src="https://raw.githubusercontent.com/joep-source/minecraft_game/main/media/player_icon.png" align="right" alt="Soldier logo by LikeAboss" width="120" height="178">

Requirements:
- Python 3.6+
- [Pipenv](https://pypi.org/project/pipenv/)

Play:
- `pipenv shell`
- `pipenv sync` (only once)
- `python play.py`

## Motivation :star:

Inspired by an article about Minecraft world generation in Python, I wanted to create something similar myself.
Combining one of my favorite programming languages and videogames together :heart:. 
A non-interactive 3D map was still a bit boring so I turned it into playable game.

## Media

<center><img src="https://raw.githubusercontent.com/joep-source/minecraft_game/main/media/play.png" alt="play" width="640" height="360"></center>
<br>
<center><img src="https://raw.githubusercontent.com/joep-source/minecraft_game/main/media/spectate.png" alt="spectate" width="640" height="360"></center>

## Game features

- Enemies are spawned randomly over the island.
- Hit and attack animation for player and enemy.
- Minimap with live player position.
- Player and enemy can jump.
- Sink in water.
- Player can place wood blocks on land to block enemies.
- Random island shapes.
- Biomes based on altitude and temperature.
- Progress bar on loading screen.
- Main menu with settings.

## Troubleshooting

- Issue: `UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.` <br>
  Solutions:
    - `pip install pyqt5`
    - `sudo apt-get install python3-tk` (Unix systems)

### Tested setups
- Ubuntu with Python 3.8.
- Windows with Python 3.8.

## Sources :books:
- [Ursina Engine](https://www.ursinaengine.org/).
- Article [Replicating Minecraft World Generation in Python](https://towardsdatascience.com/replicating-minecraft-world-generation-in-python-1b491bc9b9a4) by Bilal Himite.
- Article [Generating Digital Worlds Using Perlin Noise](https://medium.com/nerd-for-tech/generating-digital-worlds-using-perlin-noise-5d11237c29e9) by Robert MacWha.
- Article [Making maps with noise functions](https://www.redblobgames.com/maps/terrain-from-noise/) by Red Blob Games.
- Created block textures with [Tynker](https://www.tynker.com/minecraft).
- 3D player object [Soldier](https://www.tynker.com/minecraft/editor/mob/zombie/5d8ba4c0f22e09193573a962/) by LikeAboss.
- 3D enemy object [Necromancer](https://skfb.ly/6RprX) by omargabagu.
- [Blockbench](https://web.blockbench.net/) for editing 3D objects.
- Cursor icon [Fighting Weapon Target](https://www.flaticon.com/free-icon/fighting-weapon-target_20180) by Freepik.

## License :label:
MIT
