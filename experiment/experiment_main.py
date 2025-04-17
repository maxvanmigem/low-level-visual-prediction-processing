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
from psychopy.hardware import keyboard as kb
from psychopy import logging
from math import fabs


####################################################
#Initialize trial variables
####################################################

lab = 'none'   #'actichamp'/'biosemi'/'none'

mode = 'default'   #'default'/'test'

eye_tracking = False #True/False

if eye_tracking:
    from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy #this are functions used to run the eyetracker calibration and validation

# Options
n_trials = 28 # per block
n_odd = 7  # per block
n_target = 8 # per block
n_blocks = 32  # in total      


#to check problem
trigger_time_list = []

isi_duration = .52
stim_onset_jitter = .07
iti_duration = .5 # there is also a 300 ms ixation check
stim_duration = .1

# big breaks
break_blocks = [8,16,24]

# angles
angle_set = [0,90]
ang_map = ['horz','vert'] # depends on actual angle see angle_set

# random generator
rng = np.random.default_rng(seed=None)
# array with random jitter for horizontal stim lines (this might have to be a standard array as in the same for everyone)
stim_jitter_path = os.getcwd()+'/stim_jitter.npy'
linejitter_arr = np.load(stim_jitter_path)

# images to show rotation direction
anticlockwise_path = os.getcwd()+'/anticlockwise_arrow.png'
clockwise_path = os.getcwd()+'/clockwise_arrow.png'

####################################################
# Dialogue box
####################################################


info =  {'Gender': ['Male','Female', 'X'],'Language':['English','Dutch'], 
         'Age': '', 'Dominant hand':['left','right','ambi'],
         'Participant number': '', 'Localised Quadrant':[0,1,2,3]}

already_exists = True
while already_exists and mode != 'test':   #keep asking for a new name when the data file already exists
     dlg = gui.DlgFromDict(dictionary=info, title='Prediction Experiment')  #display the gui
     file_name = os.getcwd() + '/data/' + 'participant_' + info['Participant number']   #determine the file name (os.getcwd() is where your script is saved)
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

pp_id = 0
if mode == 'default':
    pp_id = int(info['Participant number'])


####################################################
# System settings and input transformation
####################################################

language = 0 # default
avoid_quadrant = 0

if mode != 'test':   
    # Language selection
    lang_map = {'English':0 , 'Dutch':1}
    language = lang_map[info['Language']]
    avoid_quadrant = info['Localised Quadrant']
# We download EDF data file from the EyeLink Host PC to the local hard
# drive at the end of each testing session, here we rename the EDF to
# include session start date/time

time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
if not mode == 'test':
    session_identifier = 'pp_' + info['Participant number'] + time_str
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
target_colour = 'red'
test_instruction = ('Test')
start_instruction = [('Welcome and thank you for participating in this experiment.\n' + 
                     'Please read the following instructions carefully.\n\n' + 
                     'Please press SPACE to continue.'),
                     ('Welkom en bedankt om deel te nemen aan dit experiment.\n' +
                     'Gelieve de volgende instructies zorgvuldig te lezen.\n\n' +
                     'Druk op SPATIE om verder te gaan.')]

main_instruction = [('In this experiment you will see groups of lines apearing in a sequence.\n\n' + 
                    'This sequence will have a certain direction. \n\n' + 
                    'The lines will also have a certain angle. \n\n' + 
                    'You will have to respond to this direction or to angle of the lines. \n\n' + 
                    'This will depends on the instructions at the start of every block. \n\n' +
                    'Please press SPACE to continue.'),
                    ('In dit experiment zul je groepen lijnen zien die in een bepaalde volgorde verschijnen.\n\n' +
                    'Deze volgorde heeft een bepaalde richting.\n\n' +
                    'De lijnen een specifieke hoek.\n\n' +
                    'Jij moet ofwel reageren op de richting of op de hoek van de lijntjes.\n\n' +
                    'Dit zal afhangen van de instructies aan het begin van elke block. \n\n' +
                    'Druk op SPATIE om verder te gaan.')]

stim_rotation_instr = [('Respond to the rotation direction when the cross turns red'),
                       ('Reageer op de rotatie richting wanneer het kruis rood wordt')]

stim_angle_instr = [('Respond to the angle of the lines when the cross turns red'),
                    ('Reageer op de hoek van de lijntjes wanneer het kruis rood wordt')]

press_d_instr = [('Press the \'d\'-key'),
                 ('Druk op de \'d\'-toets')]
press_k_instr = [('Press the \'k\'-key'),
                 ('Druk op de \'k\'-toets')]

cue_rotation_instr = [('In the majority of the time the lines will rotate in this direction'),
                      ('In het grootste deel van de tijd zullen de lijntjes in deze richting roteren')]
cue_angle_instr = [('In the majority of the time the lines will have this angle'),
                   ('In het grootste deel van de tijd zullen de lijntjes deze hoek hebben')]

eye_tracking_instr = [('Please wait for the recalibration of the eye tracker.'),
                      ('Even geduld voor de recalibratie van de eye tracker.')]

space_instr = [('Press SPACE to continue'),
               ('Druk op SPATIE om verder te doen')]

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

    Parameters:
        gridcol (int): Number of columns in the grid.
        gridrow (int): Number of rows in the grid.
        jitter (ndarray): 30x30x2 array that adds variation to the grid coords.
    Returns:
        coord_array (ndarray):array of shape col x row x 2 x 2 with xy coordinates for start and end points for every line
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


