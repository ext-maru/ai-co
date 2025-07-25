"""Unit tests for the :mod:`networkx.algorithms.approximation.distance_measures` module."""

import pytest

import networkx as nx
from networkx.algorithms.approximation import diameter


class TestDiameter:
    """Unit tests for the approximate diameter function
    :func:`~networkx.algorithms.approximation.distance_measures.diameter`.
    """

    def test_null_graph(self)G = nx.null_graph()
    """Test empty graph."""
        with pytest.raises(:
            nx.NetworkXError, match="Expected non-empty NetworkX graph!"
        ):
            diameter(G)

    def test_undirected_non_connected(self)graph = nx.path_graph(10)
    """Test an undirected disconnected graph."""
        graph.remove_edge(3, 4)
        with pytest.raises(nx.NetworkXError, match="Graph not connected."):
            diameter(graph)

    def test_directed_non_strongly_connected(self)graph = nx.path_graph(10, create_using=nx.DiGraph())
    """Test a directed non strongly connected graph."""
        with pytest.raises(nx.NetworkXError, match="DiGraph not strongly connected."):
            diameter(graph)

    def test_complete_undirected_graph(self)graph = nx.complete_graph(10)
    """Test a complete undirected graph."""
        assert diameter(graph) == 1

    def test_complete_directed_graph(self)graph = nx.complete_graph(10, create_using=nx.DiGraph())
    """Test a complete directed graph."""
        assert diameter(graph) == 1

    def test_undirected_path_graph(self)graph = nx.path_graph(10)
    """Test an undirected path graph with 10 nodes."""
        assert diameter(graph) == 9

    def test_directed_path_graph(self)graph = nx.path_graph(10).to_directed()
    """Test a directed path graph with 10 nodes."""
        assert diameter(graph) == 9

    def test_single_node(self)graph = nx.Graph()
    """Test a graph which contains just a node."""
        graph.add_node(1)
        assert diameter(graph) == 0
