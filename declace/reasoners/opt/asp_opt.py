import time
from collections import defaultdict
from math import ceil
from pathlib import Path
from typing import List, Tuple, Any, Dict

from ctypes import *
from pathlib import Path

import clingo

from declace.exceptions import UnsatisfiablePlacement
from declace.model import Problem, Placement, Image
from declace.reasoners import OIPPReasoningService


from loguru import logger

LOG_LEVEL_NAME = "OPT_ASP"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")

logger.level("@TERM", no=15, color="<blue>")


class Messages:
    TRANSFER_TIME_COMPUTATION = (
        "Computing @-term: compute_transfer_time({},{},{}) = {} ~ {}"
    )
    INTERMEDIATE_SOLUTION = "Found a solution with cost {}, optimal? {}, model: \n{}"


class Context:
    def __init__(self, precision):
        # TODO: Unità di misura, cifre aritmetica
        self.precision = precision
        so_file = (Path(__file__).parent / 'ttime.so').absolute() 
        my_functions = CDLL(so_file)
        my_functions.transfer_time.argtypes = [c_float, c_float, c_float]
        self.transfer_time = my_functions.transfer_time

                                  # MB,    Mb/s [1000],     ms
    def compute_transfer_time(self, size, bandwidth, latency):

        #r_milliseconds = (float(size.number) * float(8000.0) / float(bandwidth.number) + float(latency.number))
        
        r_milliseconds = self.transfer_time(size.number, bandwidth.number, latency.number)

        logger.log(
            "@TERM",
            Messages.TRANSFER_TIME_COMPUTATION.format(
                size, bandwidth, latency, r_milliseconds, ceil(r_milliseconds)
            ),
        )

        return clingo.Number(int(ceil(r_milliseconds)))


def project_answer_set(model):
    return [sym for sym in model.symbols(shown=True) if sym.match("placement", 2)]


class SolutionCallback:
    def __init__(self, precision):
        self._placement = None
        self._cost = None
        self._optimal = False

        self.init_time = time.time()
        self.intermediate_solutions: List[Tuple[int, float]] = []

        self.precision = precision

    def __call__(self, model):

        ######## HACK #########
        #if time.time() - self.init_time > 30: # SF manual timeout
        #    return False
        #######################

        atoms = project_answer_set(model)
        prg = "\n".join("{}.".format(str(x)) for x in atoms)
        logger.log(
            LOG_LEVEL_NAME,
            Messages.INTERMEDIATE_SOLUTION.format(
                model.cost, model.optimality_proven, prg
            ),
        )

        if not model.optimality_proven:
            exec_time = time.time() - self.init_time
            logger.log(
                LOG_LEVEL_NAME,
                f"Cost: {model.cost[0]} computed in: {exec_time:.3f} seconds",
            )
            self.intermediate_solutions.append((model.cost[0], exec_time))
            self._placement = atoms
            self._cost = model.cost
            return True  

        # self.current_time = time.time()
        assert model.optimality_proven 
        self._placement = atoms
        self._cost = model.cost
        self._optimal = True
        exec_time = time.time() - self.init_time
        logger.log(
            LOG_LEVEL_NAME,
            f"OPTIMAL Cost[{self.precision}]: {model.cost[0]} computed in: {exec_time:.3f} seconds",
        )
        self.intermediate_solutions.append((model.cost[0], exec_time))
        return False

    @property
    def best_known_placement(self):
        image_on_nodes = defaultdict(lambda: [])

        for symbol in self._placement:
            image = Image(
                symbol.arguments[0].arguments[0].name,
                symbol.arguments[0].arguments[1].number,
                symbol.arguments[0].arguments[2].number,
            )

            node = symbol.arguments[1].name

            image_on_nodes[node].append(image)

        return Placement(self._cost[0], image_on_nodes)


class ASPOptimalReasoningService(OIPPReasoningService):
    SOURCE_FOLDER = Path(__file__).parent / "asp_opt_source"

    def cleanup(self):
        pass

    def __init__(self, precision):
        # cost_at_time[i] = (a, b) -> i-th candidate model has cost a, found at time b
        # TODO: Refactor into a Stats class
        self.cost_at_time: List[Tuple[int, float]] = []
        self.precision = precision

    def opt_solve(self, problem: Problem, timeout: int) -> Tuple[Placement, Dict[str, Any]]:
        # Initialize a Clingo
        ctl = clingo.Control(["--models=0", "--opt-mode=optN"])
        ctl.load(
            (ASPOptimalReasoningService.SOURCE_FOLDER / "encoding.lp").as_posix()
        )  # encoding
        logger.log(LOG_LEVEL_NAME, "Loaded ASP encoding")

        # Serialize problem into a set of facts
        ctl.add("base", [], problem.as_facts)
        logger.log(LOG_LEVEL_NAME, "Loaded Problem-as-facts")

        # Grounding
        ground_start = time.time()
        logger.log(LOG_LEVEL_NAME, "GROUNDING START")
        ctl.ground([("base", [])], context=Context(self.precision))
        logger.log(
            LOG_LEVEL_NAME, "GROUNDING TIME: {:.3f}s".format(time.time() - ground_start)
        )

        # Solving
        cb = SolutionCallback(precision=self.precision)
        stats = None
        
        with ctl.solve(async_=True, on_model=cb) as handle:
            _ = handle.wait(timeout=float(timeout))
            handle.cancel()
            ans = handle.get()
            
            if ans.unsatisfiable:
                raise UnsatisfiablePlacement()

            elif ans.unknown:
                raise RuntimeError("Something was wrong in the clingo call, timeout?")

        # Parse the answer back into a Placement
        logger.log(
            LOG_LEVEL_NAME, "Intermediate solutions:", len(cb.intermediate_solutions)
        )

        return cb.best_known_placement, {'time': ctl.statistics['summary']['times']['total']}