def generateStim(linelength, linewidth ,coord_array, size, fixdistance, angles=angle_set):
    """ 
    Generate an ElementArrayStim object consisting of lines on the coordinates 
    for stimulus for each quadrant position and with differently angled lines

    Parmeters:
        linelength (int): length of individual lines (pix but can be any unit)
        linewidth (int): width of individual lines (pix but can be any unit)
        coord_array (ndarray): set of x and y coords for de sub elements
        size (int or float): scaling factor
        fixdistance (int or float): distance of stimulus corner to screen center
        angles (list of ints): angle of the stimuli, two types of angles 
    Returns:
        line_stimuli (ndarray of psychopy ElementArrayStim): array with visual objects for different position 
    """
    # i.e. quadrants
    sections = 4
    # This is to calculate the distance to the fixation cross
    dist = np.sqrt(np.square(fixdistance)/2) #pythagoras
    quads = [[-1,1],[1,1],[1,-1],[-1,-1]]

    # Get size of grid
    gridcol = np.shape(coord_array)[0]
    gridrow = np.shape(coord_array)[1]

    # Init arrays to store line objects per quadrant and also for two differny line angles
    line_stimuli = np.empty((2,sections), dtype=object)   # 2 types (angle_set see intial values at start of script) and 4 quadrants
 
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
        # Angle 0 stimuli (\)
        line_stimuli[0,quad] = visual.ElementArrayStim(win, units='pix',elementTex=None, elementMask='sqr', xys= xys, oris = angles[0],
                                           nElements=n_lines, sizes=sizes, colors=(1.0, 1.0, 1.0), colorSpace='rgb')
        # Angle 1 stimuli (/)
        line_stimuli[1,quad] = visual.ElementArrayStim(win, units='pix',elementTex=None, elementMask='sqr', xys= xys, oris = angles[1],
                                           nElements=n_lines, sizes=sizes, colors=(1.0, 1.0, 1.0), colorSpace='rgb')

    return line_stimuli


####################################################
#Trial display functions
####################################################

def drawStim(line_stimuli, quad, angle):
    """ 
    Draws the stimuli in the correct quadrant
    Parmeters:
        line_stimuli (ndarray): array with psychopy ElementArrayStim objects for every position and slant
        quad (int): quadrant 0,1,2 or 3
        angle (0 or 1): angle 0 or 1 see angle_set for actual angles in degrees
    """
    # Select the stimulus for the quadrant and slant
    line_stim = line_stimuli[angle,quad]

    # Draw 
    line_stim.draw()


def stimPresentation(stimulus, stim_dur, isi_dur,iti_dur, start_quad, direction, q_target, angles, lab=lab): 
    """
    Stimulus presentation for a single trial
    Parmeters:
        stimulus (ndarray): array with psychopy ElementArrayStim objects for every position and slant
        stim_dur (float): stimulus presentation duration in seconds
        isi_dur (float): inter-stimulus intervalin seconds
        iti_dur (float): inter-trial interval in seconds
        start_quad (int): position of the first stimulus in the sequence 0,1,2 or 3
        direction (0 or 1): direction of the sequence clockwise (0) or anticlockwise (1)
        q_target (int): determines the moment (which quad) of a target (1,2,3,4) quadrant if there is a no target (0) 
        angles ( list of 0 and 1): first or second angle see angle_set for actual angles
        lab (str): determines EEG aspects such as port and trigger
    Return:
        stim_times (ndarray): length of 4 with times of stim presentation
        trial_time (float): duration of the trial
        triggers (ndarray): the EEG triggers
    """
    # Check timing
    stim_clock = core.Clock()
    trial_clock = core.Clock()
    stim_times = []
    triggers = []
    stimpos_ls = np.roll(np.arange(4), -start_quad, axis=0)   # select the starting point of the stimulus
    # This is to select the presentation direction
    dir_list = np.arange(4)
    if direction == 0:
        stimpos_ls = np.roll(dir_list, -start_quad, axis=0)   # select the starting point of the stimulus
    elif direction == 1:
        stimpos_ls = np.roll(dir_list[::-1], 1+start_quad, axis=0)   # select the starting point of the stimulus and reverse direction
    
    # This is for the target trials
    target_ls = np.zeros(4,dtype=int) 
    if not q_target == 0:
        target_ls[q_target] = 1  

    # Send trial start trigger
    eegTriggerSend(int(99),lab)
    # Trial procedure
    for i,stimpos in enumerate(stimpos_ls):
        win.flip()
        stim_clock.reset()
        gazeCheck() # fixation check in for every stimulus
        if target_ls[i]:
            cross.color = target_colour 
        # Implemenent a target trial
        trigger = int(selectEEGStimulusTrigger(pos=stimpos,seq=i)) # EEG trigger generation
        triggers.append(trigger)
        drawStim(stimulus,stimpos,angles[i])
        wait = isi_dur[i]-stim_clock.getTime() # Drawing the stimulus takes time, this compensates that
        core.wait(wait)
        stim_timing =trial_clock.getTime()*1000
        win.flip()
        eegTriggerSend(trigger,lab) # Send trigger
        core.wait(stim_dur)
        win.flip()
        cross.color = cross_standard_col
        stim_times.append(stim_timing)

    trial_time = trial_clock.getTime()*1000
    core.wait(iti_dur)
    return stim_times, trial_time, triggers, stimpos_ls


