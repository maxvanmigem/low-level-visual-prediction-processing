using CSV
using DataFrames
using Effects
using Unfold
using PyMNE
using StatsModels
sub = 1
subject_num = lpad(sub,2,"0")
data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/"
event_path = data_path * "mastoid-raw-csv/512Hz/events/"
event_dir_list = readdir(event_path)
evts = DataFrame(CSV.File(event_path*"events-sub-$subject_num.csv"))

raw_path = data_path*"mastoid-raw/clean-mastoid-$subject_num-raw.fif"
py_data = PyMNE.io.read_raw_fif(raw_path)
data = py_data.get_data()
data = Array(PyArray(data))

# data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/mastoid-raw-csv/512Hz/"
# raw_path = data_path * "raw-POz/"
# destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/main/POz/"
# data = DataFrame(CSV.File(raw_path*"raw-mastoid-POz-$subject_num.csv"))
# select!(data,"POz")
# data_r = vec(Matrix(data))

rename!(evts,:sample => :latency)
filter!(row -> !(row.event_codes == 99),evts)
evts.position = string.(evts.position)
evts.sequence = string.(evts.sequence)
evts.feature = string.(evts.feature)
evts.attended_feature = string.(evts.attended_feature)
evts.unattended_feature = string.(evts.unattended_feature)

basisfunction = firbasis(τ=(-0.1,1),sfreq=512,name="myFIRbasis")
f = @formula 0 ~ 1 + sequence + position + feature*attended_feature*unattended_feature
# f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
bfDict = [Any=>(f,basisfunction)]
# Specify contrasts
contrasts = Dict(:position=>EffectsCoding(),
                 :sequence=>EffectsCoding(),
                 :feature=>EffectsCoding(),
                 :attended_feature=>EffectsCoding(),
                 :unattended_feature=>EffectsCoding())

@time m = fit(UnfoldModel,bfDict,evts,data,contrasts=contrasts)
        
setup = string(evts[1,:setup])
setdown = string(evts[1,:setdown])
        
design = Dict(:sequence =>["1","2","3","4"],
                :position => ["1","2","3","4"],
                :feature => ["angle","rotation"],
                :attended_feature => ["regular","odd"],
                :unattended_feature => ["regular","odd"])
println("effects sub $(subject_num)")
eff = effects(design,m)
eff.subject .= string(evts[1,:subject])
# Give back the channel names
ch_names = pyconvert(Vector{String}, py_data.ch_names)
eff[!,:channel] = [ch_names[num] for num in eff[!, :channel]]

# Save effects and model
destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/64-ch/"

filename = "corrected-evoked-all-sub-$subject_num.csv"
m_filename = "rERP-ch-all-sub-$subject_num.jld2"
CSV.write(destination_path*filename, eff)
save(joinpath(destination_path, m_filename), m; compress = true);

pp_efficient = [2,7,9,26,28,29]
pp_trouble

