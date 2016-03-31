import bpy
import bmesh
from math import *
from random import *


def equirectangularuvmap( scanX,scanY,scanZ, scanAngle):
    """map mesh faces to a equirectangular texture"""
    obj = bpy.context.active_object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.tex.verify()  # currently blender needs both layers.

    # Assume vertical alignment for now
    scanAngle *= pi/180


    # adjust UVs
    for f in bm.faces:
        # print(' ')
        
        planeX = f.calc_center_median().x - scanX
        planeY = f.calc_center_median().y - scanY
        planeZ = f.calc_center_median().z - scanZ
        planeVec = [planeX, planeY, planeZ]
        
        dotProd = (f.normal.x * planeX) + (f.normal.y * planeY) + (f.normal.z * planeZ) 
        
        # If a face has a normal direction away from the center of the scan, delect the face.
        # Hopefully this means that there will be no UV for this coordinate at all. 
        if dotProd>0:
            f.select_set(False)
            
            for l in f.loops:
                luv = l[uv_layer]
                luv.uv = (0.5+random()/100,0+random()/100)
            
            continue
        
        for L in f.loops:
            # Calculate radial distance from center of image
            r = sqrt( (L.vert.co.x - scanX)**2 + (L.vert.co.y - scanY)**2 )

            # IF radial distance is too small, assume values for U and V
            if r < 0.01:
                U = 0.5
                if (L.vert.co.z-scanZ) > 0:
                    V = 1.0
                else:
                    V= 0.0
                    
            else:
                # U is the normalized horizontal angle
                U = (atan2( (L.vert.co.y - scanY) , -(L.vert.co.x - scanX)) - scanAngle +pi )/(2.0*pi)

                # V is the normalized vertical angle (zero for straight down, 1 for straight up)
                
                V = (atan2( r, scanZ-L.vert.co.z))/(pi)
                #print("xyz coordinates = ", L.vert.co)
                
                if U < 0:
                    U += 1
                    
                if V < 0:
                    V += 1
                
                #print("uv coordinates = ",U,', ',V)
                
                luv = L[uv_layer]
                luv.uv = (U,V)
                    
    bmesh.update_edit_mesh(me)
    
# Scan 1
#equirectangularuvmap(-3.679692,  3.942834 ,1.393807 , 58.353693)

# Scan 2
#equirectangularuvmap(-0.84634, 7.649932, 1.213567  , 72.287435)

# Scan 3
#equirectangularuvmap(1.856701, 6.924198, 0.391366 , 36.992808)

# Scan 4
#equirectangularuvmap(5.289296, 2.512209, -0.695059  , 36.801182)

# Scan 5
#equirectangularuvmap(6.022316, -1.458117, -1.520517, 103.64301)

# Scan 6
equirectangularuvmap(1.60267, -1.84452, -0.8429, 165.616499)

# Scan 7
#equirectangularuvmap(-0.815092, -1.530523, -0.203589 , 117.531972)

# Scan 8
#equirectangularuvmap(-3.13409, 1.85642, 0.87117, 144.713466)

# Scan 9
#equirectangularuvmap(4.366643, 5.5628, -0.289433, 142.801249)

# Scan 10
#equirectangularuvmap(3.67919, -3.942931, -1.396275, 126.174026)
