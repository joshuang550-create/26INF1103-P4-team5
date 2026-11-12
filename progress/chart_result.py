from dataclasses import dataclass


@dataclass(frozen=True)
class ChartResult:
    """ What GUI gets back for chart, show graph if have, else show default text """
    graph: object = None # matplotlib fig when chart was made, else none
    default: str = ""    # text show instead when no graph

    @property
    def has_graph(self):
        return self.graph is not None