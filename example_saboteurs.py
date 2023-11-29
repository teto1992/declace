import sys
from numpy.random import RandomState

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import BarabasiAlbert
from declace_simulation_framework.generator.attribute import (
    UniformDiscrete,
    MultiModal,
    UniformContinuous,
)
from declace_simulation_framework.generator import (
    LinkGenerator,
    NodeGenerator,
    NetworkGenerator,
)

from declace_simulation_framework.simulator.saboteurs import (
    InstanceSaboteur,
    ImageSizeWobble,
    NodeStorageWobble,
    LinkTiedLatencyBandwidthWobble,
)
from declace_simulation_framework.utils import prune_network, snapshot_closure

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
    random_network = g.generate(r)

    print("Before saboteurs:")
    print(random_network)

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.05, 0.05)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.02, 0.08)),
        ImageSizeWobble(UniformContinuous(0.05, 0.10)),
    )

    images = [Image("ubuntu", 120, 8.0), Image("busybox", 150, 4.0)]

    new_instance = saboteur.ruin(Problem(images, random_network), r)

    print("After saboteurs:")
    print(new_instance.network)

    print("Example pruned network:")
    pruned = prune_network(new_instance.network, 0.10, r)
    print(pruned)

    print("Example closure:")
    clos = snapshot_closure(pruned)
    print(clos)