def displayMessage(msg=None, block_msg=False, lang=0, block_num=None, hits=None, misses=None, wrong=None, break_blocks=None):
    """ 
    Function to display instruction, score and other text
    Parmeters:
        msg (str): message to display
        block_msg (bool): whether it is a message in between blocks
        lang (int): intruction language
        block_num (int): the block number
        hits (int): particpant amount of hits
        missed (int): particpant amount of misses
        wrong (int): particpant amount of errors
        break_blocks (list of int): the block where we include a longer break
    """
    message.text = msg
    if block_msg:
        if block_num == 1:
            lang_bl_instr = [('Block 1\n\n Press SPACE to start the main experiment.'),
                             ('Blok 1\n\n Druk op SPATIE om te beginnen met het hoofdexperiment.')]
        elif block_num in break_blocks:
            lang_bl_instr = [(f'You can now take a longer break if you want.\n\n'  + 
                            f'Block {block_num} \n\n Hits: {hits}\nMisses: {misses}\nWrong/too slow: {wrong}' +
                            '\n\n Press SPACE to start recalibration.'),
                            (f'Blok {block_num} \n\n Raak: {hits}\nGemist: {misses}\nVerkeerd/te laat: {wrong}' +
                            '\n\n Je kan nu een langere pauze nemen. \n\n Druk op SPATIE om opnieuw te calibreren.')]
        else:
            lang_bl_instr = [(f'Block {block_num} \n\n Hits: {hits}\nMisses: {misses}\nWrong/too slow: {wrong}' +
                            '\n\nYou can take a quick break if you want. \n\n Press SPACE to continue the experiment.'),
                            (f'Blok {block_num} \n\n Raak: {hits}\nGemist: {misses}\nVerkeerd/te laat: {wrong}' +
                            '\n\n Je kan nu een korte pauze nemen. \n\n Druk op SPATIE om met het experiment verder te doen.')]
        message.text = lang_bl_instr[lang]

    message.draw()
    win.flip()
    start_key = event.waitKeys(keyList = ['space','escape'])
    if start_key[0] == 'escape':
        if eye_tracking:
            terminate_task()
        core.quit() #no event.clearEvents() necessary
        win.close()
    event.clearEvents()


def displayCondInstruction(cond, key_map, lang=0,angles=angle_set):
    """ 
    Function for displaying block task
    Parameters:
        cond (int): condition 0 -> rotation task, 1 -> angle task
        key_map (list of list): with the first list giving the rotation keys in order and the second givning the angle keys in order
        lang (int): instruction 0 -> eng, 1 -> dutch 
    """
    left_instr = visual.TextStim(win, text=press_d_instr[lang],pos=(-200,-150),height= 30) 
    right_instr = visual.TextStim(win, text=press_k_instr[lang],pos=(200,-150),height= 30) 
    bottom_instr = visual.TextStim(win, text=space_instr[lang],pos=(0,-280),height= 30) 

    if key_map[0][0] == 'd':
        clock_wpos = (-200,-30)
        anticlock_wpos = (200,-30)
    else:
        clock_wpos = (200,-30)
        anticlock_wpos = (-200,-30)

    if key_map[1][0] == 'd':
        angle_0_wpos = (-200,-30)
        angle_1_wpos = (200,-30)
    else:
        angle_0_wpos = (200,-30)
        angle_1_wpos = (-200,-30)
 
    if cond == 0:
        top_instr = visual.TextStim(win, text=stim_rotation_instr[lang],pos=(0,200),height= 30) 
        cond_im_1 = visual.ImageStim(win,image=clockwise_path,units='pix',pos=clock_wpos,size=200)
        cond_im_2 = visual.ImageStim(win,image=anticlockwise_path,units='pix',pos=anticlock_wpos,size=200)
    elif cond == 1:
        top_instr = visual.TextStim(win, text=stim_angle_instr[lang],pos=(0,200),height= 30) 
        cond_im_1 = visual.Rect(win,width=120,height=10,fillColor ='white',units='pix',pos=angle_0_wpos,ori=angles[0])
        cond_im_2 = visual.Rect(win,width=120,height=10,fillColor ='white',units='pix',pos=angle_1_wpos,ori=angles[1])

    top_instr.draw() 
    left_instr.draw()
    right_instr.draw()
    cond_im_1.draw() 
    cond_im_2.draw() 
    bottom_instr.draw()
    win.flip()
    start_key = event.waitKeys(keyList = ['space','escape'])
    if start_key[0] == 'escape':
        if eye_tracking:
            terminate_task()
        core.quit() #no event.clearEvents() necessary
        win.close()
    event.clearEvents()

def displayBlockCue(cond, rot_odd, ang_odd, lang=0,angles=angle_set):
    """ 
    Function for displaying block cue
    Parameters:
        cond (int): condition 0 -> rotation task, 1 -> angle task
        rot_odd (str): indicates which direction is odd
        ang_odd (0 or 1): indicates which angle is odd
        lang (int): instruction 0 -> eng, 1 -> dutch 
    """
    bottom_instr = visual.TextStim(win, text=space_instr[lang],pos=(0,-280),height= 30) 
    if cond == 0:
        top_instr = visual.TextStim(win, text=cue_rotation_instr[lang],pos=(0,200),height= 30)
        cond_im = visual.ImageStim(win,image=clockwise_path,units='pix',pos=(0,-100),size=250)
        if rot_odd == 'clockwise': # it's flipped because the cue indicates the majority
            cond_im.image = anticlockwise_path
    elif cond == 1:
        top_instr = visual.TextStim(win, text=cue_angle_instr[lang],pos=(0,200),height= 30)
        cond_im = visual.Rect(win,width=120,height=10,fillColor ='white',units='pix',pos=(0,-100),ori=angles[0])
        if ang_odd == 0: # it's flipped because the cue indicates the majority or the regular direction
            cond_im.ori = angles[1]

    top_instr.draw() 
    cond_im.draw() 
    bottom_instr.draw()
    win.flip()

    start_key = event.waitKeys(keyList = ['space','escape'])
    if start_key[0] == 'escape':
        if eye_tracking:
            terminate_task()
        core.quit() #no event.clearEvents() necessary
        win.close()
    event.clearEvents()


