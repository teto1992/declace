import sys
import time
from pathlib import Path
from typing import List, Tuple

from numpy.random import RandomState

from declace.api.prolog import PrologQuery
from declace.exceptions import UnsatisfiableContinuousReasoning, UnsatisfiablePlacement
from declace.model import Problem, PRECISION
from declace.reasoners.cr.prolog_cr import PrologContinuousReasoningService
from declace.reasoners.opt.asp_opt import ASPOptimalReasoningService
from declace.reasoners.opt.prolog_heu import PrologHeuristicReasoningService
from declace_simulation_framework.generator import NetworkGenerator

from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)
from declace_simulation_framework.utils import Stopwatch
import csv

from loguru import logger

LOG_LEVEL_NAME = "PAPER_SIMULATOR_SCRATCH"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class PaperBenchmarkSimulatorScratch:
    def __init__(
        self,
        problem: Problem,
        timeout: int,
    ):

        self.original_problem = problem
        self.asp_scratch = ASPOptimalReasoningService(PRECISION)
        self.prolog_scratch = PrologHeuristicReasoningService()
        self.timeout = timeout

    def __cleanup__(self):
        self.prolog_scratch.cleanup()

    def simulate(self):
        asp_placement, asp_cost = None, -1
        heu_placement, heu_cost = None, -1

        stopwatch = Stopwatch(5)

        problem = self.original_problem

        problem = problem.change_underlying_network(snapshot_closure(problem.network))

        try:
            with stopwatch.trigger('asp'):
                asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.timeout)
        except:
            pass

        try:
            with stopwatch.trigger('heu'):
                heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.timeout)
        except:
            pass

        dict_row = {
            'asp_time': stopwatch.get('asp'),
            'asp_cost': asp_placement.cost if asp_placement is not None else -1,
            'heu_time': stopwatch.get('heu'),
            'heu_cost': heu_placement.cost if heu_placement is not None else -1,
            'asp_placement': asp_placement.as_pairs if asp_placement is not None else None,
            'heu_placement': heu_placement.as_pairs if heu_placement is not None else None,
        }

        self.__cleanup__()
        return dict_row
