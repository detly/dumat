# Dungeon excavator

## Overview

Create dungeon maps with a bit of depth to them! The dungeon excavator takes:

  1. A floor image
  2. A wall image
  3. A floorplan image
  
From these, it produces an Inkscape SVG showing a nicely shaded dungeon map.

The floorplan image should be black where you want the ground to show and white
everywhere else. It is used to create shading to give the impression of depth
wherever the walls meet the floor. An outline is added with a bit of random
jittering to give a "hand drawn" effect.

## Dependencies

The dungeon excavator runs under Python 3. It requires:

  - BeautifulSoup4
  - lxml
  - pillow

(Those are the package names as `pip` knows them.)

It also requires the `potrace` executable, although I'm looking at how to
replace that with Python based tracing.