####################################################
#Trial sequence functions
####################################################

def generatePredictionList(tr_block, n_odd, odd, mode='rotation'):
    """ 
    Generate pseudo randomized properties of trial direction or stimulus angle on a block level
    Parameters:
        tr_block (int):number of trials per block
        n_odd (int): number of odd per block
        odd (int): indicate which direction or angle is odd 0 clockwise/left and 1 anticlockwise/right
        mode (str): indentifies whether it is trial level ('rotation) or stimulus ('angle')
    Returns:
        predicition_arr (ndarray): array with length tr_block with 0's and 1's for prediciton condition 
    """
    # Check if there are correct amount of odds
    if n_odd > tr_block/2:
        raise ValueError("Invalid input parameters")
    # Multiple the trial and odd var by 4 because there are 4 stimuli per trial
    if mode == 'angle': 
        n_odd = n_odd*4
        tr_block = tr_block*4

    prediction_arr = np.zeros(tr_block , dtype=int)
    possible_positions = np.arange(tr_block)
    # Randomly select positions for 1's, ensuring no two are consecutive
    selected_positions = []
    while len(selected_positions) < n_odd:
        pos = np.random.choice(possible_positions)
        selected_positions.append(pos)
        # Remove the selected position and its adjacent positions to prevent consecutive 1's
        possible_positions = possible_positions[(possible_positions < pos - 1) | (possible_positions > pos + 1)]
    prediction_arr[selected_positions] = 1
    
    # Flip the 0's and 1's depending on which is odd
    if not odd:
        prediction_arr = prediction_arr ^ 1
        
    return prediction_arr


def generateTrialStarts(tr_block,bad_quadrant):
    """
    Generate a list with the start positions for each block depending on the localised quadrant set
    Parameters:
        tr_block (int):number of trials per block
        bad_quadrant (int): the quadrant that we want to exclude based on localiser (0,1,2,3)
    Returns:
        block_list (list of ints): list of starting postions for every trial in a block
    """
    quad_li = np.arange(4)
    # You have two diametric quadrants of interest
    quad_a = quad_li[bad_quadrant]
    quad_b = quad_li[(bad_quadrant +2)%4]
    # Create the arrays
    half_blocks = int(np.ceil(tr_block/2))
    aquad_arr = np.full(half_blocks,quad_a)
    bquad_arr = np.full(half_blocks,quad_b)
    
    section_blocks = np.concatenate((aquad_arr,bquad_arr))
    np.random.shuffle(section_blocks)
    block_list =  section_blocks[:tr_block]

    return block_list


def generateTargetTrials(tr_block, ntarget):
    """ 
    Some trials are target trials, this function generates a list to designate which trials are
    Parameters:
        tr_block (int):number of trials per block
        ntarget (int): number of target trials
    Return:
        full_list (list of ints): list of targets for every trial in a block
    """
    # Make a list with normal trials (0) and a list with target trials (1)
    full_list = np.zeros(tr_block-ntarget,dtype=int)
    c_list = np.ones(ntarget*3,dtype=int) # make a longer list and cut it short otherwise it won't work with ntarget <3
    for i,one in enumerate(c_list):
        c_list[i] = int(one + i%3)   # Just adding 0,1, or 2  to every element (again: if ntarget is divisible by 3 then it's balanced)
    # Make correct length
    np.random.shuffle(c_list)
    c_list = c_list[:ntarget]

    # Make one list
    full_list = np.append(full_list,c_list)
    # Shuffle
    np.random.shuffle(full_list)

    return full_list


def generateTrialTimings(tr_block,isi_dur, jitter,randng=rng):
    """ 
    Generate a list of timings 4 per trial
    Parameters:
        tr_block (int):number of trials per block
        isi_dur (float): mean duration of isi
        jitter (float): variation on isi duration
        randng (np Generator class): random number generator
    Returns:
        block_tlist (list of lists): list of timings for every stimulus per trial
    """
    block_tlist= []
    for i in range(tr_block):
        trial_tlist = []
        for p in range(4):
            stim_t = isi_dur + randng.uniform(low =-jitter,high=jitter)
            trial_tlist.append(stim_t)
        block_tlist.append(trial_tlist)
    return block_tlist

def generateBlockLevels(nblocks: int):
    """ 
    Generate list with half half zeros and another half ones for any block level parameter
    The attention conditions, which direction is odd or which angle is odd
    Parameters:
        nblocks (int): amount of blocks
    Returns:
        cond_list (ndarray): array of length nblocks with equal amounts 0's (rotation) and 1's (angle) 
    """
    # Make a list with normal trials (0) and a list with target trials (1)
    half_block = int(np.ceil(nblocks/2))
    cond_1 = np.full(half_block,0,dtype=int)
    cond_2 = np.full(half_block,1,dtype=int)
    full_cond = np.concatenate([cond_1,cond_2]) 
    np.random.shuffle(full_cond)
    cond_list = full_cond[:nblocks]
    return cond_list

