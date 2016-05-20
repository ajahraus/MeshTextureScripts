import bpy
import bmesh
from collections import namedtuple
from math import *
from random import *

Point = namedtuple('Point',['x','y','z','name'])
Point.__new__.__defaults__=(None,)

def findEffectiveUVsizeDict(f, scan):
    
    currName = scan.name
    scanX = scan.x
    scanY = scan.y
    scanZ = scan.z
    scanAngle = scan.ang
    
    UVinfo = namedtuple('UVinfo',['UVarea','UVvertexCoords'])
    
    vertexCoords = dict()
    for v in f.verts:
        vertexCoords[v] = (0,0)
    
    currUVinfo = UVinfo(UVarea=0.0, UVvertexCoords=vertexCoords)
        
    planeX = f.calc_center_median().x - scanX
    planeY = f.calc_center_median().y - scanY
    planeZ = f.calc_center_median().z - scanZ
    planeVec = [planeX, planeY, planeZ]

    dotProd = (f.normal.x * planeX) + (f.normal.y * planeY) + (f.normal.z * planeZ) 

    #This function, unlike the one it was copied from, doesn't assign UVs directly, 
    # but instead calculates the average area of the face in this scan's UV space,
    # assigning zero if it faces away from the scan
    if dotProd>0:
        return currUVinfo

    f_c = f.calc_center_median()
    
    for L in f.loops:

        # Calculate radial distance from center of image
        r = sqrt( (L.vert.co.x - scanX)**2 + (L.vert.co.y - scanY)**2 )

        # If radial distance is too small, assume values for U and V
        if r < 0.01:
            U = 0.5
            if (L.vert.co.z-scanZ) > 0:
                V = 1.0
            else:
                V= 0.0
                
        else:
            
            f_c_r = sqrt( (f_c.x - scanX)**2 + (f_c.y - scanY)**2 )
            
            centroidU = (atan2( (f_c.y - scanY) , -(f_c.x - scanX)) - scanAngle +pi )/(2.0*pi)
            centroidV = (atan2( f_c_r, scanZ-f_c.z))/(pi)
            
            if centroidU < 0:
                centroidU+=1
                
            if centroidV < 0:
                centroidV += 1
            
            
            # U is the normalized horizontal angle
            U = (atan2( (L.vert.co.y - scanY) , -(L.vert.co.x - scanX)) - scanAngle +pi )/(2.0*pi)

            # V is the normalized vertical angle (zero for straight down, 1 for straight up)
            V = (atan2( r, scanZ-L.vert.co.z))/(pi)
            
            if U < 0:
                U+=1
                
            if V < 0:
                V += 1
            
            if fabs(U)<0.0001 or fabs(U-1)<0.0001:
                if floor(centroidU + 0.5) == 0:
                    U = 0.0
                else:
                    U = 1.0
                    
        # After calculating the UV coordinates for each vertex,
        # save those UVs in a dictionary with the vertex as the key
        currUVinfo.UVvertexCoords[L.vert] = (U,V)
        
    # The final step to to calculate the effective area of the face in UV space
    # I'm not perfectly certain how to do this, since it might be the case that 
    # the face is an n-gon.
    p  = []
    for x in currUVinfo.UVvertexCoords.values():
        p.append(x)
    
    # The area is conceptually the best metric for determining the number of pixels
    # being applied to this face, but there are a couple of complicating factors:
    # The first is the alpha (i.e. transparancy) of the pixels of the part of the texture.
    # If the alpha for part or all of that polygon is zero, then that should be considered
    # as a reduction of the polygon's effective size. The second factor is occlusion, which 
    # is more complicated. Luckily, I've figured a pretty simple method of determining 
    # occluded areas without a huge amount of additional computation. Create a new array 
    # equal in size to the texture, and equal in value to it's alpha channel (or with a 
    # binarry representation, rounding to zero or one). Then for each scan, estimate the
    # effective area of the polygons with this as a multiplicative factor rather than the 
    # actual alpha channel. Importantly, this needs to be done in order of the closest 
    # polygons first. Then, once the effective area of a polygon is determined, set the
    # pixels in that part of the texture to zero. This process lets the same method be used
    # to determine the alpha values and occlusion simultaneously. It's not perfect, since
    # partially occluded faces may still end up with visual errors, but those can be cleaned 
    # manually farely simply, and it'll be orders of magnitude faster than a rigorous approach
    
    
    # This is just a nieve approach right now
    area = ngonArea(p)
        
    currUVinfo = UVinfo(area, currUVinfo.UVvertexCoords)
        
    return currUVinfo

