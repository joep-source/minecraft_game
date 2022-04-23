# Ursina Minecraft Game

[![CI](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/joep-source/minecraft_game/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/joep-source/minecraft_game/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Minecraft-based game with random generated island maps, built with Ursina Engine. 


## Getting started

Installation (Python 3.8):
- `pipenv shell`
- `pipenv sync`

Start:
- `python play.py`


## Troubleshooting
- Issue: `UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.` <br>
  Solutions:
    - `pip install pyqt5`
    - `sudo apt-get install python3-tk` (Unix systems)


## License
MIT
