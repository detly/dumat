# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
# Copyright 2005,2007 Aaron Spike, aaron@ekips.org
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
# Copyright 2001-2002 Matt Chisholm matt@theory.org
# Copyright 2008 Joel Holdsworth joel@airwebreathe.org.uk
#     for AP
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
"""
This is a collection of utilities adapted from Inkscape's extensions. Everything
here has been taken from the "inkscape/share/extensions" directory. Individual
copyright information and origin is documented with each function just in case
it's useful.
"""
from dumat import bezmisc, cubicsuperpath, simplepath
import random, math, copy, re

# From inkscape/share/extensions/addnodes.py.
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
def cspbezsplit(sp1, sp2, t = 0.5):
    """ Support function for add_nodes_to_path. """
    m1=tpoint(sp1[1],sp1[2],t)
    m2=tpoint(sp1[2],sp2[0],t)
    m3=tpoint(sp2[0],sp2[1],t)
    m4=tpoint(m1,m2,t)
    m5=tpoint(m2,m3,t)
    m=tpoint(m4,m5,t)
    return [[sp1[0][:],sp1[1][:],m1], [m4,m,m5], [m3,sp2[1][:],sp2[2][:]]]

# From inkscape/share/extensions/addnodes.py.
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
def tpoint(point1, point2, t = 0.5):
    """ Support function for add_nodes_to_path. """
    (x1,y1) = point1
    (x2,y2) = point2
    return [x1+t*(x2-x1),y1+t*(y2-y1)]


# From inkscape/share/extensions/addnodes.py.
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
def cspbezsplitatlength(sp1, sp2, l = 0.5, tolerance = 0.001):
    """ Support function for add_nodes_to_path. """
    bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
    t = bezmisc.beziertatlength(bez, l, tolerance)
    return cspbezsplit(sp1, sp2, t)


# From inkscape/share/extensions/addnodes.py.
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
def cspseglength(sp1,sp2, tolerance = 0.001):
    """ Support function for add_nodes_to_path. """
    bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
    return bezmisc.bezierlength(bez, tolerance)    


# Based on SplitIt.effect in inkscape/share/extensions/addnodes.py.
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
# Copyright (C) 2014 Jason Heeris, jason.heeris@gmail.com
def add_nodes_to_path(path_string, method, max_length=10, max_num=2):
    """
    @return the new "d" attribute of an SVG path
    
    @param path_string the "d" attribute of an SVG path    
    @param method 'bynum' to create a maximum number of segments; 'bymax' to
           create a maximum segment length
    @param max_length if method is 'bymax', the maximum length in px for any
           segment (ignored otherwise)
    @param max_num if method is 'bynum', the maximum number of segments to
           create
    """
    p = cubicsuperpath.parsePath(path_string)
    
    #lens, total = csplength(p)
    #avg = total/numlengths(lens)
    #inkex.debug("average segment length: %s" % avg)

    new = []
    for sub in p:
        new.append([sub[0][:]])
        i = 1
        while i <= len(sub)-1:
            length = cspseglength(new[-1][-1], sub[i])
            
            if method == 'bynum':
                splits = max_num
            else:
                splits = math.ceil(length/max_length)

            for s in range(int(splits),1,-1):
                new[-1][-1], next, sub[i] = cspbezsplitatlength(new[-1][-1], sub[i], 1.0/s)
                new[-1].append(next[:])
            new[-1].append(sub[i])
            i+=1
        
    return cubicsuperpath.formatPath(new)

# From inkscape/share/extensions/radiusrand.py
# Copyright (C) 2005 Aaron Spike, aaron@ekips.org
def randomize(point, rx, ry, norm):
    """ Support function for jitter_nodes. """
    (x, y) = point
    if norm:
        r = abs(random.normalvariate(0.0,0.5*max(rx, ry)))
    else:
        r = random.uniform(0.0,max(rx, ry))
    a = random.uniform(0.0,2*math.pi)
    x += math.cos(a)*rx
    y += math.sin(a)*ry
    return [x, y]

