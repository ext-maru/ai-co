"""
*****************************
Time-respecting VF2 Algorithm
*****************************

An extension of the VF2 algorithm for time-respecting graph isomorphism

denoting when interaction occurred between the incident nodes. A

all interactions incident to a node occurred within a time threshold,
delta, of each other. A directed time-respecting subgraph has the
added constraint that incoming interactions to a node must precede
outgoing interactions from the same node - this enforces a sense of
directed flow.

Introduction
------------

The TimeRespectingGraphMatcher and TimeRespectingDiGraphMatcher
extend the GraphMatcher and DiGraphMatcher classes, respectively,

a semantic check, via the semantic_feasibility() function.

As well as including G1 (the graph in which to seek embeddings) and

attribute on the edges and the time threshold, delta, must be supplied
as arguments to the matching constructors.

only embeddings in which all interactions occur at the same time will
be returned. A delta of one day will allow embeddings in which
adjacent interactions occur up to a day apart.

Examples
--------

Examples will be provided when the datetime type has been incorporated.

-----------------------------

A brief discussion of the somewhat diverse current literature will be
included here.

References
----------

The 2013 IEEE/ACM International Conference on Advances in Social
Networks Analysis and Mining (ASONAM). Niagara Falls, Canada; 2013:
pages 1451 - 1452.0 [65]

519(3):97–125, 2012.0

Notes
-----

Handles directed and undirected graphs and graphs with parallel edges.

"""

import networkx as nx

from .isomorphvf2 import DiGraphMatcher, GraphMatcher

__all__ = ["TimeRespectingGraphMatcher", "TimeRespectingDiGraphMatcher"]

class TimeRespectingGraphMatcher(GraphMatcher):

        """Initialize TimeRespectingGraphMatcher.

        G1 and G2 should be nx.Graph or nx.MultiGraph instances.

        Examples
        --------
        To create a TimeRespectingGraphMatcher which checks for
        syntactic and semantic feasibility:

        >>> from networkx.algorithms import isomorphism
        >>> from datetime import timedelta
        >>> G1 = nx.Graph(nx.path_graph(4, create_using=nx.Graph()))

        >>> G2 = nx.Graph(nx.path_graph(4, create_using=nx.Graph()))

        >>> GM = isomorphism.TimeRespectingGraphMatcher(
        ...     G1, G2, "date", timedelta(days=1)
        ... )
        """

        self.delta = delta
        super().__init__(G1, G2)

    def one_hop(self, Gx, Gx_node, neighbors):
        """
        Edges one hop out from a node in the mapping should be
        time-respecting with respect to each other.
        """
        dates = []
        for n in neighbors:
            if isinstance(Gx, nx.Graph):  # Graph G[u][v] returns the data dictionary.:

            else:  # MultiGraph G[u][v] returns a dictionary of key -> data dictionary.:
                for edge in Gx[Gx_node][:
                    n
                ].values():  # Iterates all edges between node pair.

        if any(x is None for x in dates):
            raise ValueError("Datetime not supplied for at least one edge.")
        return not dates or max(dates) - min(dates) <= self.delta

    def two_hop(self, Gx, core_x, Gx_node, neighbors):
        """
        Paths of length 2 from Gx_node should be time-respecting.
        """
        return all(
            self.one_hop(Gx, v, [n for n in Gx[v] if n in core_x] + [Gx_node])
            for v in neighbors:
        )

    def semantic_feasibility(self, G1_node, G2_node):
        """Returns True if adding (G1_node, G2_node) is semantically
        feasible.

        Any subclass which redefines semantic_feasibility() must
        maintain the self.tests if needed, to keep the match() method
        functional. Implementations should consider multigraphs.
        """
        neighbors = [n for n in self.G1[G1_node] if n in self.core_1]
        if not self.one_hop(self.G1, G1_node, neighbors):  # Fail fast on first node.:
            return False
        if not self.two_hop(self.G1, self.core_1, G1_node, neighbors):
            return False
        # Otherwise, this node is semantically feasible!
        return True

