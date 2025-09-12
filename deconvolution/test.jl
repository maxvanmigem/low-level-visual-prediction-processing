using CSV
using DataFrames
using Effects
using Unfold
using UnfoldSim
using UnfoldMakie,CairoMakie
using StatsModels

data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/mastoid-raw-csv/"
event_path = data_path * "events/"
event_dir_list = readdir(event_path)
evts = DataFrame(CSV.File(event_path*"events-sub-02.csv"))
raw_path = data_path * "raw-POz/"
raw_dir_list = readdir(raw_path)

data = DataFrame(CSV.File(raw_path*raw_dir_list[2]))

rename!(evts,:sample => :latency)
filter!(row -> !(row.event_codes == 99),evts)
evts.position = string.(evts.position)
evts.sequence = string.(evts.sequence)
select!(data,"POz")
data_r = vec(Matrix(data))

basisfunction = firbasis(τ=(-0.1,1),sfreq=512,name="myFIRbasis")
f = @formula 0 ~ 1 + sequence + position*feature*attended_feature*unattended_feature
        # f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
bfDict = [Any=>(f,basisfunction)]
        # Specify contrasts
contrasts = Dict(:position=>EffectsCoding(),
                        :sequence=>EffectsCoding(),
                        :feature=>EffectsCoding(),
                        :attended_feature=>EffectsCoding(),
                        :unattended_feature=>EffectsCoding())

m = fit(UnfoldModel,bfDict,evts,data_r,contrasts=contrasts)

setup = string(evts[1,:setup])
setdown = string(evts[1,:setdown])
        
design = Dict(:sequence =>["1","2","3","4"],
                        :position => [setup,setdown],
                        :feature => ["angle","rotation"],
                        :attended_feature => ["regular","odd"],
                        :unattended_feature => ["regular","odd"])

eff = effects(design,m)
eff.subject .= string(evts[1,:subject])
eff.selected_electrode .= "POz"

pp_efficient = [2,3,4,7,9,10,11,12,13,14,16,17,18,19,20,21,23,25,26,28,29,30,35]