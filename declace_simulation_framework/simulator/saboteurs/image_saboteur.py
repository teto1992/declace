from numpy.random import RandomState
from declace.model import Image
from declace_simulation_framework.generator.attribute import (
    AttributeGenerator,
    UniformContinuous,
)
from declace_simulation_framework.simulator.saboteurs import ImageSaboteur


class ImageSizeWobble(ImageSaboteur):
    def __init__(self, delta: AttributeGenerator):
        self.delta = delta

    def ruin(self, image: Image, state: RandomState) -> Image:

        return Image(
            image.id,
            int((1 + self.delta.generate(state)) * image.size),
            int(image.max_transfer_time),
        )
