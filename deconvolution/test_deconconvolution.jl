using CSV
using DataFrames
using Effects
using Unfold
using PyMNE
using StatsModels



# --- Make paths --- 
destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/main/"
data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/"
event_path = data_path * "mastoid-raw-csv/512Hz/events/"
event_dir_list = readdir(event_path)

mkpath(destination_path)

# --- Load events ---
# --- Get subject from Worker parameter ---
subject = 4
subject_num = subject_num = lpad(subject,2,"0")

event_dir_list = readdir(event_path)
evts = DataFrame(CSV.File(event_path*"events-sub-$subject_num.csv"))
rename!(evts,:sample => :latency)
filter!(row -> !(row.event_codes == 99),evts)
evts.position = string.(evts.position)
evts.sequence = string.(evts.sequence)
evts.feature = string.(evts.feature)
evts.attended_feature = string.(evts.attended_feature)
evts.unattended_feature = string.(evts.unattended_feature)

evts.visual_field = ifelse.(evts.position .∈ Ref(["3", "4"]), "down", "up")
# --- Load .fif ---
raw_path = data_path*"mastoid-raw/clean-mastoid-$subject_num-raw.fif"
py_data = PyMNE.io.read_raw_fif(raw_path, preload=true)
data = py_data.get_data()
data = Array(PyArray(data))

# --- Basis, formula, contrasts ---
basisfunction = firbasis(τ=(-0.1,1),sfreq=512,name="myFIRbasis")
f = @formula 0 ~ 1 + sequence + position*feature*attended_feature*unattended_feature
# f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
bfDict = [Any=>(f,basisfunction)]

# Specify contrasts
contrasts = Dict(
        :position               =>EffectsCoding(),
        :sequence               =>EffectsCoding(),
        :feature                =>EffectsCoding(),
        :attended_feature       =>EffectsCoding(),
        :unattended_feature     =>EffectsCoding()
)

# --- Fit ---
@time m = fit(UnfoldModel,bfDict,evts,data,contrasts=contrasts)

# --- Effects ---
setup = string(evts[1,:setup])
setdown = string(evts[1,:setdown])
        
design = Dict(
        :sequence           =>["1","2","3","4"],
        :position           => ["1","2","3","4"],
        :feature            => ["angle","rotation"],
        :attended_feature   => ["regular","odd"],
        :unattended_feature => ["regular","odd"]
)

println("effects sub $(subject_num)")
eff = effects(design,m)
eff.subject .= string(evts[1,:subject])
# Give back the channel names
ch_names = pyconvert(Vector{String}, py_data.ch_names)
eff[!,:channel] = [ch_names[num] for num in eff[!, :channel]]

# --- Save ---
filename = "corrected-evoked-all-sub-$subject_num.csv"
m_filename = "rERP-ch-all-sub-$subject_num.jld2"
CSV.write(destination_path*filename, eff)
save(joinpath(destination_path, m_filename), m; compress = true);

