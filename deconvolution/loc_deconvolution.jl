using CSV
using DataFrames
using Effects
using Unfold
using PyMNE
using StatsModels

# Data paths
data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/localiser/"
destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/localiser/"
raw_path = data_path * "mastoid-raw/"
raw_dir_list = readdir(raw_path)
event_path = data_path * "mastoid-raw-csv/events/"
event_dir_list = readdir(event_path)
# Define basisfunction
basisfunction = firbasis(τ=(-0.1,1),sfreq=512,name="myFIRbasis")
# Define the linear formula 
f = @formula 0 ~ 1 + position
# f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
bfDict = [Any=>(f,basisfunction)]

for (evp,rawp) in zip(event_dir_list,raw_dir_list)
    # Read in the data
    # Load MNE fif files with PyMNE 
    py_data = PyMNE.io.read_raw_fif(raw_path*rawp)
    data = py_data.get_data()
    data = Array(PyArray(data))
    # Events
    evts = DataFrame(CSV.File(event_path*evp))
    # Change the column names to fit toolbox
    rename!(evts,:sample => :latency)
    evts.position = string.(evts.position)
    # Specify contrasts
    contrasts = Dict(:position=>EffectsCoding())
    # Fit
    @time m = fit(UnfoldModel,bfDict,evts,data,contrasts=contrasts)
    
    design = Dict(:position => ["1","2","3","4"])
    eff = effects(design,m)
    eff.subject .= string(evts[1,:subject])
    # Save evoked
    subject_num = lpad(evts[1,:subject],2,"0")
    filename = "corrected-loc-$subject_num.csv"
    m_filename = "rERP-loc-$subject_num.jld2"
    # Give back the channel names
    ch_names = pyconvert(Vector{String}, py_data.ch_names)
    eff[!,:channel] = [ch_names[num] for num in eff[!, :channel]]
    # Save effects and model
    CSV.write(destination_path*filename, eff)
    save(joinpath(destination_path, m_filename), m; compress = true);

end

