import tempfile
import time
from collections import defaultdict
from math import ceil
from pathlib import Path
from typing import List, Tuple, Any, Dict

import clingo

from declace.api.prolog import PrologServer, PrologDatafile, PrologPredicate, PrologQuery
from declace.exceptions import UnsatisfiablePlacement
from declace.model import Problem, Placement, Image
from declace.reasoners import OIPPReasoningService


from loguru import logger

LOG_LEVEL_NAME = "PROLOG_HEU"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class PrologHeuristicReasoningService(OIPPReasoningService):
    SOURCE_FOLDER = Path(__file__).parent / "prolog_heu_source"

    def __init__(self):
        super().__init__()

        src = PrologHeuristicReasoningService.SOURCE_FOLDER
        self.prolog_server: PrologServer = PrologServer(
            src / "config.pl", src / "main.pl"
        )
        self.scratch_directory = tempfile.TemporaryDirectory()

    def cleanup(self):
        return self.__del__()

    def __del__(self):
        if self.prolog_server.alive:
            self.prolog_server.stop()

        self.scratch_directory.cleanup()

    def _set_up_datafile(self, problem: Problem):
        FILENAME = "infrastructure.pl"
        with Path(self.scratch_directory.name, FILENAME).open("w") as f:
            f.write(problem.as_facts + "\n")
            f.flush()

        data = PrologDatafile(
            path=Path(self.scratch_directory.name, FILENAME),
            retractions=PrologPredicate.from_strings(
                "node/3", "link/4", "image/3", "maxReplicas/1", "placedImages/3"
            ),
        )

        self.prolog_server.load_datafile(data)
        self.last_ = None

    def _ans_to_obj(self, query_result, images):
        image_id_to_image = {i.id: i for i in images}

        #### Atomi duplicati nelle risposte di Prolog?
        # query_ans = set()
        # for atom in query_result["P"]:
        #    query_ans.add(tuple(atom['args']))
        ####

        node_has_images = defaultdict(lambda: [], dict())
        for dict_ in query_result["Placement"]:
            image, node = dict_["args"]
            node_has_images[node].append(image_id_to_image[image])

        return Placement(query_result["Cost"], node_has_images)

    def opt_solve(
        self, problem: Problem, timeout: int
    , swiplserver=None) -> Tuple[Placement, Dict[str, Any]]:
        if not self.prolog_server.alive:
            self.prolog_server.start()

        # Write infrastructure changes to a datafile, loads it
        self._set_up_datafile(problem)

        # Query PrologServer for declare(P,Cost,Time)
        try:
            query_result = self.prolog_server.query(
                PrologQuery.from_string("placement", "Placement,Cost"), timeout=timeout
            )

            if not query_result:
                raise Exception("Unsatisfiable Prolog Heuristic")

            else:
                query_result = query_result[0]

        except swiplserver.PrologQueryTimeoutError:
            raise Exception("Prolog Heuristic Timeout")

        except swiplserver.PrologError as e:
            raise RuntimeError(
                "A Prolog error that is unrelated to timeouts or unsatisfiability:", e
            )

        # Parse result into a placement object
        computed_placement = self._ans_to_obj(query_result, problem.images)

        return computed_placement, {} #{'time': query_result["Time"]}