# Based on RadiusRandomize.effect from inkscape/share/extensions/radiusrand.py
# Copyright 2005 Aaron Spike, aaron@ekips.org
# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def jitter_nodes(
        path_string,
        end=True,
        ctrl=False,
        radiusx=10,
        radiusy=10,
        norm=True):
    """
    Randomly moves path nodes (and optionally their tangents).
    
    @param path_string the "d" attribute of an SVG path
    
    @param end shift nodes
    @param ctrl shift node "handles" (control points for bezier curves)
    @param radiusx horizontal distance to move nodes
    @param radiusy vertical distance to move nodes
    @param norm use normal distribution instead of uniform   
    
    @return a path with randomly shifted nodes, as the "d" attribute of an SVG
            path
    """
    p = cubicsuperpath.parsePath(path_string)
    for subpath in p:
        for csp in subpath:
            if end:
                delta=randomize([0,0], radiusx, radiusy, norm)
                csp[0][0]+=delta[0] 
                csp[0][1]+=delta[1] 
                csp[1][0]+=delta[0] 
                csp[1][1]+=delta[1] 
                csp[2][0]+=delta[0] 
                csp[2][1]+=delta[1] 
            if ctrl:
                csp[0]=randomize(csp[0], radiusx, radiusy, norm)
                csp[2]=randomize(csp[2], radiusx, radiusy, norm)
    
    return cubicsuperpath.formatPath(p)


# From inkscape/share/extensions/simpletransform.py
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
def composeTransform(M1,M2):
    """ Support function for fuseTransform """
    a11 = M1[0][0]*M2[0][0] + M1[0][1]*M2[1][0]
    a12 = M1[0][0]*M2[0][1] + M1[0][1]*M2[1][1]
    a21 = M1[1][0]*M2[0][0] + M1[1][1]*M2[1][0]
    a22 = M1[1][0]*M2[0][1] + M1[1][1]*M2[1][1]

    v1 = M1[0][0]*M2[0][2] + M1[0][1]*M2[1][2] + M1[0][2]
    v2 = M1[1][0]*M2[0][2] + M1[1][1]*M2[1][2] + M1[1][2]
    return [[a11,a12,v1],[a21,a22,v2]]


# From inkscape/share/extensions/simpletransform.py
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
def parseTransform(transf,mat=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):
    """ Support function for fuseTransform """
    if transf=="" or transf==None:
        return(mat)
    stransf = transf.strip()
    result=re.match("(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?",stransf)
#-- translate --
    if result.group(1)=="translate":
        args=result.group(2).replace(',',' ').split()
        dx=float(args[0])
        if len(args)==1:
            dy=0.0
        else:
            dy=float(args[1])
        matrix=[[1,0,dx],[0,1,dy]]
#-- scale --
    if result.group(1)=="scale":
        args=result.group(2).replace(',',' ').split()
        sx=float(args[0])
        if len(args)==1:
            sy=sx
        else:
            sy=float(args[1])
        matrix=[[sx,0,0],[0,sy,0]]
#-- rotate --
    if result.group(1)=="rotate":
        args=result.group(2).replace(',',' ').split()
        a=float(args[0])*math.pi/180
        if len(args)==1:
            cx,cy=(0.0,0.0)
        else:
            cx,cy=tuple(map(float,args[1:]))
        matrix=[[math.cos(a),-math.sin(a),cx],[math.sin(a),math.cos(a),cy]]
        matrix=composeTransform(matrix,[[1,0,-cx],[0,1,-cy]])
#-- skewX --
    if result.group(1)=="skewX":
        a=float(result.group(2))*math.pi/180
        matrix=[[1,math.tan(a),0],[0,1,0]]
#-- skewY --
    if result.group(1)=="skewY":
        a=float(result.group(2))*math.pi/180
        matrix=[[1,0,0],[math.tan(a),1,0]]
#-- matrix --
    if result.group(1)=="matrix":
        a11,a21,a12,a22,v1,v2=result.group(2).replace(',',' ').split()
        matrix=[[float(a11),float(a12),float(v1)], [float(a21),float(a22),float(v2)]]

    matrix=composeTransform(mat,matrix)
    if result.end() < len(stransf):
        return(parseTransform(stransf[result.end():], matrix))
    else:
        return matrix


