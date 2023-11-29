from abc import ABC, abstractmethod
import networkx as nx


"""
A set of classes that wraps networkx.generators.*_graph classes.
"""


class GraphGenerator(ABC):
    def __init__(self, nx_generator, **kwargs):
        self.kwargs = kwargs
        self.generator = nx_generator

    def generate(self, random_state) -> nx.Graph:
        # build a new graph

        raw_g = self.generator(seed=random_state, **self.kwargs)
        return raw_g

        #node_mapping = dict(zip(raw_g.nodes(), sorted(raw_g.nodes(), key=lambda k: random_state.random())))
        #return nx.relabel_nodes(raw_g, node_mapping)


class BarabasiAlbert(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "m" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.barabasi_albert_graph, **kwargs)


class TruncatedBarabasiAlbert(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "m" in kwargs
        assert "k" in kwargs

        self.k = kwargs["k"]
        del kwargs["k"]

        assert "seed" not in kwargs
        super().__init__(nx.generators.barabasi_albert_graph, **kwargs)

    def generate(self, random_state) -> nx.Graph:
        g = super().generate(random_state)
        for node_id in range(self.k):
            g.remove_node(node_id)
        return g


class ErdosRenyi(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "p" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.erdos_renyi_graph, **kwargs)

class WattsStrogatz(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "k" in kwargs
        assert "p" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.watts_strogatz_graph, **kwargs)

class RandomInternet(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.random_internet_as_graph, **kwargs)
