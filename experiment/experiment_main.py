"""
Created on Mon Mar 10 2025
@author: Max Van Migem
"""
import numpy as np
import os
import time
import sys
import pylink #the last is to communicate with the eyetracker
import pickle
from psychopy import parallel, visual, gui, data, event, core, monitors
from psychopy.visual import ShapeStim
from psychopy import logging
from math import fabs


####################################################
#Initialize trial variables
####################################################

lab = 'none'   #'actichamp'/'biosemi'/'none'

mode = 'test'   #'default'/'test'

eye_tracking = False #True/False

if eye_tracking:
    from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy #this are functions used to run the eyetracker calibration and validation

#options
n_trials = 28 # per block
n_odd = 7  # per block
n_catch = 13 # per section

n_blocks = 15  # per section        
n_sections = 2 # divides experiment into attended vs unattended sections 

#to check problem
trigger_time_list = []

isi_duration = .52
stim_onset_jitter = .07
iti_duration = .5
stim_duration = .1

# random generator
rng = np.random.default_rng(seed=None)
# array with random jitter for horizontal stim lines (this might have to be a standard array as in the same for everyone)
stim_jitter_path = os.getcwd()+'/stim_jitter.npy'
linejitter_arr = np.load(stim_jitter_path)

####################################################
# Dialogue box
####################################################

language = 'English' # default

info =  {'Gender': ['Male','Female', 'X'],'Language':['English','Dutch'], 
         'Age': '', 'Dominant hand':['left','right','ambi'],
         'Participant ID (***)': '', 'Localised Quadrant':[0,1,2,3]}

already_exists = True
while already_exists and mode != 'test':   #keep asking for a new name when the data file already exists
     dlg = gui.DlgFromDict(dictionary=info, title='Predatt Experiment')  #display the gui
     file_name = os.getcwd() + '/data/' + 'predatt_participant_' + info['Participant ID (***)']   #determine the file name (os.getcwd() is where your script is saved)
     if not dlg.OK:
         core.quit()
     if not os.path.isfile((file_name + '.csv')):  #only escape the while loop if ParticipantNr is unique
         already_exists = False
     else:
         dlg2 = gui.Dlg(title = 'Warning')  #if the suggested_participant_nr is not unique, present a warning msg
         suggested_participant_nr = 0
         suggested_file_name = file_name
         while os.path.isfile(suggested_file_name + '.csv'): #provide a suggestion for another ParticipantNr
             suggested_participant_nr += 1
             suggested_file_name = os.getcwd() + '/data/' + 'predatt_participant_' + str(suggested_participant_nr)
         dlg2.addText('This Participant Nr is in use already, please select another.\n\nParticipant Nr ' 
                      +  str(suggested_participant_nr) + ' is still available.')
         dlg2.show()

####################################################
# System settings and input transformation
####################################################
if mode != 'test':   
    # Language selection
    lang_map = {'English':0 , 'Dutch':1}
    language = lang_map[info['Language']]
# We download EDF data file from the EyeLink Host PC to the local hard
# drive at the end of each testing session, here we rename the EDF to
# include session start date/time

time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
if not mode == 'test':
    session_identifier = 'pp_' + info['Participant ID (***)'] + time_str
    # create a folder for the current testing session in the "results" folder
    session_folder = os.path.join(os.getcwd() + '/data/', session_identifier)

    if not os.path.exists(session_folder):
        os.makedirs(session_folder)
# Define a monitor
system_monitor = monitors.Monitor('cap_lab_monitor')   
# # This is to set a new configuration for your monitor
# system_monitor.setSizePix((1024, 768))
# system_monitor.setWidth(39.2)
# system_monitor.setDistance(65)
# system_monitor.save()

# #initialize window#
win = visual.Window(fullscr=True,color= (-1, -1, -1), colorSpace = 'rgb', units = 'pix', monitor= system_monitor,  useFBO=True, multiSample=True)
win.mouseVisible = False

####################################################
# Create text and fixation cross
####################################################

cross_standard_col = 'white'
catch_colour = 'red'
test_instruction = ('Test')
start_instruction =[('Welcome and thank you for participating in this experiment.\n\n' + 
                     'Please press SPACE to continue.'),
                    ('Welkom en bedankt om deel te nemen aan dit experiment.\n\n' +
                     'Druk op SPATIE om verder te gaan.')]

stim_attend_instr = [('.'),
                     ('.')]

stim_unattend_instr = [('.'),
                       ('.')]

eye_tracking_instr = [('Please wait for the recalibration of the eye tracker.'),
                      ('Even geduld voor de recalibratie van de eye tracker.')]

eye_tracking_pauze_instr = [('Press SPACE to continue the experiment.'),
                            ('Druk op SPATIE om verder te doen met het experiment')]

message = visual.TextStim(win, text='',height= 30) 

# manual input of fixation cross vertices, very hard coded but it's fast and customizable
cross_vert = [(-.05, .05), (-.05, .35), (.05, .35,), (.05, .05),
              (.35, .05), (.35,-.05), (.05, -.05),(.05,-.35),
              (-.05,-.35), (-.05, -.05), (-.35,-.05), (-.35, .05)]

# defining fixcross using vertices above, you can change the size, colour, etc.. of the fixation cross here   
cross = ShapeStim(win, vertices=cross_vert, size=30, color=cross_standard_col,
                   lineWidth=0, pos=(0, 0), ori=0, autoDraw=False)

