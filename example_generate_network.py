import sys
from numpy.random import RandomState
from declace_simulation_framework.generator.topology import BarabasiAlbert
from declace_simulation_framework.generator.attribute import UniformDiscrete, MultiModal
from declace_simulation_framework.generator import (
    LinkGenerator,
    NodeGenerator,
    NetworkGenerator,
)


if __name__ == "__main__":
    g = NetworkGenerator(
        BarabasiAlbert(n=10, m=3),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(20, 20, 30, 40), 0.2),
                (UniformDiscrete(1, 2, 3, 4), 0.8),
            ),
            cost=UniformDiscrete(1, 2, 3, 4),
        ),
        LinkGenerator(
            latency=UniformDiscrete(1, 2, 3, 4), bandwidth=UniformDiscrete(1, 2, 3, 4)
        ),
    )

    r = RandomState(int(sys.argv[1]))
    print(g.generate(r))
    print(g.generate(r))
    print(g.generate(r))
