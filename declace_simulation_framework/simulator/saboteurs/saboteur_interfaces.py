from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
from numpy.random import RandomState
from declace.model import Node, Link, Image, Problem, NetworkSnapshot

"""
Saboteur interfaces. Saboteur implementations affect a PP instance's attributes, by e.g. altering image's sizes.
{Node,Link,Image} saboteurs are responsible for altering {Node,Link,Image}s respectively.
InstanceSaboteur alters the whole network.
---

Saboteur objects are meant to ``step'' a NetworkSnapshot, simulating changes in the underlying network topology.
"""


class Saboteur(ABC):
    @abstractmethod
    def ruin(
        self, obj: Union[Node, Link, Image], state: RandomState
    ) -> Union[Node, Link, Image]:
        pass


class NodeSaboteur(Saboteur):
    @abstractmethod
    def ruin(self, node: Node, state: RandomState) -> Node:
        pass


class LinkSaboteur(Saboteur):
    @abstractmethod
    def ruin(self, link: Link, state: RandomState) -> Link:
        pass


class ImageSaboteur(Saboteur):
    @abstractmethod
    def ruin(self, image: Image, state: RandomState) -> Image:
        pass


@dataclass(frozen=True)
class InstanceSaboteur:
    node: NodeSaboteur
    link: LinkSaboteur
    image: ImageSaboteur

    def ruin(self, problem: Problem, state: RandomState):

        VARIATION_RATE = 1/10

        if state.random() < 0.5:
            nodes = [self.node.ruin(n, state) for n in problem.network.nodes]
            links = [self.link.ruin(l, state) for l in problem.network.links]
        
        else:
            nodes = problem.network.nodes
            links = problem.network.links

        if state.random() < VARIATION_RATE:
            images = [self.image.ruin(i, state) for i in problem.images]
        else:
            images = problem.images

        return Problem(images, NetworkSnapshot(nodes, links), problem.max_replicas)

class NullSaboteur(InstanceSaboteur):
    def ruin(self, problem: Problem, state: RandomState):
        return problem
