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
from itertools import product
import logging.config
from math import ceil
import os.path
import subprocess
import sys
from tempfile import TemporaryFile, NamedTemporaryFile

from bs4 import BeautifulSoup as bs
import cssutils
from PIL import Image
from pkg_resources import resource_stream

from dungeon import svgtools

# SVG template name for the map
TEMPLATE_FILE = 'template.svg'

# Width of the inside shading (relative to the tile size)
BLUR_INSIDE_WIDTH = 0.5

# Width of the outside shading (relative to the tile size)
BLUR_OUTSIDE_WIDTH = 0.15

# Width of the wall outline
WALL_STROKE_WIDTH = 0.02

# Size of jitter displacement
JITTER_SCALE = WALL_STROKE_WIDTH/4

HELP_TEXT="""\
The dungeon excavator takes a floor image, a wall image and a floorplan and
renders a dungeon map. The floorplan image is used to create shading to give the
impression of depth, and an outline is added with a bit of random jittering to
give a "hand drawn" effect. The output will be the same size as the floorplan.
The wall and floor images are tiled if they are smaller than the floorplan.
"""

TRACING_FORMAT='ppm'


def image_trace(image):
    """
    Uses "potrace" to trace the given PIL.Image object. Returns a beautifulsoup
    document for the SVG path.
    """ 
    with TemporaryFile('w+b') as vfile:
        with TemporaryFile('w+b') as rfile:
            image.save(rfile, TRACING_FORMAT)
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

    # The SVG produced by 'potrace' contain units in their dimensions
    svg_root = path_doc.find('svg')
    
    for dim in ('width', 'height'):
        dim_str = svg_root[dim]
        if dim_str.endswith('pt'):
            svg_root[dim] = dim_str[:-2]
    
    return path_doc


def extract_image_path(image_data):
    """
    Returns the 'd' attribute of an SVG path for the given image data. If the
    data represents an SVG file, the first path found is returned. If it is a
    raster image, it is traced using 'potrace' and the path from that is
    returned.
    """
    try:
        # Try to open as a raster image
        data = BytesIO(image_data)
        im = Image.open(data)
    except IOError:
        # Pillow throws an IOError if it doesn't recognise the image format,
        # which might mean it's an SVG file already.
        path_doc = bs(image_data, 'xml')
    else:
        try:
            path_doc = image_trace(im)
        except FileNotFoundError:
            raise ValueError(
                "Bitmap floorplans require 'potrace' to be installed"
            )

    svg_root = path_doc.find('svg')

    width  = float(svg_root['width'])
    height = float(svg_root['height'])

    traced_path = path_doc.find('path')
    
    if not traced_path:
        raise ValueError("Cannot extract path from floorplan file")
    
    traced_path_d = traced_path['d']
    traced_path_tx = traced_path.get('transform', '')
    traced_path_parent_tx = traced_path.parent.get('transform', '')
    
    # Apply the transforms to the path to simplify it
    transformed_path = svgtools.fuseTransform(
        traced_path_tx,
        traced_path_d
    )
        
    transformed_path = svgtools.fuseTransform(
        traced_path_parent_tx,
        transformed_path
    )
    
    return transformed_path, width, height


def raster_size(raster_data):
    """
    Given a buffer of raster image data, return the size of the image
    represented.
    """
    data = BytesIO(raster_data)
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


def insert_and_tile_raster(image_data, map_doc, dimensions, image_id, layer_id):
    """ Given raster (PNG) image data, convert it to SVG data and tile it.
    
    @param image_data a buffer of PNG data
    @param map_doc the SVG file containing the template definitions
    @param dimensions a tuple of the map dimensions (width, height)
    @param image_id the ID of the image definition in the SVG template
    @param layer_id the ID of the layer that should contain the tiled image
    """
    # The floor
    width, height = dimensions
    image_width, image_height = raster_size(image_data)
    image_svg = image_to_svg(image_data)
    image_element = map_doc.find(id=image_id)
    image_element['xlink:href'] = image_svg
    image_element['width']  = image_width
    image_element['height'] = image_height
    
    # Tile the floor
    image_layer = map_doc.find(id=layer_id)
    x_repeats = ceil(width / image_width)
    y_repeats = ceil(height / image_height)
    
    x_offsets = (num * image_width for num in range(x_repeats))
    y_offsets = (num * image_width for num in range(y_repeats))
    
    for x_offset, y_offset in product(x_offsets, y_offsets):
        x_offset_str = '{:d}'.format(x_offset)
        y_offset_str = '{:d}'.format(y_offset)

        tile = map_doc.new_tag(
            'use',
            **{
                'xlink:href': '#' + image_id,
                'y': y_offset_str,
                'x': x_offset_str
            }  
        )

        image_layer.append(tile)