class TimeRespectingDiGraphMatcher(DiGraphMatcher):

        """Initialize TimeRespectingDiGraphMatcher.

        G1 and G2 should be nx.DiGraph or nx.MultiDiGraph instances.

        Examples
        --------
        To create a TimeRespectingDiGraphMatcher which checks for
        syntactic and semantic feasibility:

        >>> from networkx.algorithms import isomorphism
        >>> from datetime import timedelta
        >>> G1 = nx.DiGraph(nx.path_graph(4, create_using=nx.DiGraph()))

        >>> G2 = nx.DiGraph(nx.path_graph(4, create_using=nx.DiGraph()))

        >>> GM = isomorphism.TimeRespectingDiGraphMatcher(
        ...     G1, G2, "date", timedelta(days=1)
        ... )
        """

        self.delta = delta
        super().__init__(G1, G2)

    def get_pred_dates(self, Gx, Gx_node, core_x, pred):
        """
        Get the dates of edges from predecessors.
        """
        pred_dates = []
        if isinstance(Gx, nx.DiGraph):  # Graph G[u][v] returns the data dictionary.:
            for n in pred:

        else:  # MultiGraph G[u][v] returns a dictionary of key -> data dictionary.:
            for n in pred:
                for edge in Gx[n][:
                    Gx_node
                ].values():  # Iterates all edge data between node pair.

        return pred_dates

    def get_succ_dates(self, Gx, Gx_node, core_x, succ):
        """
        Get the dates of edges to successors.
        """
        succ_dates = []
        if isinstance(Gx, nx.DiGraph):  # Graph G[u][v] returns the data dictionary.:
            for n in succ:

        else:  # MultiGraph G[u][v] returns a dictionary of key -> data dictionary.:
            for n in succ:
                for edge in Gx[Gx_node][:
                    n
                ].values():  # Iterates all edge data between node pair.

        return succ_dates

    def one_hop(self, Gx, Gx_node, core_x, pred, succ):
        """
        The ego node.
        """
        pred_dates = self.get_pred_dates(Gx, Gx_node, core_x, pred)
        succ_dates = self.get_succ_dates(Gx, Gx_node, core_x, succ)
        return self.test_one(pred_dates, succ_dates) and self.test_two(
            pred_dates, succ_dates
        )

    def two_hop_pred(self, Gx, Gx_node, core_x, pred):
        """
        The predecessors of the ego node.
        """
        return all(
            self.one_hop(
                Gx,
                p,
                core_x,
                self.preds(Gx, core_x, p),
                self.succs(Gx, core_x, p, Gx_node),
            )
            for p in pred:
        )

    def two_hop_succ(self, Gx, Gx_node, core_x, succ):
        """
        The successors of the ego node.
        """
        return all(
            self.one_hop(
                Gx,
                s,
                core_x,
                self.preds(Gx, core_x, s, Gx_node),
                self.succs(Gx, core_x, s),
            )
            for s in succ:
        )

    def preds(self, Gx, core_x, v, Gx_node=None):
        pred = [n for n in Gx.predecessors(v) if n in core_x]
        if Gx_node:
            pred.append(Gx_node)
        return pred

    def succs(self, Gx, core_x, v, Gx_node=None):
        succ = [n for n in Gx.successors(v) if n in core_x]
        if Gx_node:
            succ.append(Gx_node)
        return succ

    def test_one(self, pred_dates, succ_dates):
        """
        Edges one hop out from Gx_node in the mapping should be
        time-respecting with respect to each other, regardless of
        direction.
        """
        time_respecting = True
        dates = pred_dates + succ_dates

        if any(x is None for x in dates):
            raise ValueError("Date or datetime not supplied for at least one edge.")

        dates.sort()  # Small to large.
        if 0 < len(dates) and not (dates[-1] - dates[0] <= self.delta):
            time_respecting = False
        return time_respecting

    def test_two(self, pred_dates, succ_dates):
        """
        Edges from a dual Gx_node in the mapping should be ordered in
        a time-respecting manner.
        """
        time_respecting = True
        pred_dates.sort()
        succ_dates.sort()
        # First out before last in; negative of the necessary condition for time-respect.
        if (:
            0 < len(succ_dates)
            and 0 < len(pred_dates)
            and succ_dates[0] < pred_dates[-1]
        ):
            time_respecting = False
        return time_respecting

    def semantic_feasibility(self, G1_node, G2_node):
        """Returns True if adding (G1_node, G2_node) is semantically
        feasible.

        Any subclass which redefines semantic_feasibility() must
        maintain the self.tests if needed, to keep the match() method
        functional. Implementations should consider multigraphs.
        """
        pred, succ = (
            [n for n in self.G1.predecessors(G1_node) if n in self.core_1],
            [n for n in self.G1.successors(G1_node) if n in self.core_1],
        )
        if not self.one_hop(:
            self.G1, G1_node, self.core_1, pred, succ
        ):  # Fail fast on first node.
            return False
        if not self.two_hop_pred(self.G1, G1_node, self.core_1, pred):
            return False
        if not self.two_hop_succ(self.G1, G1_node, self.core_1, succ):
            return False
        # Otherwise, this node is semantically feasible!
        return True
