# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
# 
# This file is part of the dungeon excavator ("dumat").
# 
# Dumat is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Dumat is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# dumat. If not, see <http://www.gnu.org/licenses/>.
from setuptools import setup, find_packages

setup(
    name = "dumat",
    version = "1.0",
    packages = find_packages(),
    
    package_data = {
        'dumat': ['template.svg'],
        'dumat.web': ['static/style.css', 'templates/*.html'],
    },
    
    install_requires = [
        'BeautifulSoup4',
        'lxml',
        'pillow',
        'cssutils',
        'wand',
    ],
    
    entry_points = {
        'console_scripts': [
            'excavate = dumat.excavate:main',
        ]
    }
)
