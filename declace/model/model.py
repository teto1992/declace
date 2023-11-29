import dataclasses
import math
import typing
from math import ceil

from loguru import logger

LOG_LEVEL_NAME = "FIXED_ARITHMETIC"
logger.level(LOG_LEVEL_NAME, no=16, color="<blue>")

PRECISION = 3

"""
truncate(X,N,Result):- X >= 0, Result is floor(10^N*X)/10^N, !.
"""


@dataclasses.dataclass(frozen=True)
class Node:
    id: int
    storage: int
    cost: int

    @property
    def atom(self):
        return "node(n{},{},{})".format(self.id, self.storage, self.cost)


@dataclasses.dataclass(frozen=True)
class Link:
    source: int
    target: int
    latency: int # millisecondi di latenza del link
    bandwidth: float # Mb/s

    @property
    def atom(self):
        return "link(n{}, n{}, {}, {})".format(
            self.source,
            self.target,
            self.latency, # MILLISECONDI IN PRECISIONE FISSA
            int(self.bandwidth), #* 1000), SF: non serve?
        )


@dataclasses.dataclass(frozen=True)
class Image:
    id: str
    size: int
    max_transfer_time: int #secondi

    @property
    def atom(self):
        return "image({}, {}, {})".format(
            self.id, self.size, int(self.max_transfer_time)
        )


@dataclasses.dataclass(frozen=True)
class NetworkSnapshot:
    nodes: typing.Iterable[Node]
    links: typing.Iterable[Link]

    def __str__(self):
        string = [
            "A network on {} nodes and {} links.".format(
                len(self.nodes), len(self.links)
            )
        ]
        string.append("Nodes:\n")
        for node in self.nodes:
            string.append(
                "\t[{}] - {:.3f} MB, {:.3f} €/MB\n".format(
                    node.id, node.storage, node.cost
                )
            )

        string.append("Links:\n")
        for link in self.links:
            string.append(
                "\t{} -- {} - {:.3f}ms {:.3f}MB/s\n".format(
                    link.source, link.target, link.latency, link.bandwidth
                )
            )

        return "".join(string)


@dataclasses.dataclass(frozen=True)
class Placement:
    cost: float
    placement: typing.Dict[int, typing.Iterable[Image]]

    def __str__(self):
        string = ["A solution with cost {}.".format(self.cost)]
        for node, images in self.placement.items():
            string.append(
                "Images placed on {}: {}".format(node, [i.id for i in images])
            )
        return "\n".join(string)

    @property
    def as_facts(self):
        prg = []
        for node_id, images in self.placement.items():
            for image in images:
                # at(0, 'alpine')
                prg.append("at({}, {}).".format(image.id, node_id))
        return "\n".join(prg)

    @property
    def as_pairs(self):
        pairs = []
        for node_id, images in self.placement.items():
            for image in images:
                pairs.append((image.id, node_id))
        return ','.join("({},{})".format(*p) for p in pairs)


@dataclasses.dataclass(frozen=True)
class Problem:
    images: typing.Iterable[Image]
    network: NetworkSnapshot
    max_replicas: int

    @property
    def as_facts(self):
        prg = [
            "max_replicas({}).".format(self.max_replicas),
            "maxReplicas({}).".format(self.max_replicas),
        ]

        for image in self.images:
            prg.append("{}.".format(image.atom))

        for node in self.network.nodes:
            prg.append("{}.".format(node.atom))

        for link in self.network.links:
            prg.append("{}.".format(link.atom))

        return "\n".join(prg)

    def change_underlying_network(self, network: NetworkSnapshot) -> "Problem":
        return Problem(self.images, network, self.max_replicas)
