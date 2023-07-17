#! usr/bin/env python3
"""
Created on Sat Nov 28 12:16:02 2020

@author: gian
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from CollisionObject import CollisionObject
import configparser
import os, sys

def scale(arr):
    arr=(arr/100)
    return arr

def move_away(g,t,lat,vert,long,distance):
    distance=distance/100
    newlat=lat-distance*np.sin(-np.radians(g))*np.cos(np.radians(t))
    newvert=vert-distance*np.cos(np.radians(g))
    newlong=long-distance*np.sin(-np.radians(g))*np.sin(np.radians(t))
    return newlat, newvert, newlong

def move_without_vert(g,t,lat,long,distance):
    distance=distance/100
    newlat=lat-distance*np.sin(-np.radians(g))*np.cos(np.radians(t))
    newlong=long-distance*np.sin(-np.radians(g))*np.sin(np.radians(t))
    return newlat, newlong
        
class CollisionMapCreator (CollisionObject):
    def __init__(self,setuppath):
        super().__init__(setuppath)
    
    def readConfig(self,configpath):
        config=configparser.ConfigParser()
        config.read(configpath)
        self.binary=config.getboolean('CollisionMap','binary')
        # self.SID_shift=config.getfloat('Collision','SID shift')
        #self.safety_distance=config.getfloat('CollisionMap','safety_distance')/100.0     
        gantryspacing = config.getfloat('CollisionMap','gantryrot_spacing')
        tablespacing = config.getfloat('CollisionMap','tablerot_spacing')
        
        gantryrot_start = config.getint('CollisionMap','gantryrot_start')
        gantryrot_end = config.getint('CollisionMap','gantryrot_end')

        tablerot_start = config.getint('CollisionMap','tablerot_start')
        tablerot_end =  config.getint('CollisionMap','tablerot_end')
            
        self.n_table=int((tablerot_end-tablerot_start)/tablespacing)+1
        self.n_gantry=int((gantryrot_end-gantryrot_start)/gantryspacing)+1
        self.gantry_rot=np.linspace(gantryrot_start,gantryrot_end,self.n_gantry)
        self.table_rot=np.linspace(tablerot_start,tablerot_end,self.n_table)  
        self.collimarginbool=True
            
    def createCollisionMap(self,outpath,distance=0):
        print('Collision Map creator started')           
        collisions=np.zeros((self.n_table,self.n_gantry))

        for j,g in enumerate(self.gantry_rot):
            firstcollision=True
            for i,t in enumerate(self.table_rot):
                lat, vert, long = move_away(-g, t, self.table_lat, self.table_vert, self.table_long, distance)  
                for tol_rot in self.tol_rot:
                    for tol_pitch in self.tol_pitch:
                        for tol_roll in self.tol_roll:
                            for tol_lat in self.tol_lat:
                                for tol_vrt in self.tol_vert:
                                    for tol_lng in self.tol_long:
                                        
                                        self.move(g,0,t + tol_rot,tol_roll,tol_pitch,lat + tol_lat,vert + tol_vrt,long + tol_lng)
                                        if self.check_table_and_body():
                                            collisions[i][j] = 1
        colormap=plt.get_cmap('RdYlGn_r')
        plt.figure()
        ax = plt.gca()
        ax.imshow(collisions, extent=(self.gantry_rot[0],self.gantry_rot[-1],  self.table_rot[0], self.table_rot[-1]), interpolation='none',cmap=colormap,aspect="equal",origin='lower')
        plt.xlabel('Gantry Rtn [°]')
        plt.xticks(np.arange(-180,181,30))
        plt.yticks(np.arange(-90,91,30))
        ax.grid()
        plt.ylabel('Table Rtn [°]')

        plt.savefig(outpath +"/collision-map.png",dpi=300)
        plt.close()  
        
        with open(outpath+"/collision-map.txt", "w") as outfile:      
            outfile.write(str(self.n_gantry)+" "+str(self.n_table)+"\n")
            outfile.write(" ".join("{:n}".format(g) for g in self.gantry_rot)+"\n")
            outfile.write(" ".join("{:n}".format(t) for t in self.table_rot)+"\n")
            outfile.write('\n'.join(' '.join("{:n}".format(x) for x in y) for y in collisions))
            outfile.close() 

    def testIsocenters(self, outpath, longipositions, vertipositions, latpositions , distance=0):
        print('Test Isocenter creator started')

        collisions=np.zeros((self.n_table,self.n_gantry))
        
        for j,g in enumerate(self.gantry_rot):
            for vert in vertipositions:
                firstcollision=True
                for i,t in enumerate(self.table_rot):
                    for lat in latpositions:
                        for long in longipositions:
                            self.move(g,0,t,self.table_roll,self.table_pitch, lat ,vert ,long)
                            if self.check_table_and_body():
                                collisions[i][j] += 1
                            elif firstcollision==True:
                                firstcollision=False
                                print(g,t,vert)
                                
        colormap=plt.get_cmap('inferno')
        plt.figure()
        ax = plt.gca()
        ax.imshow(collisions, extent=(self.gantry_rot[0],self.gantry_rot[-1],  self.table_rot[0], self.table_rot[-1]), interpolation='none',cmap=colormap,aspect="equal",origin='lower')
        plt.xlabel('Gantry Rtn [°]')
        plt.xticks(np.arange(-180,181,30))
        plt.yticks(np.arange(-90,91,30))
        ax.grid()
        plt.ylabel('Table Rtn [°]')

        plt.savefig(outpath+"/isocenter-test.png",dpi=300)
        plt.close()  
        
        with open(outpath+"/isocenter-test.txt", "w") as outfile:      
            outfile.write(str(self.n_gantry)+" "+str(self.n_table)+"\n")
            outfile.write(" ".join("{:n}".format(g) for g in self.gantry_rot)+"\n")
            outfile.write(" ".join("{:n}".format(t) for t in self.table_rot)+"\n")
            outfile.write('\n'.join(' '.join("{:n}".format(x) for x in y) for y in collisions))
            outfile.close()
            

        
if __name__=='__main__':
    args = sys.argv
    setuppath = args[6]
    configpath = args[7]

    outdir = os.path.dirname(setuppath)
    
    t0=time.time()
    #import
    CM=CollisionMapCreator(setuppath)
    CM.readConfig(configpath)
    #export
    CM.createCollisionMap(outdir)
    CM.close(True, outdir)
    print("Elapsed time collision map creation= "+str(time.time()-t0)+"s")
