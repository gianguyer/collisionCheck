#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from collections import defaultdict, OrderedDict
import os, sys

class XmlReader:
    """
    works with xml beam file from Eclipse
    """
    def __init__(self, path):
        self.path = path
        self.n_control_point = 0
        
        #prepare leaves
        self.n_leaf = 60
        self.leaf_small = 0.5
        self.leaf_large = 1
        
        self.read_file()
        
    def read_file(self):
        self.cp_list = self.load_cp_from_xml(self.path)
        self.n_control_point = len(self.cp_list)
        self.width = [float(1) if entry < 10 or entry > 49 else float(0.5) for entry in range(self.n_leaf)]
        
    def load_cp_from_xml(self, path):
        """
        - Loads "Control Point" values from beam xml file
        
        - Parameters:
        .path(str): location of file
        
        - Returns:
        .cp_panda(panda Dataframe): List of "Control Point" values
        """
        
        root = ET.parse(path).getroot()
        cp_panda = pd.DataFrame()
        
        for cp_entry in root.findall("./SetBeam/ControlPoints/Cp"):
            tmp_dict = defaultdict(list)
            tmp_dict.clear()
            
            #loop through entries of <CP>...</CP>
            for cp_value in cp_entry:
                # catch MLC entry
                if(cp_value.tag =="Mlc"):
                    for leaf in cp_value:
                        value = [float(entry) for entry in leaf.text.split()]
                        tmp_dict["{0}_{1}".format(cp_value.tag, leaf.tag)] = value
                # catch multi value entries      
                elif(len(cp_value) > 0):
                    for leaf in cp_value:
                        tmp_dict["{0}_{1}".format(cp_value.tag, leaf.tag)] = leaf.text
                         
                else:
                    tmp_dict[cp_value.tag] = cp_value.text
              
          
            tmp_panda = pd.DataFrame([tmp_dict])
            cp_panda = pd.concat([cp_panda,tmp_panda], ignore_index=False, sort=True, axis=0)
            cp_panda = cp_panda.reset_index(drop = True)
        
        # fill up NAN values
        for col in cp_panda.columns:
            cp_panda.loc[:, col] = cp_panda.loc[:, col].fillna( method ='ffill')
            
        self.change_Transl_values(cp_panda)
        #set data type                
        dtype0= {
         'CollRtn': 'float64',
         'CouchVrt': 'float64',
         'CouchLat': 'float64',
         'CouchLng': 'float64',
         'CouchRtn': 'float64',
         'CouchPit' : 'float64',
         'CouchRol' : 'float64',
         'DRate': 'float64',
         'Energy': 'str',
         'GantryRtn': 'float64',
         'Mu': 'float64',
         'SubBeam_Name': 'str',
         'SubBeam_Seq': 'float64',
         'X1': 'float64',
         'X2': 'float64',
         'Y1': 'float64',
         'Y2': 'float64'
         }
        cp_panda = cp_panda.astype(dtype0)
        
        print("load file: {0}".format(path))
        return cp_panda
        
    def get_index(self,column):
        a=self.cp_list.columns
        for i in range(len(a)):
            if a[i]==column:
                return i                
   
    def write_gtci(self,outpath):
        gtci='{}\n'.format(self.n_control_point)
        g = np.array(self.get_column('GantryRtn'))[:]
        t = np.array(self.get_column('CouchRtn'))[:]
        c = np.array(self.get_column('CollRtn'))[:]
        lat = np.array(self.get_column('CouchLat'))[:]
        vrt = np.array(self.get_column('CouchVrt'))[:]
        lng = np.array(self.get_column('CouchLng'))[:]
        for i in range(self.n_control_point):
            gtci += "{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\n".format(180-g[i,0],180-t[i,0],180-c[i,0],100-lat[i,0],100-vrt[i,0],100-lng[i,0])
        with open(outpath,'w') as file:
            file.write(gtci)     
            file.close()
            
    def change_Transl_values(self,cp_panda):
        try:
            cp_panda.insert(2,'CouchLng',100)
            print("CouchLng default value included")

        except ValueError:
            pass    
        
        try:
            cp_panda.insert(2,'CouchLat',100)
            print("CouchLat default value included")
        except ValueError:
            pass
        try:
            cp_panda.insert(2,'CouchVrt',100)
            print("CouchVrt default value included")

        except ValueError:
            pass
        try:
            cp_panda.insert(6,'CouchRol',0)
            print("CouchRol default value included")

        except ValueError:
            pass
        try:
            cp_panda.insert(6,'CouchPit',0)
            print("CouchPit default value included")

        except ValueError:
            pass
        try:
            cp_panda.insert(6,'CouchRtn',180)
            print("CouchRtn default value included")

        except ValueError:
            pass
    
    def get_column(self, *column):
        try:
            return self.cp_list[list(column)] 
        except:
            print("error in get_column")
    
    def get_row(self, *row):
        try:
            return self.cp_list.iloc[list(row)] 
        except:
            print("error in get_row")
            
    def to_array(self,array):
        column =np.zeros(len(array))
        for i in range(len(array)):
           column[i]=(array[i][0])
        return column
