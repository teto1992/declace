import csv
import sys
from pathlib import Path

from numpy.random import RandomState
from argparse import ArgumentParser

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import (
    BarabasiAlbert,
    ErdosRenyi,
    TruncatedBarabasiAlbert,
    RandomInternet,
    WattsStrogatz,
)
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
from declace_simulation_framework.simulator import (
    Simulator,
    InstanceSaboteur,
    NodeStorageWobble,
    LinkTiedLatencyBandwidthWobble,
    ImageSizeWobble, PaperBenchmarkSimulatorScratch
)
from declace_simulation_framework.simulator.saboteurs import NullSaboteur
from declace.utils import enable_logging_channels

from loguru import logger
import loguru


def show_level(record):
    print("MESSAGE_LEVEL: ", record["level"].name)
    print(record)
    return True


if __name__ == "__main__":
    import sys
    enable_logging_channels(["DISABLE_LOGGING"])

    if len(sys.argv) != 3:
        print("Usage: {} [log file] [seed]".format(__file__))
        sys.exit(1)

    outputfile, seed = sys.argv[1:]
    seed = int(seed)

    r = RandomState(seed)

    g = NetworkGenerator(
        TruncatedBarabasiAlbert(n=78, m=3, k=3),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(8000, 16000), 0.4),
                (UniformDiscrete(4000), 0.5),
                (UniformDiscrete(2000), 0.1)
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5),
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1, 11))),
            bandwidth=UniformDiscrete(*list(range(25, 1001)))
        ),
    )

    images = [
        Image("busybox", 4, 15),
        Image("memcached", 126, 30),
        Image("nginx", 192, 60),
        Image("mariadb", 387, 120),

        #Image("alpine", 8, 15),
        #Image("traefik", 148, 30),
        #Image("httpd", 195, 60),
        #Image("postgres", 438, 120),

        #Image("ubuntu", 69, 15),
        #Image("redis", 149, 30),
        #Image("rabbitmq", 201, 60),
        #Image("mysql", 621, 120),
    ]


    NUM_EXPERIMENTS = 1000
    LOG_FILE = Path(outputfile).open(mode='w')

    writer = csv.DictWriter(
        LOG_FILE,
        delimiter=',',
        quoting=csv.QUOTE_MINIMAL,
        quotechar="\"",
        fieldnames=(
            'asp_time',
            'heu_time',
            'asp_cost',
            'heu_cost',
            'asp_placement',
            'heu_placement',
        )
    )
    writer.writeheader()

    for step in range(NUM_EXPERIMENTS):
        original_problem = Problem(images, g.generate(r), max_replicas=15)
        simulator = PaperBenchmarkSimulatorScratch(original_problem, timeout=45)
        dict_row = simulator.simulate()

        writer.writerow(dict_row)
        LOG_FILE.flush()

    LOG_FILE.close()