# `proimg`
Declarative container image placer to cloud-edge networks.

1. launch the `experiments.py` script to generate a sample infrastructure
2. launch either `asp_main.lp` or `lp_main.pl` to find image placements

# Installing
```bash
python3 -m build
pip3 install dist/*.whl
```

# Usage: ASP Image Placement
```bash
usage: asp_solve.py [-h] [-d] [-o OUTPUT] infrastructure images

positional arguments:
  infrastructure        File describing network architecture.
  images                File with images to be placed.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug
  -o OUTPUT, --output OUTPUT
                        Save optimal solution to file as a JSON.
```

# Usage: Generating topologies
```bash
usage: experiments.py [-h] [-o OUTPUT_FILE] [-s SEED] [-p PARAMS] num_nodes num_edges

positional arguments:
  num_nodes             Number of nodes in the generated network.
  num_edges             Number of edges under AB generation scheme.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Output file.
  -s SEED, --seed SEED  Numpy seed for random number generation.
  -p PARAMS, --params PARAMS
                        JSON containing node, link properties ranges.
```

Check out `experiments/params.json` to see an example of how to specify parameters' ranges.

# TODO

- [ ] Non-atom format (YAML, JSON?) for network topologies, images?
- [ ] Non-verbose output
- [ ] Fixed-precision arithmetic 
- [ ] ... 
