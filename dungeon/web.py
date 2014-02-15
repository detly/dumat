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

from flask import Flask, render_template, request, make_response, redirect, url_for

from dungeon.excavate import render_room

HELP_TEXT = """\
Web interface to the dungeon excavator."""

app = Flask('dungeon')

@app.route("/")
def root():
    """ Web interface landing page. """
    return render_template('index.html')


@app.route("/error")
def error():
    """ Display errors. """
    return render_template('error.html')

@app.route("/map.svg", methods=['POST'])
def process():
    """ Process submitted form data. """
    tile_size = int(request.form['size'])
    wall_file = request.files['walls']
    floor_file = request.files['floor']
    floorplan_file = request.files['floorplan']
    
    try:
        room_doc = render_room(
            floor_file.read(),
            wall_file.read(),
            floorplan_file.read(),
            tile_size
        )
    except ValueError:
        return redirect(url_for('error'))
        
    # Create response
    response = make_response(room_doc)
    response.headers['Content-Type'] = 'image/svg+xml'
    return response


def main():
    """ Parse arguments and get things going for the web interface """
    parser = argparse.ArgumentParser(description=HELP_TEXT)
    
    parser.add_argument(
        '-p', '--port',
        help="Port to serve the interface on.",
        type=int,
        default=5050
    )

    args = parser.parse_args()

    app.run(port=args.port, debug=True)
    
if __name__ == '__main__':
    main()