teststim = ShapeStim(win, vertices=[(0.5,1.0), (1.0,1.0), (0.5,1.0), (1.0,1.0)],
                     size=200, fillColor='white', lineWidth=1, pos=(0, 0), ori=0, closeShape=False)

####################################################
# Functions for generating the stimulus
####################################################

def generateStimCoordinates(gridcol, gridrow, jitter):
    """
    Generates coordinates used to draw the stimulus lines
    """
    # Calculate spacing of grid
    x_spacing = 1.0 / (gridcol)
    y_spacing = 1.0 / (gridrow)

    # Create an array to store coordinates: every point (x,y) of the grid for every quadrant (4) 
    coord_array = np.empty(shape = (gridcol,gridrow,2,4),dtype= 'object')
    quadrant_set = [[-1,1],[1,1],[1,-1],[-1,-1]]

    # Generate grid coord per quadrant
    for i,quad in enumerate(quadrant_set):
        # Per row
        for row in range(gridrow):
            # Per column
            for col in range (gridcol):

                grid_x = col * x_spacing  # grid points
                grid_y = row * y_spacing  

                grid_x = grid_x * quad[0]   # quadrant position
                grid_y = grid_y * quad[1]   # quadrant position

                coord_array[col,row,0,i] = grid_x  # Store them in big ass array
                coord_array[col,row,1,i] = grid_y

    # flip the matrices so that they have the 'orientation' corresponding to the quadrant 
    coord_array[:,:,0,0] = np.flip(coord_array[:,:,0,0], axis=0) 
    coord_array[:,:,1,0] = np.flip(coord_array[:,:,1,0], axis=0) 

    coord_array[:,:,0,2] = np.flip(coord_array[:,:,0,2], axis=1) 
    coord_array[:,:,1,2] = np.flip(coord_array[:,:,1,2], axis=1) 

    coord_array[:,:,0,3] = np.flip(coord_array[:,:,0,3], axis=(0,1)) 
    coord_array[:,:,1,3] = np.flip(coord_array[:,:,1,3], axis=(0,1)) 

    #  Add jitter
    for i in range(4):
        coord_array[:,:,:,i] =  coord_array[:,:,:,i] + jitter[:gridcol,:gridrow,:]
  
    return coord_array



def generateStim(linelength, linewidth ,coord_array, size, fixdistance, slant):
    """ 
    Generate an ElementArrayStim object consisting of lines on the coordinates for stimulus for each quadrant
    Then four more arrays are created each representing a catch trial in a separate quadrant
    Returns a 5x4 array of lists with each list containing the line stimuli for a quadrant
    If localizer is set to True then it generates a grid in the upper or lower visual field instead of quadrants
    """
    # 
    sections = 4
    # This is to calculate the distance to the fixation cross
    dist = np.sqrt(np.square(fixdistance)/2) #pythagoras
    quads = [[-1,1],[1,1],[1,-1],[-1,-1]]

    # Get size of grid
    gridcol = np.shape(coord_array)[0]
    gridrow = np.shape(coord_array)[1]

    # Init arrays to store line objects per quadrant and also for every possible catch trial 
    line_stimuli = np.empty((2,sections), dtype=object)   # 2 types (0 is normal white lines, 1 is catch stim ) and 4 quadrants
 
    for quad in range(sections):
        n_lines = gridcol*gridrow
        xys = np.empty((n_lines,2)) #coordinates to pass to elementArrayStim
        it_count = 0 # idk man... this is a work around because im too lazy to completely change the structure that I used before i.e. two nested loops per column (below)
        for row in range(gridrow):
            for col in range(gridcol):

                # Define stim coordinates
                the_x = (coord_array[col,row,0,quad] * size) + (quads[quad][0]*dist)  # size and distance from fixation are all in here 
                the_y = (coord_array[col,row,1,quad] * size) + (quads[quad][1]*dist)              
                                                                              
                xys[it_count,0] = the_x
                xys[it_count,1] = the_y
                it_count += 1
        sizes = np.atleast_2d([linelength,linewidth]).repeat(repeats=n_lines, axis=0)
        # Normal stimuli
        line_stimuli[0,quad] = visual.ElementArrayStim(win, units='pix',elementTex=None, elementMask='sqr', xys= xys, oris = slant,
                                           nElements=n_lines, sizes=sizes, colors=(1.0, 1.0, 1.0), colorSpace='rgb')


    return line_stimuli


####################################################
#Trial display functions
####################################################


def drawStim(line_stimuli, quad, catch):
    """ 
    Draws the stimuli in the correct quadrant
    Catch = 0 means normal color catch = 1 means catch
    """
    # Evaluate the task and make the apropriate catch

    line_stim = line_stimuli[0,quad]
    if catch:
        cross.color = catch_colour 
    # Draw 
    line_stim.draw()

####################################################
#Experiment value initialization
####################################################

# Generate main stimuli
grid = generateStimCoordinates(gridcol=12, gridrow=10, jitter=linejitter_arr)
stimset = generateStim(linelength=35,linewidth=2, coord_array=grid,
                        size=276, fixdistance=134,slant=30)



while True:
    win.flip()
    drawStim(line_stimuli=stimset,quad=0,catch=0)
    keys = event.getKeys()
    # If the spacebar is pressed, break the loop
    if 'space' in keys:
        break
    # Add a small delay to avoid high CPU usage
    core.wait(0.01)
# Close the window

win.close()
core.quit()