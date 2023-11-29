from numpy.random import RandomState
from declace.model import Link
from declace_simulation_framework.generator.attribute import (
    AttributeGenerator,
    UniformContinuous,
)
from declace_simulation_framework.simulator.saboteurs import LinkSaboteur


class LinkTiedLatencyBandwidthWobble(LinkSaboteur):
    def __init__(self, delta: AttributeGenerator):
        self.delta = delta

    def ruin(self, link: Link, state: RandomState) -> Link:
        d = self.delta.generate(state)
        return Link(
            link.source, link.target, int((1 + d) * link.latency), int((1 - d) * link.bandwidth)
        )
