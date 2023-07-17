#! usr/bin/env python3
"""
Created on Sat Nov 28 12:16:02 2020

@author: gian
"""
        
import time
import numpy as np
import matplotlib.pyplot as plt
from CollisionObject import CollisionObject
from XmlReader import XmlReader
import configparser
import os,sys

def scale(arr):
    arr=(arr/100)
    return arr

def move_away(g,t,lat,vert,long,distance):
    distance=distance/100
    newlat=lat-distance*np.sin(-np.radians(g))*np.cos(np.radians(t))
    newvert=vert-distance*np.cos(np.radians(g))
    newlong=long-distance*np.sin(-np.radians(g))*np.sin(np.radians(t))
    return newlat, newvert, newlong

def bound(low, high, value):
    return max(low, min(high, value))  
        
class PathCheck (CollisionObject):
    def __init__(self,setuppath):
        super().__init__(setuppath)
        self.virtual_iso = np.array([self.table_lat,self.table_vert,self.table_long])
        
    def readPath(self,filepath):
        xml = XmlReader(filepath)
        self.n = xml.n_control_point
        
        self.gantry_rot = 180 - np.array(xml.get_column('GantryRtn'))[:,0]
        self.table_rot = 180 - np.array(xml.get_column('CouchRtn'))[:,0]
        self.collimator_rot = 180 - np.array(xml.get_column('CollRtn'))[:,0]
        self.table_lat = - (100 - np.array(xml.get_column('CouchLat'))[:,0])/100
        self.table_vert = (100 - np.array(xml.get_column('CouchVrt'))[:,0])/100
        self.table_long = (100 - np.array(xml.get_column('CouchLng'))[:,0])/100
            
    def runCheck(self,outpath,name):
        print('Path Check run started')
        n_tolerances = len(self.tol_rot) * len(self.tol_pitch) * len(self.tol_roll) * len(self.tol_lat) * len(self.tol_vert) * len(self.tol_long)
        collisions=np.zeros((self.n,n_tolerances))
        distances=np.zeros((self.n,n_tolerances))
        bodydistances=np.zeros((self.n,n_tolerances))
        
        i = 0
        for tol_rot in self.tol_rot:
            for tol_pitch in self.tol_pitch:
                for tol_roll in self.tol_roll:
                    for tol_lat in self.tol_lat:
                        for tol_vrt in self.tol_vert:
                            for tol_lng in self.tol_long:
                                for j in range(self.n):
                                    
                                    lat = self.table_lat[j] + self.virtual_iso[0]
                                    vert = self.table_vert[j] + self.virtual_iso[1]
                                    long = self.table_long[j] + self.virtual_iso[2]
                                    
                                    self.move(self.gantry_rot[j],self.collimator_rot[j],self.table_rot[j] + tol_rot,self.table_roll + tol_roll,self.table_pitch + tol_pitch,lat + tol_lat,vert + tol_vrt,long + tol_lng)
                                    
                                    if self.check_table_and_body():
                                        collisions[j,i] = 1
                                    
                                    distances[j,i] = self.get_distance()*100
                                    if self.bodybool:
                                        bodydistances[j,i] = self.get_body_distance()*100
                                        
                                i += 1
               
            plt.figure(figsize=(7,3.5))
            ax = plt.gca()
            plt.fill_between(self.gantry_rot, np.amin(distances,axis=1), np.amax(distances,axis=1),color='tab:blue',alpha=0.3)
            ax.plot(self.gantry_rot,distances[:,0],'-',color='tab:blue',label='Table')
            if self.bodybool:
                plt.fill_between(self.gantry_rot, np.amin(bodydistances,axis=1), np.amax(bodydistances,axis=1),color='tab:red',alpha=0.3)
                ax.plot(self.gantry_rot,bodydistances[:,0],'-',color='tab:red',label='Patient model')
                plt.axhline(self.body_distance*100, color='tab:red', linestyle='--', linewidth=2,alpha=0.8)
            plt.xlabel('Gantry Rtn [°]')
            plt.xticks(np.arange(-180,181,30))
            ax.grid()
            plt.yticks(np.arange(0,50,5))
            plt.ylabel('Minimal distance [cm]')
            plt.legend(loc=2)
            plt.axhline(self.safety_distance*100, color='tab:blue', linestyle='--', linewidth=2,alpha=0.8)
            plt.tight_layout()
            plt.savefig(outpath + "/{}_minimal_distance.pdf".format(name),dpi=300)
            plt.savefig(outpath + "/{}_minimal_distance.png".format(name),dpi=300)
            plt.close()  
            
            with open(outpath + "/{}_collisions.txt".format(name), "w") as outfile:
                outfile.write(str(self.n) + "\n")
                for j in range(self.n):
                    outfile.write(str(self.gantry_rot[j]) + "\t" + str(collisions[j,0]) + "\t" + str(distances[j,0]) + "\n")
                outfile.close() 
            if (sum(collisions).any() > 0):
                print("Collision occured!")
            else:
                print("Collision free!")


        
if __name__=='__main__':
    args = sys.argv
    setuppath = args[6]
    outpath = os.path.dirname(setuppath)
    pathfolder = outpath + '/xml'

    t0=time.time()
    #import
    PC=PathCheck(setuppath)
    root,dirs,files = next(os.walk(pathfolder))
    for file in files:
        name = file[:-4]
        print(name)
        pathfile = os.path.join(root,file)
        PC.readPath(pathfile)
        #export
        PC.runCheck(outpath,name)
        
        PC.animate(False,outpath)
    
    PC.close(True,outpath)
    print("Elapsed time path check = "+str(time.time()-t0)+"s")

            

    
   
