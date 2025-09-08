using Unfold
using UnfoldSim
using UnfoldMakie,CairoMakie
using CSV
using DataFrames
using Effects
using StatsModels

# el_list = ["Pz","POz","PO4","PO3"] #for P3 analysis of seq 1
el_list = ["Oz","POz","O1","O2",
            "PO3","PO4",
            "P1","Pz","P2",
            "CP1","CPz","CP2",
            ]
for i in el_list
    data_path = "C:/Users/mvmigem/Documents/data/project_2/preprocessed/mastoid-raw-csv/"
    raw_path = data_path * "raw-$i/"
    destination_path = "C:/Users/mvmigem/Documents/data/project_2/overlap_corrected/main/$i/"
    # destination_path = "C:/Users/mvmigem/Documents/data/project_1/overlap_corrected/seq-1-p3/$i/" # for seq 1 p3 analysis
    if !isdir(destination_path)
        mkdir(destination_path)
    end
    # Data paths
    # destination_path = "C:/Users/mvmigem/Documents/data/project_1/overlap_corrected/variable-electrode/"
    event_path = data_path * "events/"
    # raw_path = data_path * "raw-POz/"
    # raw_path = data_path * "raw-selected/"
    

    event_dir_list = readdir(event_path)
    raw_dir_list = readdir(raw_path)

    # data = DataFrame(CSV.File(raw_path*raw_dir_list[1]))
    # evts = DataFrame(CSV.File(event_path*event_dir_list[1]))

    for (evp,rawp) in zip(event_dir_list,raw_dir_list)
        # Read in the data
        data = DataFrame(CSV.File(raw_path*rawp))
        evts = DataFrame(CSV.File(event_path*evp))

        subject_num = lpad(evts[1,:subject],2,"0")
        filename = "corrected_$(i)_evoked_$subject_num.csv"
        if isfile(destination_path*filename)
            continue
        end
        # Change the column names to fit toolbox
        rename!(evts,:sample => :latency)
        filter!(row -> !(row.event_codes == 99),evts)
        evts.position = string.(evts.position)
        evts.sequence = string.(evts.sequence)
        
        # selected electrode

        # selected_electrode = string(evts[1,:selected_electrode])
        select!(data,i)
        # Transform to data to Matrix
        data_r = vec(Matrix(data))
        # Define basisfunction
        basisfunction = firbasis(τ=(-0.1,0.8),sfreq=512,name="myFIRbasis")
        # Define the linear formula 
        f = @formula 0 ~ 1 + sequence + position*feature*attended_feature*unattended_feature
        # f = @formula 0 ~ 1 + condition + continuous # note the formulas left side is `0 ~ ` for technical reasons`
        bfDict = [Any=>(f,basisfunction)]
        # Specify contrasts
        contrasts = Dict(:position=>EffectsCoding(),
                        :sequence=>EffectsCoding(),
                        :feature=>EffectsCoding(),
                        :attended_feature=>EffectsCoding(),
                        :unattended_feature=>EffectsCoding())
        # Fit
        println("fitiing sub $(subject_num) el $(i)")
        m = fit(UnfoldModel,bfDict,evts,data_r,contrasts=contrasts)

        setup = string(evts[1,:setup])
        setdown = string(evts[1,:setdown])
        
        design = Dict(:sequence =>["1","2","3","4"],
                        :position => [setup,setdown],
                        :feature => ["angle","rotation"],
                        :attended_feature => ["regular","odd"],
                        :unattended_feature => ["regular","odd"])
        println("effects sub $(subject_num) el $(i)")
        eff = effects(design,m)
        eff.subject .= string(evts[1,:subject])
        eff.selected_electrode .= i
        # Save evoked
        CSV.write(destination_path*filename, eff)
    end
end