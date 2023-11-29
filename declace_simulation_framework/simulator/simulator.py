import sys
import time

from declace.exceptions import UnsatisfiableContinuousReasoning, UnsatisfiablePlacement
from declace.model import Problem, PRECISION
from declace.reasoners.cr.prolog_cr import PrologContinuousReasoningService
from declace.reasoners.opt.asp_opt import ASPOptimalReasoningService
from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)

from loguru import logger

LOG_LEVEL_NAME = "SIMULATOR_LOW"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class Simulator:
    def __init__(
        self,
        problem: Problem,
        saboteur: InstanceSaboteur,
        shutdown_probability: float,
        cr_timeout: int,
        opt_timeout: int,
    ):
        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.opt = ASPOptimalReasoningService(PRECISION)
        self.cr = PrologContinuousReasoningService()

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

    def __cleanup__(self):
        self.cr.cleanup()
        self.opt.cleanup()

    def simulate(self, n, random_state):
        now = time.time()
        logger.log(LOG_LEVEL_NAME, "====== SIMULATION STEP 0 ========")

        preprocessing_time = time.time()
        ########################## Solving OIPP for the first time on the instance
        pruned_network = prune_network(
            self.original_problem.network, self.shutdown_probability, random_state
        )
        logger.log(LOG_LEVEL_NAME, "Pruning network for first solving shot")

        closure = snapshot_closure(pruned_network)
        logger.log(LOG_LEVEL_NAME, "Computing network closure")
        net_preprocessing_time = time.time() - preprocessing_time

        current_problem = self.original_problem.change_underlying_network(closure)
        current_placement, stats = self.opt.opt_solve(current_problem, self.opt_timeout)
        ##########################################################################

        print("OPT step {:.3f}s".format(stats['time']))

        ############################# Inject starting CR solution
        # First optimal solution with ASP; inject into CR module
        self.cr.inject_placement(current_placement)
        ##########################################################

        logger.log(
            LOG_LEVEL_NAME,
            "First shot: {:.3f}".format((time.time() - now) - net_preprocessing_time),
        )
        logger.log(
            LOG_LEVEL_NAME,
            "Network preprocessing time (routing): {:.3f}s".format(
                net_preprocessing_time
            ),
        )
        now = time.time()

        current_step = 1
        while current_step < n:
            logger.log(
                LOG_LEVEL_NAME,
                "====== SIMULATION STEP {} ========".format(current_step),
            )
            ################################### Apply saboteurs + Network closure
            preprocessing_time = time.time()
            current_network = prune_network(
                self.original_problem.network, self.shutdown_probability, random_state
            )
            problem = self.saboteur.ruin(
                current_problem.change_underlying_network(current_network), random_state
            )
            current_network = snapshot_closure(problem.network)
            net_preprocessing_time = time.time() - preprocessing_time
            logger.log(
                LOG_LEVEL_NAME,
                "Network preprocessing time (routing): {:.3f}s".format(
                    net_preprocessing_time
                ),
            )
            #################################################################################

            try:
                current_problem = problem.change_underlying_network(current_network)

                # CR works, cr_solve self-updates the Placement
                current_placement, stats = self.cr.cr_solve(
                    current_problem, self.cr_timeout
                )
                logger.log(
                    LOG_LEVEL_NAME,
                    "CONTINUOUS REASONING OK, prolog solving time: {:.3f}s".format(
                        stats['time']
                    ),
                )

                print("CR step: {:.3f}s".format(stats['time']))

            except UnsatisfiableContinuousReasoning:
                # or timeout; name it better
                logger.log(LOG_LEVEL_NAME, "CONTINUOUS REASONING FAIL")

                try:
                    # try to compute a new one with ASP, and update
                    current_placement, stats = self.opt.opt_solve(
                        current_problem, self.opt_timeout
                    )
                    self.cr.inject_placement(current_placement)
                    logger.log(LOG_LEVEL_NAME, "OPTIMAL REASONING OK")
                    print("OPT step: {:.3f}s".format(stats['time']))

                except UnsatisfiablePlacement:
                    logger.log(LOG_LEVEL_NAME, "OPTIMAL REASONING FAIL")
                    self.__cleanup__()
                    sys.exit(0)

            # If I arrive here, I want to be sure that next round I can peform CR
            assert self.cr.can_perform_continuous_reasoning

            logger.log(LOG_LEVEL_NAME, current_placement)

            current_step += 1
            logger.log(
                LOG_LEVEL_NAME,
                "Solving shot: {:.3f}, cost {}".format(
                    (time.time() - now) - net_preprocessing_time, current_placement.cost
                ),
            )

            now = time.time()

        self.__cleanup__()

        return
