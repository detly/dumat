# Dumat, a dungeon excavator

## Overview

Create dungeon maps with a bit of depth to them! Suitable for online TRPG tools
such as Roll20 or MapTool.

The dungeon excavator takes:

  1. A floor image
  2. A wall image
  3. A floorplan image
  
The floorplan image should be black where you want the ground to show and white
everywhere else. It is used to create shading to give the impression of depth
wherever the walls meet the floor. An outline is added with a bit of random
jittering to give a "hand drawn" effect.

The output image is an SVG file. It will be the same size as the floorplan. If
the ground and wall images are smaller than the floorplan, they will be tiled.

## Dependencies

The dungeon excavator runs under Python 3. It requires:

  - BeautifulSoup4
  - cssutils
  - lxml
  - pillow

(Those are the package names as `pip` knows them.)

With these dependencies you can only supply the floorplan as an SVG. If you have
the `potrace` utility installed you can also supply any bitmap image that the
Pillow library can read.

You will also need `setuptools` to install the package and generate the
command-line script.

## Usage

This assumes you have installed the package via `pip` (eg. `pip install -e .`)
or setuptools, and therefore have the `excavate` script available. If not,
`python -m dumat` can replace `excavate`.

```
excavate -s 100 ground.png wall.png floorplan.png map.svg
```

The `-s` argument specifies the tile size in pixels, and defaults to 100. It
determines the size of the gradient (approximately half a square for the inside
shading) and thickness of the walls.

## Web interface

See the [Dumat project](https://github.com/detly/dumat) for a web interface.