def render_room(ground_data, wall_data, clip_data, tile_size):
    """ Fill out the template document with the ground and wall textures. """
    # Disable logging for the cssutils module, it's just so darn talkative
    logging_config = {
        'version' : 1,
        'loggers' : {
            'cssutils' : {
                'level' : 'ERROR'
            }
        }
    }
    logging.config.dictConfig(logging_config)    
   
    # Trace paths for the floor plan
    floorplan_path, width, height = extract_image_path(clip_data)

    # Create a bounding box for everything
    bounding_path = svgtools.create_bounding_path(width, height)
 
    # Load SVG
    with resource_stream(__name__, TEMPLATE_FILE) as template_data:
        template_doc = bs(template_data, 'xml')
   
    # Set the sizes
    svg_doc = template_doc.find('svg')
    svg_doc['width']  = width
    svg_doc['height'] = height
    
    # Put some bitmaps in
    # Insert and tile the walls
    insert_and_tile_raster(
        wall_data,
        template_doc,
        (width, height),
        'image-wall',
        'layer-wall',
    )

    # Insert and tile the floor
    insert_and_tile_raster(
        ground_data,
        template_doc,
        (width, height),
        'image-ground',
        'layer-ground',
    )
    
    # Adjust the blur
    blur_inside = int(round(BLUR_INSIDE_WIDTH * tile_size))
    blur_outside = int(round(BLUR_OUTSIDE_WIDTH * tile_size))
    template_doc.find(id='wall-blur-inside')['stdDeviation'] = str(blur_inside)
    template_doc.find(id='wall-blur-outside')['stdDeviation'] = str(blur_outside)
    
    # Clip the floor
    clip_path = template_doc.find(id='clip-path-room-path')
    clip_path['d'] = bounding_path
    
    # Clip the walls
    floor_path = template_doc.find(id='clip-path-floor-path')
    floor_path['d'] = floorplan_path
    
    # Invert the wall path
    floorplan_path_inverted = svgtools.path_difference(bounding_path, floorplan_path)
    floor_path_inverted = template_doc.find(id='clip-path-floor-path-inverted')
    floor_path_inverted['d'] = floorplan_path_inverted
    
    floorplan_path_extra = svgtools.add_nodes_to_path(
        floorplan_path,
        'bymax',
        max_length=40)
    
    wall_outline = template_doc.find(id='path-wall-outline')
    
    wall_outline_attrs = cssutils.parseStyle(
        wall_outline['style'],
        validate=False
    )
        
    wall_outline_attrs['stroke-width'] = (
        '{:.2f}'.format(WALL_STROKE_WIDTH * tile_size)
    )
    
    jitter_radius = JITTER_SCALE * tile_size
    
    wall_outline_new_d = svgtools.jitter_nodes(
        floorplan_path_extra,
        end=True,
        ctrl=True,
        radiusx=jitter_radius,
        radiusy=jitter_radius,
        norm=False
    )
    
    wall_outline['d'] = wall_outline_new_d
    wall_outline['style'] = wall_outline_attrs.cssText

    # Remove the copyright notice
    del template_doc.contents[0]
    
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

    parser.add_argument('ground', help="Ground texture (PNG image)")
    parser.add_argument('wall'  , help="Wall texture (PNG image)")

    parser.add_argument(
        'floorplan',
        help=(
            "Mask for the floor plan. This can be a bitmap image (any format "
            "supported by Pillow) or an SVG image. If it is a bitmap, it should"
            " be black where you want the ground to show and white everywhere "
            "else. The 'potrace' executable must be installed to be able to use"
            " bitmaps. If the file is an SVG file, the first path in the file "
            "will be used."
        )
    )
    
    parser.add_argument('output', help="Output file (Inkscape SVG)")
    
    parser.add_argument('-s', '--tile-size',
                        help="The size of a single grid square in px (default "
                             "100px). Used to scale the shading and wall "
                             "outline.",
                        type=int,
                        default=100)
    
    args = parser.parse_args()
    
    return render_room_from_paths(
        args.ground,
        args.wall,
        args.floorplan,
        args.output,
        args.tile_size)
