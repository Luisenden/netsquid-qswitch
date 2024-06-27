NetSquid-QSwitch (1.1.1)
================================

Description
-----------

This is an extended version of the orginal user contributed [_snippet_](https://gitlab.com/softwarequtech/netsquid-snippets/netsquid-qswitch) for the [NetSquid quantum network simulator](https://netsquid.org) and contains tools for simulating a quantum switch.

The quantum switch node is located as center node in a star topology network. The leaf nodes continuously generate EPR pairs with the switch node, which performs a local operation to convert these into multipartite entangled states, shared by the leaf nodes. With tools from this snippet, one can obtain the capacity (the number of multipartite states produced) and the average quality (fidelity) of the produced multipartite states.

The tools were used for the simulations for the article [NetSquid, a discrete-event simulation platform for quantum networks](https://arxiv.org/abs/2010.12535), where we used NetSquid to go beyond the analytical analysis of the quantum switch by [Vardoyan et al.](https://dl.acm.org/doi/abs/10.1145/3374888.3374899) ([arXiv-version](https://arxiv.org/abs/1903.04420)).

Installation
------------

See the [INSTALL file](INSTALL.md) for instruction of how to install this snippet.
Verify the correct installation of the tool via `make verify`.

Documentation
-------------

To build and see the docs see the [docs README](docs/README.md).

Usage
-----

Starting to use this snippet is most easily done by (adjusting) any of the scripts in the `examples` folder. For example, the script `example_buffer_size_vs_capacity.py` obtains the mean capacity of the switch (the number of multipartite states produced) as function of the buffer size (a cap of the total number of memory positions that the switch node has available per leaf node), and plots the result.

Contributors
------------

* Tim Coopmans (t.j.coopmans[at]tudelft.nl)
* Luise Prielinger (l.p.prielinger[at]tudelft.nl)

License
-------

`netsquid-qswitch` has the following license:

> Copyright 2020 QuTech (TUDelft and TNO)
>
>   Licensed under the Apache License, Version 2.0 (the "License");
>   you may not use this file except in compliance with the License.
>   You may obtain a copy of the License at
>
>     http://www.apache.org/licenses/LICENSE-2.0
>
>   Unless required by applicable law or agreed to in writing, software
>   distributed under the License is distributed on an "AS IS" BASIS,
>   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
>   See the License for the specific language governing permissions and
>   limitations under the License.
