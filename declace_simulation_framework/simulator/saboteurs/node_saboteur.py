from numpy.random import RandomState
from declace.model import Node
from declace_simulation_framework.generator.attribute import AttributeGenerator
from declace_simulation_framework.simulator.saboteurs import NodeSaboteur


class NodeStorageWobble(NodeSaboteur):
    def __init__(self, delta: AttributeGenerator):
        self.delta = delta

    def ruin(self, node: Node, state: RandomState) -> Node:
        return Node(
            node.id, int((1 + self.delta.generate(state)) * node.storage), int(node.cost)
        )
