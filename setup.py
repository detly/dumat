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
from setuptools import setup, find_packages

setup(
    name = "Dungeon",
    version = "1.0",
    packages = find_packages(),
    
    package_data = {
        'dungeon': ['template.svg'],
        'dungeon.web': ['static/style.css', 'templates/*.html'],
    },
    
    install_requires = [
        'BeautifulSoup4',
        'lxml',
        'pillow',
        'cssutils',
    ],
    
    entry_points = {
        'console_scripts': [
            'excavate = dungeon.excavate:main',
            'webcavate = dungeon.web.app:main',
        ]
    }
)
