# -*- coding: utf-8 -*-
import bpy
from mathutils.bvhtree import BVHTree
import bmesh
from math import radians
import numpy as np

def collision_check(obj1,obj2):
    collision = False
    bpy.context.view_layer.update()
    obj1.create_mesh()  
    obj2.create_mesh()
    if obj1.BVHtree.overlap(obj2.BVHtree):
        collision = True
    return collision

def find_distance(obj1,obj2,double=False):
    bpy.context.view_layer.update()
    obj1.create_mesh()
    obj2.create_mesh()
    if double:
        nearest=np.array([])
        for v in obj2.bm.verts:
            dist=obj1.BVHtree.find_nearest(v.co)[-1]
            nearest=np.append(nearest,dist)
        nearest2=np.array([])   
        for v in obj1.bm.verts:
            dist=obj2.BVHtree.find_nearest(v.co)[-1]
            nearest2=np.append(nearest2,dist)
        if obj1.BVHtree.overlap(obj2.BVHtree):
           return 0
        else:
            return min(min(nearest),min(nearest2))
    else:
        nearest=np.array([])
        for v in obj1.bm.verts:
            dist=obj2.BVHtree.find_nearest(v.co)[-1]
            nearest=np.append(nearest,dist)        
        if obj1.BVHtree.overlap(obj2.BVHtree):
           return 0
        else:
            return min(nearest)

class Object:
    def __init__(self,name):
        self.name=name
        self.locstart=np.array([0.0,0.0,1.3])
        self.rotstart=np.array([0.0,0.0,0.0])
        self.object = bpy.data.objects[name]
        self.rotate(self.rotstart)
        self.move(self.locstart)
        
    def create_mesh(self):
        self.bm=bmesh.new()
        if self.object.data:
            self.bm.from_mesh(self.object.data)
            self.bm.transform(self.object.matrix_world)
            self.BVHtree = BVHTree.FromBMesh(self.bm)
        
    def rotate(self,deg):
        self.object.rotation_euler=(radians(deg[0]),radians(deg[1]), radians(deg[2]))
        
    def move(self,pos):
        self.object.location=(pos[0], pos[1], pos[2])  