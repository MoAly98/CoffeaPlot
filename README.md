# CoffeaPlot

This is a *framework* which is configuration-based layer on top of `coffea` data processing to produce histograms for analysis and create various types of useful plots for analysis studies. The framework is modularised keeping the user-becoming-developer in mind. This means that if the user needs a different type of plot, they can easily implement it with clear instructions. The nominal setup assumes the analysis is composed of the following building blocks:

- Regions
- Samples
- Variables
- Rescalings (Optional)

All of which the user can specify in a configuration file with an enforced schema. The plots that can be produced with the framework are:

- Data vs MC stacks
- Significance stacks
- MC v MC comparisons
- Separation Plots
- Efficiency plots
- Pie charts

## Known Limitations

- No optimisation for multi-tree analyses. This is a limitation of coffea single-tree processing. A condor-based approach can be helpful here.
- Pie charts can only be produced one at a time currently
- If a variable being histogrammed has not gotten event-boundaries, all arguments entering the variable definition must have the same length at the outer level.
- There is no support for systematic uncertainties.

## The Configuration File and Helpers

The configuration file has the following block strucutres:

`General`: The block handles the general settings such as input/output directories, logging levels,

## Caveats and Defaults

## Future Developments and Ideas
