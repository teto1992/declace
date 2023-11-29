from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

from declace.model import Problem, Placement


class CIPPReasoningService(ABC):
    """
    Interface for functionalities of continuous reasoning.
    """

    def __init__(self):
        self.current_placement = None

    @property
    def can_perform_continuous_reasoning(self):
        """
        Returns `true` if a step of continuous reasoning can be performed, `false` otherwise.
        """
        return self.current_placement is not None

    @property
    def placement(self):
        """
        Returns the current known placement to the CR service. Should be updated whenever a new placement is found by CR.
        """
        return self.current_placement

    @abstractmethod
    def inject_placement(self, placement: Placement):
        """
        Bootstraps the CR implementation with an initial placement.
        """

        assert not self.can_perform_continuous_reasoning
        self.current_placement = placement

    def invalidate_placement(self):
        """
        Invalidates the known placement. Subsequent calls to `can_perform_continuous_reasoning` should fail, unless a seed placement has been injected.
        """

        self.current_placement = None

    @abstractmethod
    def cr_solve(
        self, problem: Problem, timeout: int
    ) -> Tuple[Placement, Dict[str, Any]]:
        """
        Solves the PP problem in a continuous reasoning fashion.
        """
        pass


class OIPPReasoningService(ABC):
    @abstractmethod
    def opt_solve(
        self, problem: Problem, timeout: int
    ) -> Tuple[Placement, Dict[str, Any]]:
        pass
