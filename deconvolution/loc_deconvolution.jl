using Unfold
using CSV
using DataFrames
using Effects
using StatsModels

for i in el_list
    data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/localiser/mastoid-raw-csv/"
    raw_path = data_path * "raw-$i/"
    destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/localiser/$i/"
    # destination_path = "C:/Users/mvmigem/Documents/data/project_1/overlap_corrected/seq-1-p3/$i/" # for seq 1 p3 analysis
    if !isdir(destination_path)
        mkdir(destination_path)
        # Data paths
        event_path = data_path * "events/"

        event_dir_list = readdir(event_path)
        raw_dir_list = readdir(raw_path)

        for (evp,rawp) in zip(event_dir_list,raw_dir_list)
            # Read in the data
            data = DataFrame(CSV.File(raw_path*rawp))
            evts = DataFrame(CSV.File(event_path*evp))
            # Change the column names to fit toolbox
            rename!(evts,:sample => :latency)
            evts.position = string.(evts.position)
            
            select!(data,i)
            # Transform to data to Matrix
            data_r = vec(Matrix(data))
            # Define basisfunction
            basisfunction = firbasis(τ=(-0.1,1),sfreq=512,name="myFIRbasis")
            # Define the linear formula 
            f = @formula 0 ~ 1 + position
            # f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
            bfDict = Dict(Any=>(f,basisfunction))
            # Specify contrasts
            contrasts = Dict(:position=>EffectsCoding())
            # Fit
            m = fit(UnfoldModel,bfDict,evts,data_r,contrasts=contrasts)
            
            design = Dict(:position => ["1","2","3","4"])
            eff = effects(design,m)
            eff.subject .= string(evts[1,:subject])
            eff.selected_electrode .= i
            # Save evoked
            subject_num = lpad(evts[1,:subject],2,"0")
            filename = "corrected-$(i)-loc_evoked-$subject_num.csv"
            CSV.write(destination_path*filename, eff)

        end
    end
end