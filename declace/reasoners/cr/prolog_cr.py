from collections import defaultdict
from pathlib import Path
from typing import Tuple, Dict, Any

from declace.api.prolog import (
    PrologServer,
    PrologDatafile,
    PrologQuery,
    PrologPredicate,
)
from declace.exceptions import (
    UnsatisfiableContinuousReasoning,
    NoStartingPlacementForContinuousReasoning,
)
from declace.model import Problem, Placement
from declace.reasoners import CIPPReasoningService
import swiplserver

import tempfile
from loguru import logger

LOG_LEVEL_NAME = "CR_PROLOG"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class PrologContinuousReasoningService(CIPPReasoningService):
    SOURCE_FOLDER = Path(__file__).parent / "prolog_cr_source"

    def __init__(self):
        super().__init__()

        src = PrologContinuousReasoningService.SOURCE_FOLDER
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
            # f.write(placement.as_facts + "\n")
            f.flush()

        data = PrologDatafile(
            path=Path(self.scratch_directory.name, FILENAME),
            retractions=PrologPredicate.from_strings(
                "node/3", "link/4", "image/3", "maxReplicas/1"
            ),
        )

        self.prolog_server.load_datafile(data)

        # BUG: was deleting previously asserted placement at/2 and placedImages/3
        # Rename to load infrastructure?
        # self.prolog_server.query(PrologQuery.from_string("loadASP", "")) 
    

        self.last_ = None

    def _ans_to_obj(self, query_result, images):
        image_id_to_image = {i.id: i for i in images}

        #### Atomi duplicati nelle risposte di Prolog?
        # query_ans = set()
        # for atom in query_result["P"]:
        #    query_ans.add(tuple(atom['args']))
        ####

        node_has_images = defaultdict(lambda: [], dict())
        for dict_ in query_result["P"]:
            image, node = dict_["args"]
            node_has_images[node].append(image_id_to_image[image])

        return Placement(query_result["Cost"], node_has_images)

    def inject_placement(self, placement: Placement):
        if not self.prolog_server.alive:
            self.prolog_server.start()

        super().inject_placement(placement)

        # Injects at/2 -- found by ASP
        # retracts at/2, placedImages/3 -- probably redundant
        # calls loadASP

        FILENAME = "placement.pl"
        with Path(self.scratch_directory.name, FILENAME).open("w") as f:
            f.write(placement.as_facts + "\n")
            f.flush()

        data = PrologDatafile(
            path=Path(self.scratch_directory.name, FILENAME),
            #retractions=PrologPredicate.from_strings("", "")
            retractions=PrologPredicate.from_strings("at/2", "placedImages/3"), # SF: yes, it is redundant
        )

        self.prolog_server.load_datafile(data)

        # Rename to load infrastructure?
        self.prolog_server.query(PrologQuery.from_string("loadASP", ""))

    def cr_solve(
        self, problem: Problem, timeout: int
    ) -> Tuple[Placement, Dict[str, Any]]:
        if not self.can_perform_continuous_reasoning:
            raise NoStartingPlacementForContinuousReasoning()

        if not self.prolog_server.alive:
            self.prolog_server.start()

        # Write infrastructure changes to a datafile, loads it
        self._set_up_datafile(problem)

        # Query PrologServer for declare(P,Cost,Time)
        try:
            query_result = self.prolog_server.query(
                PrologQuery.from_string("declace", "P,Cost"), timeout=timeout
            )

            if not query_result:
                self.invalidate_placement()
                raise UnsatisfiableContinuousReasoning()

            else:
                query_result = query_result[0]

        except swiplserver.PrologQueryTimeoutError:
            self.invalidate_placement()
            raise UnsatisfiableContinuousReasoning()

        except swiplserver.PrologError as e:
            self.invalidate_placement()
            raise RuntimeError(
                "A Prolog error that is unrelated to timeouts or unsatisfiability:", e
            )

        # Parse result into a placement object
        computed_placement = self._ans_to_obj(query_result, problem.images)
        self.current_placement = computed_placement

        return computed_placement, {} #{'time': query_result["Time"]}