def equirectangularuvmap( ob, scan ):
    """map mesh faces to a equirectangular texture"""
    bm  = bmesh.from_edit_mesh(ob.data)
    
    uv_layer = bm.loops.layers.uv.new(scan.name)
    bm.faces.layers.tex.verify()  # currently blender needs both layers.

    # Assume vertical alignment for now
    currName = scan.name
    scanX = scan.x
    scanY = scan.y
    scanZ = scan.z
    scanAngle = radians(scan.ang)
    
    # adjust UVs
    for f in bm.faces:
        if f.select == True:
            f_c = f.calc_center_median()
    
            planeX = f_c.x - scanX
            planeY = f_c.y - scanY
            planeZ = f_c.z - scanZ
            planeVec = [planeX, planeY, planeZ]
            
            dotProd = (f.normal.x * planeX) + (f.normal.y * planeY) + (f.normal.z * planeZ) 
            
            # If a face has a normal direction away from the center of the scan, set the uv to a section 
            # of alpha = 0 and skip the rest of the calculations
            if dotProd>0:
                for l in f.loops:
                    luv = l[uv_layer]
                    luv.uv = (0.5+random()/100,0+random()/100)
                continue
            
            f_c = f.calc_center_median()
            
            # Calculate the offset for the whole face at a time rather than
            # per vertex. This should prevent smearing
            
            f_c_r = sqrt( (f_c.x - scanX)**2 + (f_c.y - scanY)**2 )
            
            centroidU = (atan2( (f_c.y - scanY) , -(f_c.x - scanX)) - scanAngle +pi )/(2.0*pi)
            centroidV = (atan2( f_c_r, scanZ-f_c.z))/(pi)
            
            if centroidU < 0:
                centroidU+=1
            
            if centroidV < 0:
                centroidV += 1
            
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
                    
                    for i in range(-1,2):
                        if fabs((U+i)-centroidU) < 0.25:
                            U += i
                            break
                    
                    luv = L[uv_layer]
                    luv.uv = (U,V)
        else:
            for l in f.loops:
                luv = l[uv_layer]
                luv.uv = (0.5+random()/100,0+random()/100)
            
    bmesh.update_edit_mesh(ob.data)

def ngonArea(p):
    return 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in segments(p)))

def segments(p):
    return zip(p, p[1:] + [p[0]])    

def distance(a,b):
    return sqrt( (a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2 )

def findEffectiveArea(f,scan):
    f_c = f.calc_center_median()

    planeX = f_c.x - scan.x
    planeY = f_c.y - scan.y
    planeZ = f_c.z - scan.z
    planeVec = [planeX, planeY, planeZ]
    
    dotProd = (f.normal.x * planeX) + (f.normal.y * planeY) + (f.normal.z * planeZ)
    
    r = sqrt(planeX**2 + planeY**2)
    angle = atan2(r,-planeZ)
    if (dotProd > 0) or (angle < radians(30) and planeZ<0):
        return 0
    else:
        return abs(dotProd/sum(x**2 for x in planeVec))
    
def assignVertexGroupsByFaceArea(groupCenters):
    """With an object selected, set in edit mode and assign vertexes to vertex groups with
    the same names an the scan scans in the list of groups"""
    ob = bpy.context.selected_objects[0]
    ob.vertex_groups.clear()
    
    for scan in groupCenters:
        ob.vertex_groups.new(name=scan.name)
    ob.vertex_groups.new(name='No Scan')
    listOfPoints = {'No Scan':[]}
    
    for x in groupCenters:
        listOfPoints[x.name] = []

    bpy.ops.object.mode_set(mode='EDIT')

    bm  = bmesh.from_edit_mesh(ob.data)

    for f in bm.faces:
        max_area = (None, None)
        for scan in groupCenters:
            currentArea = (findEffectiveArea(f,scan), scan.name)
            if (max_area == (None, None)) or (currentArea > max_area[0]):
                max_area = (currentArea, scan.name)
            
        if max_area[1] != None:
            for v in f.verts:
                listOfPoints[max_area[1]].append(v)
        else:
            for v in f.verts:
                listOfPoints['No Scan'].append(v)
        
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.mesh.select_all(action='DESELECT')
    for scan in groupCenters:
        for x in listOfPoints[scan.name]:
            x.select_set(True)
        bpy.ops.object.vertex_group_set_active(group = scan.name)
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        
    for x in listOfPoints['No Scan']:
        x.select_set(True)
    bpy.ops.object.vertex_group_set_active(group = 'No Scan')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    

scanPosition = namedtuple('ScanPosition',['name','x','y','z','ang'])

# This is hard coded and is therefore lazy, but I don't want to write a scheme
# for reading these values staight from Faro Scene, so copy-paste is what you get
allScanPoses = [
 scanPosition('scan1', -3.679692,  3.942834 ,1.393807 , 58.353693),
 scanPosition('scan2', -0.84634, 7.649932, 1.213567  , 72.287435),
 scanPosition('scan3', 1.856701, 6.924198, 0.391366 , 36.992808),
 scanPosition('scan4', 5.289296, 2.512209, -0.695059  , 36.801182),
 scanPosition('scan5', 6.022316, -1.458117, -1.520517, 103.64301),
 scanPosition('scan6', 1.60267, -1.84452, -0.8429, 165.616499),
 scanPosition('scan7', -0.815092, -1.530523, -0.203589 , 117.531972),
 scanPosition('scan8', -3.13409, 1.85642, 0.87117, 144.713466),
 scanPosition('scan9', 4.366643, 5.5628, -0.289433, 142.801249),
 scanPosition('scan10', 3.67919, -3.942931, -1.396275, 126.174026)
 ]

assignVertexGroupsByFaceArea(allScanPoses)
ob = bpy.context.selected_objects[0]
bm = bmesh.from_edit_mesh(ob.data)
bpy.ops.mesh.select_all(action='DESELECT')

for scan in allScanPoses[0:1]:
    bpy.ops.object.vertex_group_set_active(group=scan.name)
    bpy.ops.object.vertex_group_select()
    equirectangularuvmap(ob, scan)
    bpy.ops.mesh.select_all(action='DESELECT')