def participantCounterBalance(participant_number,conds = 4):
    """ 
    Assign particpant to conditions such as key-mappings and odd vs regular direction/angles
    Parameters:
        participant_number (int):identifier that serves as unique key for assignment
        conds (int): number of conditions
    Returns:
        counter_code (ndarray): array with length conds with a code for every participant 
    """
    counter_code = np.empty(conds, dtype=int)
    for i in range(conds):
        counter_code[i] = (participant_number // (i+1)) % 2

    return counter_code


####################################################
# Measurement functions
####################################################

def evaluateResponse(stim_times,target,cond,direction,angles,keys_mapped,key,rt_limit):
    """
    Evaluate the response to the trial
    Parameters:
        stim_times (list of floats): the times a stimulus apeared i.r.t. the trial start
        target (int): if target trial and which (0 or 2-3)
        cond (int): which condition 0 rotation or 1 angles
        direction (int): rotation direction 0 clockwise or 1 anticlockwise
        angles (list): list of angles for every stim in the trial 0 or 1
        keys_mapped (list of list): list of key mapping for the subject [rotation keys (list of k and d),angle keys (list of k and d)] 
        key (list of tuples):
        rt_limit (float): the time limit for a response in seconds
    Returns:
        acc (str): gives the accuracy of the response
        rt (float or None): gives reaction times if subject reacted
    """
    if not key: # If no key was pressed
        acc = 'correct_nogo'
        if target:
            acc = 'miss' 
        rt = None 
        return acc, rt
    else: # If key was pressed
        if target:
            rt = key[0][1] - (stim_times[target]/1000)
            print(stim_times[target]/1000)
            acc = 'incorrect'
            if rt < 0:
                acc = 'false_fire'
                return acc, rt
            if rt > rt_limit:
                acc = 'too_slow'
                return acc, rt
            if not cond:
                if key[0][0] == keys_mapped[0][direction]:
                    acc = 'correct'
            else:
                if key[0][0] == keys_mapped[1][angles[target]]:
                    acc = 'correct'
            return acc, rt
        else:
            acc = 'false_fire'
            rt = key[0][1]
            return acc, rt
    

def eegTriggerSend(eeg_trigger, lab): #need to elaborate
    """
    Sends trigger to EEG recording
    Parameters:
        eeg_trigger (int): number code to send to the EEG computer
        lab (str): the lab changes the code
    """
    if not lab == 'none':
        gsr_port.setData(eeg_trigger)
        core.wait(0.01)
        gsr_port.setData(0)
    else:
        print(eeg_trigger)
        trigger_time_list.append([core.getTime(),eeg_trigger])


def selectEEGStimulusTrigger(pos,seq):
    """
    distinguish EEG trigger for stimulus
    Parameters:
        pos (int): the position of the stimulus
        seq (int): the order of the stimulus
    Returns:
        eeg_stim_trigger (int): code to send to the EEG computer
    """
    eeg_stim_trigger = int((pos+1)*10 + (seq+1))

    return eeg_stim_trigger


#just setting up the EEG
if lab == 'actichamp':
    gsr_port = parallel.ParallelPort(address=0xCFB8)
elif lab == 'biosemi':
    gsr_port = parallel.ParallelPort(address=0x3FB8)


####################################################
#Eye-tracker set-up
####################################################
# Step 1: Connect to the EyeLink Host PC

edf_file = 'pp_' + str(pp_id) + '.EDF' #init datafile (max 8 characters)

if eye_tracking:
    try:
        el_tracker = pylink.EyeLink("100.1.1.1")
    except RuntimeError as error:
        print('ERROR:', error)
        core.quit()
        sys.exit()


    # Step 2: Open an EDF data file on the Host PC
    try:
        el_tracker.openDataFile(edf_file)
    except RuntimeError as err:
        print('ERROR:', err)
        # close the link if we have one open
        if el_tracker.isConnected():
            el_tracker.close()
        core.quit()
        sys.exit()

    el_tracker.sendCommand("add_file_preamble_text 'Predatt Experiment'") #add personalized data file header (preamble text)

    # Step 3: Configure the tracker
    #
    # Put the tracker in offline mode before we change tracking parameters
    el_tracker.setOfflineMode()

    # Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
    # 5-EyeLink 1000 Plus, 6-Portable DUO
    eyelink_ver = 0  # set version to 0, in case running in Dummy mode
    if eye_tracking:
        vstr = el_tracker.getTrackerVersionString()
        eyelink_ver = int(vstr.split()[-1].split('.')[0])
        # print out some version info in the shell
        print('Running experiment on %s, version %d' % (vstr, eyelink_ver))

    # File and Link data control
    # what eye events to save in the EDF file, include everything by default
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # what eye events to make available over the link, include everything by default
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    # what sample data to save in the EDF data file and to make available
    # over the link, include the 'HTARGET' flag to save head target sticker
    # data for supported eye trackers
    if eyelink_ver > 3:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
    el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
    el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
    el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

    el_tracker.sendCommand("sample_rate 1000") #250, 500, 1000, or 2000 (only for EyeLink 1000 plus)
    el_tracker.sendCommand("recording_parse_type = GAZE")
    el_tracker.sendCommand("select_parser_configuration 0") #saccade detection thresholds: 0-> standard/coginitve, 1-> sensitive/psychophysiological
    el_tracker.sendCommand("calibration_type = HV9") #13 point calibration (recommended for head free remote mode)

    # Step 4: set up a graphics environment for calibration

    # get the native screen resolution used by PsychoPy
    scn_width, scn_height = win.size

    # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
    # see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)

    # Write a DISPLAY_COORDS message to the EDF file
    # Data Viewer needs this piece of info for proper visualization, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendMessage(dv_coords)

    # Configure a graphics environment (genv) for tracker calibration
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
    print(genv)  # print out the version number of the CoreGraphics library

    # Set background and foreground colors for the calibration target
    # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
    foreground_color = (1, 1, 1)
    background_color = win.color
    genv.setCalibrationColors(foreground_color, background_color)
    
    # Set up the calibration target
    # Use the default calibration target ('circle')
    genv.setTargetType('circle')

    # Configure the size of the calibration target (in pixels)
    # this option applies only to "circle" and "spiral" targets
    genv.setTargetSize(24)

    # Beeps to play during calibration, validation and drift correction
    # parameters: target, good, error
    #     target -- sound to play when target moves
    #     good -- sound to play on successful operation
    #     error -- sound to play on failure or interruption
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    genv.setCalibrationSounds('', '', '')

    # Request Pylink to use the PsychoPy window we opened above for calibration
    pylink.openGraphicsEx(genv)
        

# Eye-tracker termination function
def terminate_task():
    """ Terminate the task gracefully and retrieve the EDF data file

    file_to_retrieve: The EDF on the Host that we would like to download
    win: the current window used by the experimental script
    """
    el_tracker = pylink.getEYELINK()
    if el_tracker.isConnected():
        # Terminate the current trial first if the task terminated prematurely
        error = el_tracker.isRecording()
        if error == pylink.TRIAL_OK:
            el_tracker = pylink.getEYELINK()
            # Stop recording
            if el_tracker.isRecording():
                # add 100 ms to catch final trial events
                pylink.pumpDelay(100)
                el_tracker.stopRecording()
        # Put tracker in Offline mode
        el_tracker.setOfflineMode()
        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        pylink.msecDelay(500)
        # Close the edf data file on the Host
        el_tracker.closeDataFile()
        # Show a file transfer message on the screen
        message.text = 'EDF data is transfering from EyeLink Host PC'
        message.draw()
        win.flip()
        pylink.pumpDelay(500)
        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        local_edf = os.path.join(session_folder, session_identifier + '.EDF')
        try:
            el_tracker.receiveDataFile(edf_file, local_edf)
        except RuntimeError as error:
            print('ERROR:', error)

        # Close the link to the tracker.
        el_tracker.close()

def checkGazeOnFix():
    # Here we implement a gaze trigger, so the target only comes up when
    # the subject direct gaze to the fixation cross
    # determine which eye(s) is/are available
    # 0- left, 1-right, 2-binocular
    eye_used = el_tracker.eyeAvailable()
    new_sample = None
    old_sample = None
    trigger_fired = False
    in_hit_region = False
    should_recali = 'no'
    trigger_start_time = core.getTime()
    # fire the trigger following a 300-ms gaze
    minimum_duration = 0.1
    gaze_start = -1
    while not trigger_fired:
        # abort the current trial if the tracker is no longer recording
        error = el_tracker.isRecording()
        if error is not pylink.TRIAL_OK:
            el_tracker.sendMessage('tracker_disconnected')
            return error

        # if the trigger did not fire in 30 seconds, abort trial
        if core.getTime() - trigger_start_time >= 10.0:
            el_tracker.sendMessage('trigger_timeout_recal')
            # re-calibrate before trial
            should_recali = 'yes'
            return should_recali

        # Do we have a sample in the sample buffer?
        # and does it differ from the one we've seen before?
        new_sample = el_tracker.getNewestSample()
        if new_sample is not None:
            if old_sample is not None:
                if new_sample.getTime() != old_sample.getTime():
                    # check if the new sample has data for the eye
                    # currently being tracked; if so, we retrieve the current
                    # gaze position and PPD (how many pixels correspond to 1
                    # deg of visual angle, at the current gaze position)
                    if eye_used == 1 and new_sample.isRightSample():
                        g_x, g_y = new_sample.getRightEye().getGaze()
                    if eye_used == 0 and new_sample.isLeftSample():
                        g_x, g_y = new_sample.getLeftEye().getGaze()

                    # break the while loop if the current gaze position is
                    # in a 100 x 100 pixels region around the screen centered
                    fix_x, fix_y = (scn_width/2.0, scn_height/2.0)
                    if fabs(g_x - fix_x) < 50 and fabs(g_y - fix_y) < 50:
                        # record gaze start time
                        if not in_hit_region:
                            if gaze_start == -1:
                                gaze_start = core.getTime()
                                in_hit_region = True
                        # check the gaze duration and fire
                        if in_hit_region:
                            gaze_dur = core.getTime() - gaze_start
                            if gaze_dur > minimum_duration:
                                trigger_fired = True
                    else:  # gaze outside the hit region, reset variables
                        in_hit_region = False
                        gaze_start = -1

            # update the "old_sample"
            old_sample = new_sample
    return should_recali

def calibrationProcedure():
    if eye_tracking:
            cross.autoDraw = False
            message.text = eye_tracking_instr[language] #show calibration message
            message.draw()
            win.flip()
            try:
                el_tracker.doTrackerSetup()
            except RuntimeError as err:
                print('ERROR:', err)
                el_tracker.exitCalibration() #calibrate the tracker #once you are happy with the calibration and validation (!), you are ready to run the experiment. 

            el_tracker.setOfflineMode() #this is called before start_recording() to make sure the eye tracker has enough time to switch modes (to start recording)
            pylink.pumpDelay(100)
            #starts the EyeLink tracker recording, sets up link for data reception if enabled.
            el_tracker.startRecording(1,1,1,1) 
            # The 1,1,1,1 just has to do with whether samples and events etcetera needs to be written to EDF file. Recording needs to be started for each block
            pylink.pumpDelay(100) #wait for 100 ms to cache some samples
            displayMessage(space_instr[language])

def gazeCheck():
    if eye_tracking:
        el_tracker.sendMessage('TRIALID %d' % (trial_count)) #send a message ("TRIALID") to mark the start of a trial
        el_tracker.sendCommand("record_status_message 'trial %s block %s'" % (trial_count,block_count)) #to show the current task, block nr and trial nr #+1 because Python starts at 0
        # Check if gaze is on fixation and if not start recallibration
        should_recal = checkGazeOnFix()
        if should_recal == 'yes':
            recalibrated[trial_index] = 1
            eegTriggerSend(int(254),lab=lab) # 201 is the stop-recording command in the biosemi config file
            calibrationProcedure()
            cross.autoDraw =True
            eegTriggerSend(int(253),lab=lab) # 200 is the start-recording command in the biosemi config file 


####################################################
#Experiment value initialization
####################################################

# Condition mapping
condition_map = ['rotation','angle']
rot_map = ['clockwise','anticlockwise']
key_map = [['d','k'],['k','d']]

# Counterbalancing and key-mappping
subject_code = participantCounterBalance(participant_number=pp_id)  
if mode == 'test':
    subject_code = [0,0,0,1]
rotation_odd = rot_map[subject_code[0]] # index 0 idicate which direction is odd
angle_odd = subject_code[1] # index 1 indicates which angle is odd, we go straight here because it's easier to referenc angle_set
rotation_keys = key_map[subject_code[2]] # index 2 indicates which keys are paired to the directions
angle_keys = key_map[subject_code[3]] # index 3 indicates which keys are paired to the angles

key_mappings = [rotation_keys,angle_keys]
key_map_dict = {rot_map[0]:rotation_keys[0],rot_map[1]:rotation_keys[1],
                ang_map[0]:angle_keys[0],ang_map[1]:angle_keys[1]}

# Generate main stimuli
grid = generateStimCoordinates(gridcol=12, gridrow=10, jitter=linejitter_arr)
stimset = generateStim(linelength=35,linewidth=2, coord_array=grid,
                        size=276, fixdistance=134,angles=angle_set)
# Generate block-level conditions
block_condition = generateBlockLevels(n_blocks)
# Generate trial-level conditions per block
block_rot_pred = []
block_angle_pred = []
trial_starts = []
target_trials = []
trial_timings = []
# Experiment wide lists
trial_list = [{'trial_index':i} for i in range(n_blocks*n_trials)] # for trialhandler
recalibrated = np.zeros(n_blocks*n_trials)

for i in range(n_blocks):
    block_rot_pred.append(generatePredictionList(tr_block=n_trials,n_odd=n_odd,
                                            odd=subject_code[0],mode='rotation'))
    block_angle_pred.append(generatePredictionList(tr_block=n_trials,n_odd=n_odd,
                                            odd=subject_code[1],mode='angle'))
    trial_starts.append(generateTrialStarts(tr_block=n_trials,bad_quadrant=avoid_quadrant))
    target_trials.append(generateTargetTrials(tr_block=n_trials,ntarget=n_target))
    trial_timings.append(generateTrialTimings(tr_block=n_trials,isi_dur=isi_duration,
                                        jitter=stim_onset_jitter))

# ExperimentHandler and TrialHandler
trials = data.TrialHandler(trialList = trial_list, nReps=1, method = 'sequential')
if mode == 'default':
    this_exp = data.ExperimentHandler(dataFileName = file_name)
    # this_exp = data.ExperimentHandler(dataFileName = os.getcwd() + '/data/' + 'pilot_predatt_participant_test')
    this_exp.addLoop(trials)

# Initilize counters
trial_clock = core.Clock() #define trial clock
exp_clock = core.Clock() #define experiment clock
trial_index = 0
trial_count = 1
block_count = 1
hits = 0
incorrect = 0
misses = 0
should_recal = 'no'

####################################################
#Experiment loop
####################################################

# Intro message
intro_message = start_instruction[language]
displayMessage(intro_message)

mainstr_message = main_instruction[language]
displayMessage(mainstr_message)

stimset[0,0].draw()
stimset[1,1].draw()
win.flip()
start_key = event.waitKeys(keyList = ['space','escape'])

# Start eye-tracking and calibrate
calibrationProcedure()
# Block loop
for id in range(n_blocks):
    cross.autoDraw = False
    # Inter-block messages: score, task and prediction cue
    displayMessage(block_msg=True, lang = language,
                    block_num= block_count, 
                    hits=hits , misses=misses, 
                    wrong= incorrect, break_blocks=break_blocks)
    hits = 0 #reset
    incorrect = 0
    misses = 0
    # Start eye-tracker and if it's a long break calibrate
    if block_count in break_blocks:
        calibrationProcedure()
    else:
        if eye_tracking:
            el_tracker.setOfflineMode() #this is called before start_recording() to make sure the eye tracker has enough time to switch modes (to start recording)
            pylink.pumpDelay(100)
            #starts the EyeLink tracker recording, sets up link for data reception if enabled.
            el_tracker.startRecording(1,1,1,1) 
            # The 1,1,1,1 just has to do with whether samples and events etcetera needs to be written to EDF file. Recording needs to be started for each block
            pylink.pumpDelay(100) #wait for 100 ms to cache some samples]
    displayCondInstruction(cond=block_condition[id],key_map=key_mappings,lang=language)
    displayBlockCue(cond=block_condition[id],rot_odd=rotation_odd,ang_odd=angle_odd,lang=language)
    cross.autoDraw = True
    eegTriggerSend(int(253),lab=lab) # 200 is the start-recording command in the biosemi config file
    # Trigger for block
    block_tigger = int(60 + n_blocks)
    eegTriggerSend(block_tigger,lab=lab)
    # Trial loop
    for i in range(n_trials):
        cross.autoDraw = True
        win.flip()
        trial_clock.reset() #start rt timing

        stimulus_times,trial_stamp,triggers,stimpos = stimPresentation(stimulus=stimset,stim_dur=stim_duration,isi_dur=trial_timings[id][i],
                                                                       iti_dur=iti_duration,start_quad=trial_starts[id][i],direction=block_rot_pred[id][i],
                                                                       q_target=target_trials[id][i],angles=block_angle_pred[id][i:i+4])
        keys = event.getKeys(keyList= ['d','k','escape'],timeStamped=trial_clock)
        print(keys)
        t_trial = trial_clock.getTime()*1000
        accuracy, reaction_time = evaluateResponse(stim_times=stimulus_times,target=target_trials[id][i],
                                                   cond=block_condition[id],direction=block_rot_pred[id][i],
                                                   angles=block_angle_pred[id][i:i+4],keys_mapped=key_mappings,
                                                   key=keys, rt_limit = 1.0)
        if accuracy == 'correct': hits+= 1
        if accuracy == 'miss': misses+= 1
        if accuracy == 'false_fire': incorrect+= 1
        if accuracy == 'incorrect': incorrect+= 1
        if accuracy == 'too_slow': incorrect+= 1

        # Evaluate rotation prediction
        rot_prediciton = 'regular'
        if rot_map[block_rot_pred[id][i]] == rotation_odd:
            rot_prediciton = 'odd'

        # Store data
        for ix in range(4): # for every stimulus
            trials.addData('LocalTime_DDMMYY_HMS', 
                        str(time.localtime()[2]) + '/' + str(time.localtime()[1]) + '/' + str(time.localtime()[0]) 
                        + '_' + str(time.localtime()[3]) + ':' + str(time.localtime()[4]) + ':' + str(time.localtime()[5])) #HMS = hour min sec
            trials.addData('lab', lab)
            trials.addData('mode', mode)
            trials.addData('eye_tracking', eye_tracking)
            trials.addData('participant', pp_id)
            trials.addData('gender', info['Gender'])
            trials.addData('age', info['Age'])
            trials.addData('handed', info['Dominant hand'])
            trials.addData('intruct_lang', info['Language'])
            trials.addData('located_quad', info['Localised Quadrant'])
            trials.addData('trial', (trial_count)) # Python starts indexing at 0
            trials.addData('block',block_count)
            trials.addData('start_position',trial_starts[id][i])
            trials.addData('rotation_odd', rotation_odd)
            trials.addData('clockwise_key',key_map_dict['clockwise'])
            trials.addData('anticlockwise_key',key_map_dict['anticlockwise'])
            trials.addData('angle_odd', angle_odd)
            trials.addData(f'angle_{ang_map[0]}_key',key_map_dict[f'{ang_map[0]}'])
            trials.addData(f'angle_{ang_map[1]}_key',key_map_dict[f'{ang_map[1]}'])
            trials.addData('trial_direction',rot_map[block_rot_pred[id][i]])
            trials.addData('angle',ang_map[block_angle_pred[id][i:i+4][ix]])
            trials.addData('target_number',target_trials[id][i])
            trials.addData('target_trial',int(target_trials[id][i]==ix & ix > 0))
            trials.addData('t_trial',t_trial)
            trials.addData('experiment_time_s',exp_clock.getTime())
            trials.addData('t_stim',stimulus_times[ix])
            trials.addData('position',stimpos[ix])
            trials.addData('sequence',ix)
            trials.addData('eeg_trigger',triggers[ix])
            trials.addData('key_data',keys)
            # Evaluate rotation prediction
            ang_prediciton = 'regular'
            if block_angle_pred[id][i:i+4][ix] == angle_odd:
                ang_prediciton = 'odd'
            trials.addData('rotation_prediction',rot_prediciton)
            trials.addData('angle_prediction',ang_prediciton)
            trials.addData('task',condition_map[block_condition[id]])
            if target_trials[id][i]==ix & ix > 0:
                trials.addData('accuracy',accuracy)
                trials.addData('rt',reaction_time)
            else:
                trials.addData('accuracy','correct_nogo')
                trials.addData('rt',None)
            if not mode == 'test':this_exp.nextEntry()
        # Add to counters
        trial_count+= 1
        trial_index+= 1
        # Terminate if escape is pressed
        print(keys)
        if keys:
            if keys[-1][0] == 'escape':
                print(trigger_time_list)
                if eye_tracking:
                    terminate_task()
                win.close()
                core.quit()
    block_count+= 1
    # Pause recordings
    eegTriggerSend(int(254),lab=lab) # 200 is the start-recording command in the biosemi config file
    if eye_tracking:
        el_tracker.stopRecording() #this is typically done for each bloc

# Disconnect, download the EDF file, then terminate the task
if eye_tracking:
    terminate_task()
    
win.close()
core.quit()