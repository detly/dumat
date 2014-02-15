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

from flask import Flask, render_template

HELP_TEXT = """\
Web interface to the dungeon excavator."""

def root():
    """ Web interface page. """
    return render_template('index.html')

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

    # Web app object
    app = Flask('dungeon')

    # Front page
    app.route("/")(root)

    app.run(port=args.port, debug=True)
    
if __name__ == '__main__':
    main()
