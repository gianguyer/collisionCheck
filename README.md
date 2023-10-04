# collisionCheck
This is a collision check program using blender. The program either calculates a collision-free map or checks paths for collisions given in XML file format for a TrueBeam system model. There is a GUI  available for the Eclipse Treatment Planning System (TPS). The corresponding publication can be found here:  https://doi.org/10.1002/acm2.14165

There are following folders:
- code: contains all code files
- config: contains the configuration file
- model: contains the blender model
- studies: Folder for data

Requirements:
- Blender needs to be installed. You can get blender from here https://www.blender.org/download/

Attention: 
The python programs run in the bundled python of blender. If packages are missing, do the following steps:
1. Go to the python library inside the blender distribution folder, e.g. blender/3.2/python/bin
2. Run /python3 -m pip install --upgrade pip
3. Run /pip3 install matplotlib

Installation:
Following paths need to be set to run the program:
- blenderpath in config.properties: The path to the blender executable needs to be specified, e.g. /home/blender/blender
- HOMEDIR in run-blender script: The path to the collisionCheck folder needs to be specified, e.g. /home/collisionCheck

Run:
Run the collision check: ./code/run-blender study patient plan script
- study: specify the study, e.g. demo
- patient: specify the patient, e.g. Patient_0
- plan: specify the plan, e.g. Plan_1
- script: specify which script to run, either collisionMap or pathCheck


Eclipse Script:
- There are two Eclipse scripting API for running the collision check directly from the Eclipse TPS.
- Local script: This script is for when the collision check and blender are installed on the same computer as the Eclipse TPS
- Remote script: This script is for when the collision check and blender are installed on a different computer which can be accesed via ssh from the Eclipse TPS computer

In the remote script, following things need to be specified:
- localDir: Path for the data on the local computer, e.g. d:\\data\\collision
- remote: Name and  IP for the remote connection, e.g. demo@remote.ch
- remoteDir: Path to the collisionCheck folder on the remote computer

In the local script, following things need to be specified:
- localDir: Path to the collisionCheck folder 
