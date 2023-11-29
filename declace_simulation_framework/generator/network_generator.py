from numpy.random import RandomState
from declace.model import NetworkSnapshot, Node, Link
from declace_simulation_framework.generator.attribute import AttributeGenerator
from declace_simulation_framework.generator.topology.nx_wrappers import GraphGenerator
from dataclasses import dataclass

"""
A Network object models a network of devices. In our model, Nodes are characterized by storage costs and available storage. 
Links are characterized by latencies and bandwidths.
"""


@dataclass(frozen=True)
class NodeGenerator:
    storage: AttributeGenerator
    cost: AttributeGenerator

    def generate(self, i, random_state: RandomState) -> Node:
        return Node(
            i, self.storage.generate(random_state), self.cost.generate(random_state)
        )

@dataclass(frozen=True)
class LinkGenerator:
    latency: AttributeGenerator
    bandwidth: AttributeGenerator

    def generate(self, i, j, random_state: RandomState) -> Link:
        return Link(
            i,
            j,
            self.latency.generate(random_state),
            self.bandwidth.generate(random_state),
        )


@dataclass(frozen=True)
class NetworkGenerator:
    topology: GraphGenerator
    node: NodeGenerator
    link: LinkGenerator

    def generate(self, random_state: RandomState) -> NetworkSnapshot:
        g = self.topology.generate(random_state)

        return NetworkSnapshot(
            [self.node.generate(i, random_state) for i in g.nodes],
            [self.link.generate(i, j, random_state) for i, j in g.edges],
        )
