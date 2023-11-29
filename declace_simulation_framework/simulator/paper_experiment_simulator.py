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

LOG_LEVEL_NAME = "PAPER_SIMULATOR"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class PaperBenchmarkSimulator:
    def __init__(
        self,
        problem: Problem,
        network_generator: NetworkGenerator,
        saboteur: InstanceSaboteur,
        shutdown_probability: float,
        cr_timeout: int,
        opt_timeout: int,
        random_state: RandomState,
        output_filename: str
    ):

        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.current_problem = problem

        self.asp_scratch = ASPOptimalReasoningService(PRECISION)
        self.prolog_cr = PrologContinuousReasoningService()
        self.prolog_scratch = PrologHeuristicReasoningService()

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

        self.random_state = random_state
        self.output_filename = output_filename

        self.network_generator = network_generator

    def __cleanup__(self):
        self.prolog_scratch.cleanup()
        self.prolog_cr.cleanup()

    def ruin(self):
        # Update the current problem with a saboteur
        self.current_problem = self.saboteur.ruin(self.current_problem, self.random_state)

        # Now prune some nodes, build a closure
        pruned_network = prune_network(self.current_problem.network, self.shutdown_probability, self.random_state)
        closure = snapshot_closure(pruned_network)

        # Create a problem instance w/ the pruned nodes
        to_return = self.current_problem.change_underlying_network(closure)
        return to_return

    def simulate(self, n):
        asp_placement, asp_cost = None, -1
        heu_placement, heu_cost = None, -1
        cr_placement, cr_cost = None, -1

        log_file = Path(self.output_filename).open('w')
        writer = csv.DictWriter(
            log_file,
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL,
            quotechar="\"",
            fieldnames=(
                'step',
                'asp_time',
                'heu_time',
                'cr_time',
                'declace_time',
                'asp_cost',
                'heu_cost',
                'cr_cost',
                'declace_cost',
                'asp_placement',
                'heu_placement',
                'cr_placement',
                'declace_placement'
            )
        )
        writer.writeheader()

        stopwatch = Stopwatch(5)

        problem = self.ruin()

        try:
            with stopwatch.trigger('asp'):
                asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
                self.prolog_cr.inject_placement(asp_placement)
        except:
            # Unsatisfiable instance: stop
            pass


        try:
            with stopwatch.trigger('heu'):
                #heu_placement, heu_stats = None, None
                heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
        except:
            pass

        writer.writerow({
            'step': 0,
            'asp_time': stopwatch.get('asp'),
            'asp_cost': asp_placement.cost if asp_placement is not None else -1,
            'heu_time': stopwatch.get('heu'),
            'heu_cost': heu_placement.cost if heu_placement is not None else -1,
            'cr_time': -1,  # first time CR is not done
            'cr_cost': -1,  # first time CR is not done
            'asp_placement': asp_placement.as_pairs if asp_placement is not None else None,
            'heu_placement': heu_placement.as_pairs if heu_placement is not None else None,
            'cr_placement': None, # first time CR is not done
            'declace_time': stopwatch.get('asp'),
            'declace_cost': asp_placement.cost if asp_placement is not None else -1,
            'declace_placement': asp_placement.as_pairs if asp_placement is not None else None
        })
        log_file.flush()

        for step in range(1, n):
            asp_placement, asp_cost = None, -1
            heu_placement, heu_cost = None, -1
            cr_placement, cr_cost = None, -1
            declace_placement, declace_cost = None, -1

            problem = self.ruin()
            stopwatch.clear()
            row = {'step': step}

            try:
                with stopwatch.trigger('asp'):
                    asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
                row['asp_cost'] = asp_placement.cost
            except:
                row['asp_cost'] = -1
                asp_placement = None
            row['asp_time'] = stopwatch.get('asp')

            try:
                with stopwatch.trigger('cr'):
                    cr_placement, cr_stats = self.prolog_cr.cr_solve(problem, self.cr_timeout)
                row['cr_cost'] = cr_placement.cost
                row['cr_time'] = stopwatch.get('cr')
                row['declace_cost'] = cr_placement.cost
                row['declace_time'] = stopwatch.get('cr')
                declace_placement = cr_placement
            except:
                if asp_placement is None:
                    row['cr_time'] = stopwatch.get('cr')
                    row['cr_cost'] = -1
                    cr_placement = None
                    row['declace_time'] = stopwatch.get('cr') + stopwatch.get('asp')
                    row['declace_cost'] = -1
                    declace_placement = None
                else:
                    row['cr_time'] = stopwatch.get('cr')
                    row['cr_cost'] = -1 # row['asp_cost']
                    cr_placement = None # asp_placement
                    self.prolog_cr.inject_placement(asp_placement)
                    row['declace_time'] = stopwatch.get('cr') + stopwatch.get('asp')
                    row['declace_cost'] = row['asp_cost']
                    declace_placement = asp_placement
            try:
                with stopwatch.trigger('heu'):
                    #self.prolog_scratch.prolog_server.thread.query("retractall(placedImages(_,_,_))") # SF: I think this is not needed
                    #heu_placement, heu_stats = None, None
                    heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
                row['heu_cost'] = heu_placement.cost
            except:
                row['heu_cost'] = -1
                heu_placement = None
            row['heu_time'] = stopwatch.get('heu')

            row['asp_placement'] = asp_placement.as_pairs if asp_placement is not None else None
            row['heu_placement'] = heu_placement.as_pairs if heu_placement is not None else None
            row['cr_placement'] = cr_placement.as_pairs if cr_placement is not None else None
            row['declace_placement'] = cr_placement.as_pairs if cr_placement is not None else row['asp_placement']

            writer.writerow(row)
            log_file.flush()

            if asp_placement is None: #or (heu_placement is None and cr_placement is None):
                self.current_problem = self.original_problem.change_underlying_network(self.network_generator.generate(self.random_state))

        log_file.close()
        self.__cleanup__()
