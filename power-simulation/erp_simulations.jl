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


free = hanning(0.07,0.080,100)


c1 = LinearModelComponent(;
    basis = free,
    formula = @formula(0 ~ 1 + attention + position + attention&position), 
    β = [3,0,-6,-0.72]
);

# p1 = LinearModelComponent(;
#     basis = hanning(0.1,0.120,100),
#     formula = @formula(0 ~ 1 + attention),
#     β = [1,0.4],
# );
n1 = LinearModelComponent(;
    basis = n170(),
    formula = @formula(0 ~ 1 + position),
    β = [0.5,1],
);

p2 = LinearModelComponent(;
    basis = hanning(0.15,0.3,100),
    formula = @formula(0 ~ 1 + attention + prediction + position + attention&prediction),
    β = [5,0,0,-4,0.3],
);

onset = UniformOnset(; width = 0, offset = 300);

noise = PinkNoise(; noiselevel = 2);

# Combine the components in a vector
components = [c1, n1, p2]

# Simulate data
eeg_data, events_df = UnfoldSim.simulate(StableRNG(1), design, components, onset, noise);

# Validate
m = fit(
    UnfoldModel,
    [
        Any => (
            @formula(0 ~ 1 + attention*position*prediction),
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
    effects(Dict(
            :attention => ["attended", "unattended"],
            :prediction => ["regular","odd"],
            :position => ["up","down"]), m);
    mapping = (; color = :prediction, linestyle = :attention, group = :position),
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
xlims!(current_axis(), 0, 0.3)
current_figure()