# -*- coding: utf-8 -*-

from BlenderObject import Object, collision_check, find_distance
import numpy as np
import configparser
import bpy

def bound(low, high, value):
    return max(low, min(high, value))  

def move_away(g,t,lat,vert,long,distance):
    distance=distance/100
    newlat=lat-distance*np.sin(-np.radians(g))*np.cos(np.radians(t))
    newvert=vert-distance*np.cos(np.radians(g))
    newlong=long-distance*np.sin(-np.radians(g))*np.sin(np.radians(t))
    return newlat, newvert, newlong

class CollisionObject:
    def __init__(self,setuppath):
        self.collimarginbool = True        
        self.err=False
        self.gantry=Object("Gantry")
        self.table_top=Object("Table_top")
        self.tablemiddle=Object("Table_middle")
        self.tablebottom=Object("Table_bottom")
        self.tablebase=Object("Table_base")
        self.tablerot=Object("TableRot")
        self.colli=Object("Collimator") 
        self.laserguard=Object("Laserguard")    
        self.table_top_margin=Object("Table_top_margin")
        self.tablemiddle_margin=Object("Table_middle_margin")
        self.tablebottom_margin=Object("Table_bottom_margin")
        self.tablebase_margin=Object("Table_base_margin")
        self.colli_margin=Object("Collimator_margin")
        self.tol_pitch = np.zeros(1)
        self.tol_roll = np.zeros(1)
        self.tol_rot = np.zeros(1)
        self.tol_vert = np.zeros(1)
        self.tol_lat = np.zeros(1)
        self.tol_long = np.zeros(1)
        
        self.readSetup(setuppath)

    def readSetup(self,setuppath):
        config=configparser.ConfigParser()
        config.read(setuppath)
        
        self.table_pitch = config.getfloat('StartingPosition','pitch')
        self.table_roll = -config.getfloat('StartingPosition','roll')
        self.table_rot = config.getfloat('StartingPosition','rot')
        self.table_vert = -config.getfloat('StartingPosition','vrt')/100
        self.table_lat = config.getfloat('StartingPosition','lat')/100
        self.table_long = -config.getfloat('StartingPosition','lng')/100

        if config.has_section("Tolerance"):
            pitch = config.getfloat('Tolerance','pitch')
            if abs(pitch) > 0.00001:
                self.tol_pitch = np.concatenate((self.tol_pitch,np.array([pitch,-pitch])))
            roll = -config.getfloat('Tolerance','roll')
            if abs(roll) > 0.00001:
                self.tol_roll = np.concatenate((self.tol_roll,np.array([roll,-roll])))
            rot = config.getfloat('Tolerance','rot')
            if abs(rot) > 0.00001:
                self.tol_rot = np.concatenate((self.tol_rot,np.array([rot,-rot])))
            vert = -config.getfloat('Tolerance','vrt')/100
            if abs(vert) > 0.00001:
                self.tol_vert = np.concatenate((self.tol_vert,np.array([vert,-vert])))
            lat = config.getfloat('Tolerance','lat')/100
            if abs(lat) > 0.00001:
                self.tol_lat = np.concatenate((self.tol_lat,np.array([lat,-lat])))
            long = -config.getfloat('Tolerance','lng')/100
            if abs(long) > 0.00001:
                self.tol_long = np.concatenate((self.tol_long,np.array([long,-long])))
        
        self.bodybool=config.getboolean('CollisionModel','patientmodel')
        self.headplatebool=config.getboolean('CollisionModel','headplate')
        self.laserguardbool=config.getboolean('CollisionModel','laserguard')
        
        self.safety_distance=config.getfloat('SafetyDistance','table')/100.0
        self.body_distance=config.getfloat('SafetyDistance','body')/100.0
        
        self.gantry_objectlist = [self.table_top_margin,self.tablemiddle_margin,self.tablebottom_margin,self.tablebase_margin]
        self.lg_objectlist = [self.table_top,self.tablemiddle,self.tablebottom,self.tablebase]
        
        if self.bodybool:
            sdict = {'M': 'male', 'F': 'female', 'phantom': 'phantom' }
            sex = sdict[config.get('PatientModel','sex')]

            patientstring = '{}_{}_arms_{}'.format(sex,config.get('PatientModel','size'),config.get('PatientModel','arms'))
            self.body=Object(patientstring)
            self.body.object.hide_set(False)
            self.body.object.hide_render = False

        if self.headplatebool:
            self.headplate=Object("Headplate")
            self.headplate.object.hide_set(False)
            self.headplate.object.hide_render = False
            self.gantry_objectlist.append(self.headplate)
            self.lg_objectlist.append(self.headplate)
        
        self.colliobj = self.colli
        
        if self.collimarginbool:
            self.colliobj = self.colli_margin
    
    def check_table_and_body(self):
        collision = False
        if self.safety_distance==0:
            if self.check_collision():
                collision = True
        else:
            if self.check_safety_distance():
                collision = True
                
        if self.bodybool:
            if self.body_distance==0:
                if self.check_body_collision():
                    collision = True
            else:
                if self.check_body_distance():
                    collision = True
                    
        return collision
                
    def check_laserguard(self):
        collision = 0
        if any([collision_check(self.gantry, c) for c in self.gantry_objectlist]):
            collision = 1
        elif any([collision_check(self.colliobj, c) for c in self.gantry_objectlist]):
            collision = 1
        elif self.laserguardbool:
            if any([collision_check(self.laserguard, c) for c in self.lg_objectlist]):
                collision = 2
        return collision        
    
    def check_collision(self):
        collision = False
        if any([collision_check(self.gantry, c) for c in self.gantry_objectlist]):
            collision = True
        elif any([collision_check(self.colliobj, c) for c in self.gantry_objectlist]):
            collision = True
        elif self.laserguardbool:
            if any([collision_check(self.laserguard, c) for c in self.lg_objectlist]):
                collision = True
        return collision
    
    def check_body_collision(self):
        collision = False
        if collision_check(self.gantry, self.body):
            collision = True
        elif collision_check(self.colliobj, self.body):
            collision = True
        elif self.laserguardbool:
            if collision_check(self.laserguard, self.body):
                collision = True
        return collision
    
    def check_safety_distance(self):
        collision = False
        if any([find_distance(self.gantry,c)<self.safety_distance for c in self.gantry_objectlist]):
            collision = True
        elif any([find_distance(self.colliobj, c)<self.safety_distance for c in self.gantry_objectlist]):
            collision = True
        elif self.laserguardbool:
            if any([find_distance(self.laserguard, c)<self.safety_distance for c in self.lg_objectlist]):
                collision = True
        return collision

    def check_body_distance(self):
        collision = False
        if find_distance(self.gantry, self.body) < self.body_distance:
            collision = True
        elif find_distance(self.colliobj, self.body) < self.body_distance:
            collision = True
        elif self.laserguardbool:
            if find_distance(self.laserguard, self.body) < self.body_distance:
                collision = True
        return collision
    
    def get_distance(self):
        gantrydist = min([find_distance(self.gantry,c) for c in self.gantry_objectlist])
        collidist = min([find_distance(self.colliobj, c)for c in self.gantry_objectlist])
        if self.laserguardbool:
            lgdist =  min([find_distance(self.laserguard, c) for c in self.lg_objectlist])
            return min([gantrydist,collidist,lgdist])
        else:
            return min([gantrydist,collidist])

    def get_body_distance(self):
        gantrydist = find_distance(self.gantry, self.body)
        collidist = find_distance(self.colliobj, self.body)
        if self.laserguardbool:
            lgdist =  find_distance(self.laserguard, self.body)
            return min([gantrydist,collidist,lgdist])
        else:
            return min([gantrydist,collidist])
        
    def create_render(self):
        resolution_percentage=80
        quality=100
        frame_step=1
        camera=1
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        bpy.context.scene.render.resolution_percentage = resolution_percentage
        bpy.context.scene.frame_step = frame_step
        bpy.context.scene.render.filepath = self.folder
        bpy.context.scene.render.image_settings.file_format = "AVI_JPEG"
        bpy.context.scene.render.image_settings.quality = quality
        bpy.context.scene.camera = bpy.data.objects["Camera_"+str(camera)]
        bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
        bpy.ops.render.opengl(animation=True, render_keyed_only=False, sequencer=False, write_still=False, view_context=False)
        
    def move(self,gantry,collimator_rot,table_rot,table_roll,table_pitch,table_lat,table_vert,table_long):

                
        if not -0.405<table_vert<0.55:
            print('vert out of range: {}'.format(table_vert))
            table_vert = bound(-0.405,0.55,table_vert)
            # raise AssertionError("couch vertical position out of bounds: {}".format(self.table_vert))
            
        if not -1.6<table_long<1.605:
            print('long out of range: {}'.format(table_long))
            table_long = bound(-1.6,1.605,table_long)
            # raise AssertionError("couch longitudial position out of bounds: {}".format(self.table_long))
            
        if not -0.245<table_lat<0.245:
            print('lat out of range: {}'.format(table_lat))
            table_lat = bound(-0.245,0.245,table_lat)
            # raise AssertionError("couch lateral position out of bounds: {}".format(self.table_lat))
        
        #Gantry rotation around Y
        self.gantry.rotate(np.array([-gantry,0,0]))

        #Collimator rotation
        self.colliobj.rotate(np.array([0,0,collimator_rot])+self.colliobj.rotstart)
        
        #Table rotation
        self.tablerot.rotate(np.array([0,0,table_rot])+self.tablerot.rotstart)
        
        #Table translation
        self.tablebottom.move(np.array([0,0,table_vert])+self.tablebottom.locstart)
        
        self.tablemiddle.move(np.array([0,table_lat,0])+self.tablemiddle.locstart)

        self.table_top.move(np.array([table_long,0,0])+self.table_top.locstart)
        
        self.table_top.rotate(np.array([table_pitch,table_roll,0]))

            
    def animate(self,render=False,outpath=None):
        for ob in bpy.context.scene.objects:
            ob.animation_data_clear()
           
        fps=bpy.context.scene.render.fps
        frames=np.linspace(0,100,self.n)*fps
        time_frames= np.append(0,frames.astype(int))
        bpy.context.scene.frame_end = time_frames[-2] 
        
        
        for j in range(self.n):
            #set frame
            bpy.context.scene.frame_set(time_frames[j])
            

            lat = self.table_lat[j] + self.virtual_iso[0]
            vert = self.table_vert[j] + self.virtual_iso[1]
            long = self.table_long[j] + self.virtual_iso[2]

            lat, vert, long = move_away(-self.gantry_rot[j],self.collimator_rot[j], lat, vert, long, 0)
            self.move(self.gantry_rot[j],self.collimator_rot[j],self.table_rot[j],self.table_roll,self.table_pitch,lat,vert,long)

            #Gantry rotation around Y
            self.gantry.object.keyframe_insert(data_path = 'rotation_euler')
            
            #Collimator rotation
            self.colliobj.object.keyframe_insert(data_path = 'rotation_euler')

            #Table rotation
            self.tablerot.object.keyframe_insert(data_path = 'rotation_euler')
            
            #Table translation
            self.tablebottom.object.keyframe_insert(data_path = 'location')
                  
            self.tablemiddle.object.keyframe_insert(data_path = 'location')
            
            self.table_top.object.keyframe_insert(data_path = 'location')
            self.table_top.object.keyframe_insert(data_path = 'rotation_euler')
        
        if render:
            print("Render started")
            resolution_percentage=80
            quality=100
            frame_step=2
            camera=1
            
            bpy.context.scene.render.resolution_x = 1920
            bpy.context.scene.render.resolution_y = 1080
            bpy.context.scene.render.resolution_percentage = resolution_percentage
            bpy.context.scene.frame_step = frame_step
            bpy.context.scene.render.filepath = outpath + '/'
            bpy.context.scene.render.image_settings.file_format = "AVI_JPEG"
            bpy.context.scene.render.image_settings.quality = quality
            bpy.context.scene.camera = bpy.data.objects["Camera_"+str(camera)]
            bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
            bpy.ops.render.opengl(animation=True, render_keyed_only=False, sequencer=False, write_still=False, view_context=False)
            
    def animate_map(self, outpath, distance=0):
        for ob in bpy.context.scene.objects:
            ob.animation_data_clear()
           
        fps=bpy.context.scene.render.fps
        frames=np.arange(0,self.n_table*self.n_gantry)
        print(frames)
        print(np.linspace(0,30,self.n_table*self.n_gantry)*fps)
        time_frames= np.append(0,frames.astype(int))
        bpy.context.scene.frame_end = time_frames[-2] 

        for j,g in enumerate(self.gantry_rot):
            for i,t in enumerate(self.table_rot):
                bpy.context.scene.frame_set(time_frames[i + self.n_table*j])
                lat, vert, long = move_away(-g, t, self.table_lat, self.table_vert, self.table_long, distance)  

                self.move(g,0,t,0,0,lat ,vert ,long )
                print(g, t)
                #Gantry rotation around Y
                self.gantry.object.keyframe_insert(data_path = 'rotation_euler')
                
                #Collimator rotation
                self.colliobj.object.keyframe_insert(data_path = 'rotation_euler')

                #Table rotation
                self.tablerot.object.keyframe_insert(data_path = 'rotation_euler')
                
                #Table translation
                self.tablebottom.object.keyframe_insert(data_path = 'location')
                    
                self.tablemiddle.object.keyframe_insert(data_path = 'location')
                
                self.table_top.object.keyframe_insert(data_path = 'location')
                self.table_top.object.keyframe_insert(data_path = 'rotation_euler')
                
        print("Render started")
        resolution_percentage=80
        quality=100
        frame_step=10
        camera=3
        
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        bpy.context.scene.render.resolution_percentage = resolution_percentage
        bpy.context.scene.frame_step = frame_step
        bpy.context.scene.render.filepath = outpath + '/'
        bpy.context.scene.render.image_settings.file_format = "AVI_JPEG"
        bpy.context.scene.render.image_settings.quality = quality
        bpy.context.scene.camera = bpy.data.objects["Camera_"+str(camera)]
        bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
        bpy.ops.render.opengl(animation=True, render_keyed_only=False, sequencer=False, write_still=False, view_context=False)
            
    def close(self,showblender=False,outpath=None):
        if showblender:
            filepath=outpath+'/animation.blend'
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            bpy.ops.wm.quit_blender()
            bpy.ops.wm.open_mainfile(filepath=filepath)
        else:    
            bpy.ops.wm.quit_blender()