# From inkscape/share/extensions/simpletransform.py
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
def applyTransformToPoint(mat,pt):
    """ Support function for fuseTransform """
    x = mat[0][0]*pt[0] + mat[0][1]*pt[1] + mat[0][2]
    y = mat[1][0]*pt[0] + mat[1][1]*pt[1] + mat[1][2]
    pt[0]=x
    pt[1]=y


# From inkscape/share/extensions/simpletransform.py
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
def applyTransformToPath(mat,path):
    """ Support function for fuseTransform """
    for comp in path:
        for ctl in comp:
            for pt in ctl:
                applyTransformToPoint(mat,pt)


# From inkscape/share/extensions/simpletransform.py
# Copyright 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
# Copyright 2010 Alvin Penner, penner@vaxxine.com
# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def fuseTransform(transform_string, path_string):
    """
    Takes an SVG transform string and an SVG path "d" string and applies the
    transform to the path. Returns a new path string.
    """    
    m = parseTransform(transform_string)
    p = cubicsuperpath.parsePath(path_string)
    applyTransformToPath(m,p)
    return cubicsuperpath.formatPath(p, terminate=True)


# From inkscape/share/extensions/render_alphabetsoup.py
# Copyright 2001-2002 Matt Chisholm, matt@theory.org
# Copyright 2008 Joel Holdsworth, joel@airwebreathe.org.uk
#     for AP
def reverseComponent(c):
    """" Support function for reversePath. """
    nc = []
    last = c.pop()
    nc.append(['M', last[1][-2:]])
    while c:
        this = c.pop()
        cmd = last[0]
        if cmd == 'C':
            nc.append([last[0], last[1][2:4] + last[1][:2] + this[1][-2:]])
        else:
            nc.append([last[0], this[1][-2:]])
        last = this
    return nc


# From inkscape/share/extensions/render_alphabetsoup.py
# Copyright 2001-2002 Matt Chisholm, matt@theory.org
# Copyright 2008 Joel Holdsworth, joel@airwebreathe.org.uk
#     for AP
# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def reversePath(path_string):
    """
    Takes an SVG path "d" string and reverses the path. Returns a new "d"
    string.
    """
    sp = simplepath.parsePath(path_string)
    rp = []
    component = []
    for p in sp:
        cmd, params = p
        if cmd == 'Z':
            rp.extend(reverseComponent(component))
            rp.append(['Z', []])
            component = []
        else:
            component.append(p)
    return simplepath.formatPath(rp)


# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def winding_sign(path_string):
    """
    Computes the sign of the winding number of the path. Returns a negative
    number if the path is clockwise, or a positive number if it is counter-
    clockwise.
    """
    path = simplepath.parsePath(path_string)
    
    winding = 0
    last_point = None
    
    for kind, coords in path:
        # simplepath.parsePath only creates absolute coordinates
        if kind == 'M':
            this_point = coords[0:2]
            
        if kind == 'C':
            this_point = coords[4:6]
            
        if last_point is not None:
            curl = (last_point[0] + this_point[0])*(last_point[1] - this_point[1])
            winding += curl
            
        last_point = coords
    
    return winding


# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def path_difference(minuend_path_string, subtrahend_path_string):
    """
    """
    minuend_path    = simplepath.parsePath(minuend_path_string)
    
    if winding_sign(subtrahend_path_string) > 0:    
        subtrahend_path = simplepath.parsePath(reversePath(subtrahend_path_string))
    else:
        subtrahend_path = simplepath.parsePath(subtrahend_path_string)
    
    minuend_path.extend(subtrahend_path)
    return simplepath.formatPath(minuend_path)

# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
def create_bounding_path(width, height):
    """ Creates a rectangular path that borders the image. """
    path = [
        ['m', [0, 0]  ],
        ['v', [height]],
        ['h', [width ]],
        ['v', [-height]],
        ['z', []      ]
    ]
    
    return simplepath.formatPath(path)

