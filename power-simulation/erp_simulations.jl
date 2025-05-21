# Load required packages
using UnfoldSim # For simulation
using Random # For randomization
using StableRNGs # To get an RNG
using Unfold # For analysis
using CairoMakie # For plotting
using UnfoldMakie # For plotting
using MixedModels, MixedModelsSim
using DSP # For stats

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


# c1 = LinearModelComponent(; basis =);

# basisi = n170()

p1 = LinearModelComponent(;
    basis = p100(),
    formula = @formula(0 ~ 1 + attention), 
    β = [5,1]
);

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

noise = PinkNoise(; noiselevel = 0);

# Combine the components in a vector
components = [p1, n1, p3]

# Simulate data
eeg_data, events_df = UnfoldSim.simulate(StableRNG(1), design, components, onset, noise);

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

m = fit(
    UnfoldModel,
    [
        Any => (
            @formula(0 ~ 1 + position + attention ),
            firbasis(τ = [-0.1, 1], sfreq = 100, name = "basis"),
        ),
    ],
    events_df,
    eeg_data,
);

# Create a data frame with the model coefficients and extract the coefficient names
coefs = coeftable(m)
coefnames = unique(coefs.coefname)

f2 = Figure(size = (1000, 400))
ga = f2[1, 1] = GridLayout()
gb = f2[1, 2] = GridLayout()

# Plot A: Estimated regression parameters
ax_A = Axis(
    ga[1, 1],
    title = "Estimated regression parameters",
    titlegap = 12,
    xlabel = "Time [s]",
    ylabel = "Amplitude [μV]",
    xlabelsize = 16,
    ylabelsize = 16,
    xgridvisible = false,
    ygridvisible = false,
)

for coef in coefnames
    estimate = filter(:coefname => ==(coef), coefs)

    lines!(ax_A, estimate.time, estimate.estimate, label = coef)
end
axislegend("Coefficient", framevisible = false)
hidespines!(ax_A, :t, :r)

# Plot B: Marginal effects
plot_B = plot_erp!(
    gb,
    effects(Dict(:position => ["up","down"], :attention => ["attended", "unattended"]), m);
    mapping = (; color = :attention, linestyle = :position, group = :position),
    legend = (; valign = :top, halign = :right),
    axis = (
        title = "Marginal effects",
        titlegap = 12,
        xlabel = "Time [s]",
        ylabel = "Amplitude [μV]",
        xlabelsize = 16,
        ylabelsize = 16,
        xgridvisible = false,
        ygridvisible = false,
    ),
)


current_figure()