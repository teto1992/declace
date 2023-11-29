from pathlib import Path
from typing import Tuple, List, Optional

from swiplserver import PrologMQI, PrologThread
from dataclasses import dataclass

from loguru import logger

LOG_LEVEL_NAME = "PROLOG_SERVER_WRAPPER"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


@dataclass(frozen=True)
class PrologQuery:
    predicate_name: str
    varnames: List[str]

    @property
    def as_atom(self):
        return "{}({})".format(self.predicate_name, ", ".join(self.varnames))

    @staticmethod
    def from_string(pname, vars):
        return PrologQuery(pname, vars.split(","))


@dataclass(frozen=True)
class PrologPredicate:
    predicate_name: str
    arity: int

    @staticmethod
    def from_string(string):
        pname, arity = string.split("/")
        return PrologPredicate(pname, int(arity))

    @staticmethod
    def from_strings(*strings: str):
        return [PrologPredicate.from_string(s) for s in strings]


@dataclass(frozen=True)
class PrologDatafile:
    path: Path
    retractions: List[PrologPredicate]

    @property
    def retract_signature(self):
        def retract_atom(predicate: PrologPredicate):
            return "{}({})".format(
                predicate.predicate_name, ",".join("_" for _ in range(predicate.arity))
            )

        return "[{}]".format(", ".join(retract_atom(p) for p in self.retractions))


class PrologServer:
    def __init__(self, *programs: Path):
        self.mqi = PrologMQI()
        self.programs = programs
        self.thread: Optional[PrologThread] = None

    @property
    def alive(self):
        return self.thread is not None

    def __init_thread__(self):
        self.thread = self.mqi.create_thread()
        logger.log(LOG_LEVEL_NAME, "Starting thread: {}".format(str(self.thread)))

    def __load_program__(self, p):
        # TODO: Nicer exceptions
        assert p.exists() and p.is_file()
        q = "['{}']".format(p.as_posix())
        logger.log(LOG_LEVEL_NAME, "Running query to load a program: {}".format(q))
        self.thread.query(q)

    def __load_programs__(self):
        assert self.thread is not None
        for p in self.programs:
            self.__load_program__(p)

    def start(self):
        self.__init_thread__()
        self.__load_programs__()

    def stop(self):
        logger.log(LOG_LEVEL_NAME, "Stopping thread & quitting MQI")
        self.thread.stop()
        self.mqi.stop()

    def __enter__(self):
        self.start()

    # Stops the Prolog server.
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop()

    # Consults a datafile into the Prolog server through the loadFile predicate.
    # Hack: loadFile implements a read&assert loop, faster than built-in consult.
    # It retracts all predicates specified in the to_retract string.
    def load_datafile(self, datafile: PrologDatafile):
        q = "loadFile('{}', {})".format(
            datafile.path.absolute(), datafile.retract_signature
        )
        logger.log(LOG_LEVEL_NAME, "Running query to load a datafile: {}".format(q))
        self.thread.query(q)

    # def consult(self, filename: str, to_retract: str = None):
    #    if to_retract is None:
    #        self.thread.query("loadFile('{}', [])".format(filename))
    #    else:
    #        self.thread.query("loadFile('{}',{})".format(filename, to_retract))
    # Returns the first result of the specified query within the specified timeout.
    def query(self, query: PrologQuery, timeout=60):
        q = "once({})".format(query.as_atom)
        logger.log(
            LOG_LEVEL_NAME, "Querying for {}, running {}".format(query.as_atom, q)
        )
        result = self.thread.query(q, query_timeout_seconds=timeout)

        logger.log(
            LOG_LEVEL_NAME, "Query results on {}: {}".format(query.as_atom, result)
        )

        return result
