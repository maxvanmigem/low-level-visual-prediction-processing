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

mode = 'default'   #'default'/'test'

eye_tracking = False #True/False

if eye_tracking:
    from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy #this are functions used to run the eyetracker calibration and validation

#options
n_trials = 4 # per block
n_odd = 1  # per block
n_target = 2 # per block

n_blocks = 4  # in total      


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

# images to show rotation direction
anticlockwise_path = os.getcwd()+'/anticlockwise_arrow.png'
clockwise_path = os.getcwd()+'/clockwise_arrow.png'

####################################################
# Dialogue box
####################################################


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

language = 0 # default
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
target_colour = 'red'
test_instruction = ('Test')
start_instruction = [('Welcome and thank you for participating in this experiment.\n\n' + 
                     'Please press SPACE to continue.'),
                     ('Welkom en bedankt om deel te nemen aan dit experiment.\n\n' +
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


def generateStim(linelength, linewidth ,coord_array, size, fixdistance, slant_angle):
    """ 
    Generate an ElementArrayStim object consisting of lines on the coordinates 
    for stimulus for each quadrant position and with differently angled lines

    Parmeters:
        linelength (int): length of individual lines (pix but can be any unit)
        linewidth (int): width of individual lines (pix but can be any unit)
        coord_array (ndarray): set of x and y coords for de sub elements
        size (int or float): scaling factor
        fixdistance (int or float): distance of stimulus corner to screen center
        slant_angle (int): angle of the stimuli, two sets are generated: this angle and its complement 
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
    line_stimuli = np.empty((2,sections), dtype=object)   # 2 types (0 is left slanted, 1 is right slanted ) and 4 quadrants
 
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
        # Left slanted stimuli
        line_stimuli[0,quad] = visual.ElementArrayStim(win, units='pix',elementTex=None, elementMask='sqr', xys= xys, oris = 360-slant_angle,
                                           nElements=n_lines, sizes=sizes, colors=(1.0, 1.0, 1.0), colorSpace='rgb')
        # Right slanted stimuli
        line_stimuli[1,quad] = visual.ElementArrayStim(win, units='pix',elementTex=None, elementMask='sqr', xys= xys, oris = slant_angle,
                                           nElements=n_lines, sizes=sizes, colors=(1.0, 1.0, 1.0), colorSpace='rgb')

    return line_stimuli


####################################################
#Trial display functions
####################################################

def drawStim(line_stimuli, quad, slant):
    """ 
    Draws the stimuli in the correct quadrant
    Parmeters:
        line_stimuli (ndarray): array with psychopy ElementArrayStim objects for every position and slant
        quad (int): quadrant 0,1,2 or 3
        slant (0 or 1): left slanted (0) or right slanted (1)
    """
    # Select the stimulus for the quadrant and slant
    line_stim = line_stimuli[slant,quad]

    # Draw 
    line_stim.draw()


def stimPresentation(stimulus, stim_dur, isi_dur,iti_dur, start_quad, direction, q_target, slant, lab=lab): 
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
        slant (list): of 1 and 0 left slanted (0) or right slanted (1)
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
        if target_ls[i]:
            cross.color = target_colour 
        # Implemenent a target trial
        trigger = int(selectEEGStimulusTrigger(stimpos,pos=i)) # EEG trigger generation
        triggers.append(trigger)
        drawStim(stimulus,stimpos,slant[i])
        wait = isi_dur[i]-stim_clock.getTime() # Drawing the stimulus takes time, this compensates that
        core.wait(wait)
        stim_timing =trial_clock.getTime()*1000
        win.flip()
        eegTriggerSend(trigger,lab) # Send trigger
        core.wait(stim_dur)
        win.flip()
        cross.color = cross_standard_col
        print(stim_timing)
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


def displayCondInstruction(cond, key_map, lang=0):
    """ 
    Function for displaying block task
    Parameters:
        cond (int): condition 0 -> rotation task, 1 -> angle task
        key_map (dict): key mappings
        lang (int): instruction 0 -> eng, 1 -> dutch 
    """
    left_instr = visual.TextStim(win, text=press_d_instr[lang],pos=(-200,-150),height= 30) 
    right_instr = visual.TextStim(win, text=press_k_instr[lang],pos=(200,-150),height= 30) 
    bottom_instr = visual.TextStim(win, text=space_instr[lang],pos=(0,-280),height= 30) 

    if key_map['clockwise'] == 'd':
        clock_wpos = (-200,-30)
        anticlock_wpos = (200,-30)
    else:
        clock_wpos = (200,-30)
        anticlock_wpos = (-200,-30)

    if key_map['left'] == 'd':
        left_wpos = (-200,-30)
        right_wpos = (200,-30)
    else:
        left_wpos = (200,-30)
        right_wpos = (-200,-30)
 
    if cond:
        top_instr = visual.TextStim(win, text=stim_rotation_instr[lang],pos=(0,200),height= 30) 
        cond_im_1 = visual.ImageStim(win,image=clockwise_path,units='pix',pos=clock_wpos,size=200)
        cond_im_2 = visual.ImageStim(win,image=anticlockwise_path,units='pix',pos=anticlock_wpos,size=200)
    else:
        top_instr = visual.TextStim(win, text=stim_angle_instr[lang],pos=(0,200),height= 30) 
        cond_im_1 = visual.Rect(win,width=120,height=20,fillColor ='white',units='pix',pos=left_wpos,ori=45)
        cond_im_2 = visual.Rect(win,width=120,height=20,fillColor ='white',units='pix',pos=right_wpos,ori=315)

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

def displayBlockCue(cond, rot_odd, ang_odd, lang=0):
    """ 
    Function for displaying block cue
    Parameters:
        cond (int): condition 0 -> rotation task, 1 -> angle task
        rot_odd (str): indicates which direction is odd
        ang_odd (str): indicates which angle is odd
        lang (int): instruction 0 -> eng, 1 -> dutch 
    """
    bottom_instr = visual.TextStim(win, text=space_instr[lang],pos=(0,-280),height= 30) 
    if cond:
        top_instr = visual.TextStim(win, text=cue_angle_instr[lang],pos=(0,200),height= 30)
        cond_im = visual.ImageStim(win,image=clockwise_path,units='pix',pos=(0,-100),size=250)
        if rot_odd == 'clockwise': # it's flipped because the cue indicates the majority
            cond_im.image = anticlockwise_path
    else:
        top_instr = visual.TextStim(win, text=cue_rotation_instr[lang],pos=(0,200),height= 30)
        cond_im = visual.Rect(win,width=120,height=20,fillColor ='white',units='pix',pos=(0,-100),ori=315)
        if ang_odd == 'left': # it's flipped because the cue indicates the majority
            cond_im.ori = 45

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
        cond_list (ndarray): array of length nblocks with equal amounts 1's and 0's 
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
#External measurement instruments
####################################################

def eegTriggerSend(eeg_trigger, lab): #need to elaborate
    """
    Sends trigger to EEG recording
    """
    if not lab == 'none':
        gsr_port.setData(eeg_trigger)
        core.wait(0.01)
        gsr_port.setData(0)
    else:
        print(eeg_trigger)
        trigger_time_list.append([core.getTime(),eeg_trigger])


def selectEEGStimulusTrigger(start,pos):
    """
    distinguish EEG trigger for stimulus
    """
    eeg_stim_trigger = int((start+1)*10 + (pos+1))

    return eeg_stim_trigger


#just setting up the EEG
if lab == 'actichamp':
    gsr_port = parallel.ParallelPort(address=0xCFB8)
elif lab == 'biosemi':
    gsr_port = parallel.ParallelPort(address=0x3FB8)


####################################################
#Experiment value initialization
####################################################

# Condition mapping
rotodd_map = ['clockwise','anticlockwise']
angodd_map = ['left','right']
key_map = [['k','d'],['d','k']]
position_map = ['top_left','top_right','bottom_right','bottom_left']

# Counterbalancing and key-mappping
subject_code = participantCounterBalance(2)  
rotation_odd = rotodd_map[subject_code[0]] # index 0 idicate which direction is odd
angle_odd = angodd_map[subject_code[1]] # index 1 indicates which angle is odd
rotation_keys = key_map[subject_code[2]] # index 2 indicates which keys are paired to the directions
angle_keys = key_map[subject_code[3]] # index 3 indicates which keys are paired to the angles

key_mappings = {rotodd_map[0]:rotation_keys[0],rotodd_map[1]:rotation_keys[1],
                angodd_map[0]:angle_keys[0],angodd_map[1]:angle_keys[1]}

# Generate main stimuli
grid = generateStimCoordinates(gridcol=12, gridrow=10, jitter=linejitter_arr)
stimset = generateStim(linelength=35,linewidth=2, coord_array=grid,
                        size=276, fixdistance=134,slant_angle=45)
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
    trial_starts.append(generateTrialStarts(tr_block=n_trials,bad_quadrant=0))
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
n_correct = 0
point_counter = 0
trial_count = 1
block_count = 1
hits = 0
misses = 0
false_fire = 0
should_recal = 'no'

####################################################
#Experiment loop
####################################################

# Intro message
intro_message = start_instruction[language]
displayMessage(intro_message)

# Block loop
for id in range(n_blocks):
    cross.autoDraw = False
    # Inter-block messages: score, task and prediction cue
    displayMessage(block_msg=True, lang = language,
                    block_num= id+1, 
                    hits=hits , misses=misses, 
                    wrong= false_fire, break_blocks=[0,2])
    displayCondInstruction(cond=block_condition[id],key_map=key_mappings,lang=language)
    displayBlockCue(cond=block_condition[id],rot_odd=rotation_odd,ang_odd=angle_odd,lang=language)
    # Trial loop
    for i in range(n_trials): 
        cross.autoDraw = True
        win.flip()
        trial_clock.reset() #start rt timing
        stimulus_times,trial_stamp,triggers,stimpos = stimPresentation(stimulus=stimset,stim_dur=stim_duration,isi_dur=trial_timings[id][i],
                                                                       iti_dur=iti_duration,start_quad=trial_starts[id][i],direction=block_rot_pred[id][i],
                                                                       q_target=target_trials[id][i],slant=block_angle_pred[id][i:i+4])
        event.clearEvents(eventType = 'keyboard')
        keys = event.getKeys(timeStamped=trial_clock)
        print(keys)
        t_trial = trial_clock.getTime()*1000

        # Store data
        for ix in range(4):
            trials.addData('LocalTime_DDMMYY_HMS', 
                        str(time.localtime()[2]) + '/' + str(time.localtime()[1]) + '/' + str(time.localtime()[0]) 
                        + '_' + str(time.localtime()[3]) + ':' + str(time.localtime()[4]) + ':' + str(time.localtime()[5])) #HMS = hour min sec
            trials.addData('lab', lab)
            trials.addData('mode', mode)
            trials.addData('eye_tracking', eye_tracking)
            trials.addData('participant', 'test')
            trials.addData('gender', info['Gender'])
            trials.addData('age', info['Age'])
            trials.addData('handed', info['Dominant hand'])
            trials.addData('intruct_lang', info['Language'])
            # trials.addData('loc_quad', )
            trials.addData('trial', (trial_count)) # Python starts indexing at 0
            trials.addData('start_position',trial_starts[id][i])
            trials.addData('rotation_odd', rotation_odd)
            trials.addData('angle_odd', angle_odd)
            trials.addData('angle',angodd_map[block_angle_pred[id][i:i+4][ix]])
            trials.addData('trial_direction',rotodd_map[block_rot_pred[id][i]])
            trials.addData('catch_trial',target_trials[id][i])
            trials.addData('t_stim',stimulus_times[ix])
            trials.addData('position',position_map[stimpos[ix]])
            trials.addData('sequence',ix)
            trials.addData('eeg_trigger',triggers[ix])
            trials.addData('experiment_time_s',exp_clock.getTime())
            trials.addData('t_trial',t_trial)
            trials.addData('block',block_count)
            if not mode == 'test':this_exp.nextEntry()

        trial_count+= 1
        trial_index+= 1
        # Terminate if escape is pressed
        if len(keys)>= 1:
            if keys[-1][0] == 'escape':
                print(trigger_time_list)
                if eye_tracking:
                    terminate_task()
                win.close()
                core.quit()
    block_count+= 1

win.close()
core.quit()