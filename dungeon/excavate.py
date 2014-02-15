"""
Copyright 2014 Jason Heeris, jason.heeris@gmail.com

This file is part of the dungeon excavator.

The dungeon excavator is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

The dungeon excavator is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with the
dungeon excavator. If not, see <http://www.gnu.org/licenses/>.
"""
import argparse
import base64
from io import BytesIO
import os.path
import subprocess
import sys
from tempfile import TemporaryFile, NamedTemporaryFile

from bs4 import BeautifulSoup as bs
from PIL import Image
from pkg_resources import resource_stream

from dungeon import svgtools

# SVG template name for the map
TEMPLATE_FILE = 'template.svg'

# Width of the inside shading (relative to the tile size)
BLUR_INSIDE_WIDTH = 0.5

# Width of the outside shading (relative to the tile size)
BLUR_OUTSIDE_WIDTH = 0.15

HELP_TEXT="Render a dungeon from some basic images."

RANDOM_SEED=8675309

TRACING_FORMAT='ppm'


def image_trace(image_data):
    """
    Uses "potrace" to trace the image data in the buffer. Returns a
    beautifulsoup document for the SVG path.
    """
    data = BytesIO(image_data)
    im = Image.open(data)
    
    with TemporaryFile('w+b') as vfile:
        with TemporaryFile('w+b') as rfile:
            im.save(rfile, TRACING_FORMAT)
            rfile.seek(0)
            
            ptproc = subprocess.check_call(
                [
                    'potrace',
                    '-b', 'svg',
                    '-u', '1',
                    # The resolution option to potrace is tricky. The output
                    # units are pt, but we're really working with pixels. It's
                    # easiest to just ignore this and copy the transform over
                    # without conversion.
                    # '-r', '90',
                    # Output is stdout
                    '-o', '-',
                    # Input is stdin
                    '-'
                ],
                stdin=rfile,
                stdout=vfile
            )

        vfile.seek(0)
        
        path_doc = bs(vfile, 'xml')

    return path_doc


def image_size(image_data):
    """ Given a buffer, returns the size of the image represented. """
    data = BytesIO(image_data)
    im = Image.open(data)
    return im.size


def image_to_svg(image_data):
    """
    Given a buffer, returns the base64 encoded data in ASCII with a prefix
    suitable for SVG.
    """
    return (
        'data:image/png;base64,'
        + base64.b64encode(image_data).decode('ascii'))


def render_room(ground_data, wall_data, clip_data, tile_size):
    """ Fill out the template document with the ground and wall textures. """
    # Check that all the sizes match
    sizes = set(map(image_size, (ground_data, wall_data, clip_data)))
    if len(sizes) != 1:
        raise ValueError("Image sizes don't match")
    
    # Trace paths for the floor plan
    path_doc = image_trace(clip_data)
    traced_paths = path_doc('path')
    assert len(traced_paths) == 1    
    traced_path = traced_paths[0]
    traced_path_d = traced_path['d']
    traced_path_tx = traced_path.parent['transform']
    
    # Apply the transform to the path to simplify it
    floorplan_path = svgtools.fuseTransform(traced_path_tx, traced_path_d)
    
    # Replace paths in the original image
    
    # Put some bitmaps in
    # The walls
    wall_svg = image_to_svg(wall_data)
    with resource_stream(__name__, TEMPLATE_FILE) as template_data:
        template_doc = bs(template_data, 'xml')
    
    template_doc(id='image-walls')[0]['xlink:href'] = wall_svg
    
    # The floor
    floor_svg = image_to_svg(ground_data)
    template_doc(id='image-ground')[0]['xlink:href'] = floor_svg    
    
    # Adjust the blur
    blur_inside = int(round(BLUR_INSIDE_WIDTH * tile_size))
    blur_outside = int(round(BLUR_OUTSIDE_WIDTH * tile_size))
    template_doc(id='wall-blur-inside')[0]['stdDeviation'] = str(blur_inside)
    template_doc(id='wall-blur-outside')[0]['stdDeviation'] = str(blur_outside)
    
    # Clip the floor
    clip_path = template_doc(id='clip-path-room-path')[0]
    clip_path['d'] = floorplan_path
    
    floorplan_path_extra = svgtools.add_nodes_to_path(
        floorplan_path,
        'bymax',
        max_length=40)
    
    wall_outline_new_d = svgtools.jitter_nodes(
        floorplan_path_extra,
        end=True,
        ctrl=True,
        radiusx=1,
        radiusy=1,
        norm=False)
    
    wall_outline = template_doc(id='path-wall-outline')[0]
    wall_outline['d'] = wall_outline_new_d
    
    return template_doc.prettify()
    

def render_room_from_paths(
        ground_path,
        wall_path,
        clip_path,
        output_path,
        tile_size):
    """ Load template and textures and export the rendered result. """
    with open(ground_path, 'rb') as gp:
        ground_data = gp.read()
        
    with open(wall_path, 'rb') as wp:
        wall_data = wp.read()
        
    with open(clip_path, 'rb') as cp:
        clip_data = cp.read()
        
    room = render_room(
        ground_data,
        wall_data,
        clip_data,
        tile_size)
    
    with open(output_path, 'w') as op:
        op.write(room)


def main():
    """ Parse arguments and get things going. """
    parser = argparse.ArgumentParser(description=HELP_TEXT)

    parser.add_argument('ground'   , help="Ground texture")
    parser.add_argument('wall'     , help="Wall texture")
    parser.add_argument('floorplan', help="Mask for the floor plan")
    parser.add_argument('output'   , help="Output file")
    
    parser.add_argument('-s', '--tile-size',
                        help="the size of a single grid square in px (default "
                             "100px)",
                        type=int,
                        default=100)
    
    args = parser.parse_args()
    
    return render_room_from_paths(
        args.ground,
        args.wall,
        args.floorplan,
        args.output,
        args.tile_size)
