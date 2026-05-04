# low-level-visual-prediction
Repository for a study on the effects of prediction and attention on early visual processing (C1 component)and subsequent stages of processing (P1, N1, P2, N2 and P3 ERP components) manipulating both at distinct feature levels.
This repositiory contains everything related to this project such as stimulus presentation and behavioural scripts, data processing scripts, deconvolution and statistical analysis scripts.

## Team
Maximilien Van Migem, Daniele Marianzzo and Gilles Pourtois

## Setup & Requirements

### Experiment
Python 3.10.18  
Numpy 1.8.4  
Pandas 2.0.3  
Psychopy 2024.2.1


### Analysis
Python 3.13.5
Numpy 2.2.6
Matplotlib 3.10.5  
mne 1.10.1
Pandas 2.3.1  
Seaborn 0.13.2


Julia 1.11.5  
Unfold  
UnfoldSim  
DataFrames

## Data pipeline
Using the shared bids format data requires some input adjustment to scripts 
However, also makes many scripts obsolete (all data alignment scripts and bids tranform scripts).


1. localiser_prepocessing -> executes basic processing steps for localiser data
2. preprocessing.ipynb -> executes basic prepocessing steps (see mne reports for preprocessing decisions)
3. fif_transform.ipynb -> transforms preprocessed data to csv files for every electrode and particpant
4. deconvolution.jl -> performs linear deconvolution and creates rERPs
5. 
