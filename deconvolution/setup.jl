# setup.jl — run once in an interactive session
using Pkg
Pkg.activate(".")
Pkg.add([
    "CSV",
    "DataFrames",
    "Effects",
    "Unfold",
    "PyMNE",
    "StatsModels",
    "JLD2",
    "PythonCall",
    "CondaPkg",
])

# Install MNE into Julia's conda env
using CondaPkg
CondaPkg.add("mne")

Pkg.precompile()
println("Setup complete!")