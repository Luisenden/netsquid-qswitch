CHANGELOG
=========

2024-01-24 (1.1.1)
------------------
- added server_node to specify a server which is always part of the produced GHZ state
- added depolarizing noise to the quantum fiber
- added dependence on bright-sspace population to rates and depolarizing channel
- buffer size applied to leaf-node managers 

2023-12-12 (1.1.0)
------------------
- fixed sorting of leaf nodes: sort by node.name previously sorted up to 9 nodes correctly, but for n > 9 this results in '0','1', '10', '2', etc., which is why the simulation could not be executed for more than 10 nodes
- added option to define buffer size individually per node 
- included extraction of leaf nodes involved in produced GHZ states
- added function `simulate_scenarios_and_aggregate_results_as_pickle` to runtools
- added `example_capacity_vs_buffersize.py` to examples
- added `plot_impacts_capacity_vs_buffer.py` to examples

2020-12-18 (1.0.1)
------------------
- hot fix: added `matplotlib` to requirements

2020-12-18 (1.0.0)
------------------
- Updated README