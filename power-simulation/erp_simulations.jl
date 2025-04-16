# Load required packages
using UnfoldSim # For simulation
using Random # For randomization
using StableRNGs # To get an RNG
using Unfold # For analysis
using CairoMakie # For plotting
using UnfoldMakie # For plotting

design =
    SingleSubjectDesign(;
        conditions = Dict(
            :attention => ["attended", "unattended"],
            :prediction => ["regular","odd"],
            :position => ["up","down"],
        ),
        event_order_function = shuffle,
    ) |> x -> RepeatDesign(x, 100);

    
events_df = generate_events(StableRNG(1), design);
first(events_df, 10)



p1 = LinearModelComponent(; basis = p100(), formula = @formula(0 ~ 1 + attention), β = [5,1]);

n1 = LinearModelComponent(;
    basis = n170(),
    formula = @formula(0 ~ 1 ),
    β = [5],
);

p3 = LinearModelComponent(;
    basis = p300(),
    formula = @formula(0 ~ 1 + prediction),
    β = [5, 0.2],
);

onset = UniformOnset(; width = 0, offset = 200);

noise = PinkNoise(; noiselevel = 2);

# Combine the components in a vector
components = [p1, n1, p3]

# Simulate data
eeg_data, events_df = simulate(StableRNG(1), design, components, onset, noise);

f = Figure(size = (1000, 400))
ax = Axis(
    f[1, 1],
    title = "Simulated EEG data",
    titlesize = 18,
    xlabel = "Time [samples]",
    ylabel = "Amplitude [µV]",
    xlabelsize = 16,
    ylabelsize = 16,
    xgridvisible = false,
    ygridvisible = false,
)

n_samples = 1400
lines!(eeg_data[1:n_samples]; color = "black")
v_lines = [
    vlines!(
        [r["latency"]];
        color = ["orange", "teal"][1+(r["attention"]=="attended")],
        label = r["attention"],
    ) for r in
    filter(:latency => x -> x < n_samples, events_df)[:, ["latency", "attention"]] |>
    eachrow
]
xlims!(ax, 0, n_samples)
axislegend("Event onset"; unique = true);

current_figure()