from abc import ABC, abstractmethod
from typing import Tuple
from numpy.random import RandomState

"""
A set of classes that wraps numpy.random.RandomState randomness' source.
"""


class AttributeGenerator(ABC):
    """
    Interface for attribute generators.
    """

    @abstractmethod
    def generate(self, random_state: RandomState):
        pass


class UniformDiscrete(AttributeGenerator):
    """
    Uniformly samples from a finite set of choices.
    """

    def __init__(self, *available_choices):
        self.available_choices = available_choices

    def generate(self, random_state: RandomState):
        return random_state.choice(self.available_choices)


class UniformContinuous(AttributeGenerator):
    """
    Uniformly samples from [l,u]..
    """

    def __init__(self, l, u):
        self.l = l
        self.u = u

    def generate(self, random_state: RandomState):
        return random_state.uniform(self.l, self.u)


class Normal(AttributeGenerator):
    """
    Randomly samples from a normal distribution.
    """

    def __init__(self, mean, std):
        self.mu = mean
        self.std = std

    def generate(self, random_state: RandomState):
        return random_state.normal(self.mu, self.std)


class MultiModal(AttributeGenerator):
    """
    Selects an AttributeGenerator - from a non-uniform distribution, then generates an attribute.
    """

    def __init__(self, *pairs: Tuple[AttributeGenerator, float]):
        self.generators, self.probabilities = zip(*pairs)

    def generate(self, random_state: RandomState):
        generator = random_state.choice(self.generators, p=self.probabilities)
        return generator.generate(random_state)
