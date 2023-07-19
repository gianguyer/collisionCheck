# collisionCheck
This is a collision check program using blender. The program either calculates a collision-free map or checks paths for collisions given in XML file format for a TrueBeam system model. There is a GUI  available for the Eclipse Treatment Planning System.

There are following folders:
code: contains all code files
config: contains the configuration file
model: contains the blender model
studies: Folder for data

Requirements:
- Blender needs to be installed. You can get blender from here https://www.blender.org/download/

Attention: 
The python programs run in the bundled python of blender. If packages are missing, do the following steps:
1. Go to the python library inside the blender distribution folder, e.g. blender/3.2/python/bin
2. Run /python3 -m pip install --upgrade pip
3. Run /pip3 install matplotlib
