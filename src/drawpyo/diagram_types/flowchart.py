"""Typed flowchart objects with deterministic automatic layout."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple, Union

from ..diagram.edges import Edge
from ..diagram.objects import Object
from ..file import File
from ..page import Page
from ._graph_layout import (
    Point,
    ROUTING_FRAME_MARGIN,
    layout_directed_graph,
    route_edges,
)


PathInput = Union[str, os.PathLike[str]]


class FlowChart:
    """A directed flowchart containing typed nodes and links."""

    def __init__(
        self,
        *,
        direction: str = "down",
        link_style: str = "orthogonal",
        layer_spacing: int = 80,
        node_spacing: int = 40,
        component_spacing: int = 100,
        padding: int = 40,
        file_path: PathInput = ".",
        file_name: str = "Flowchart.drawio",
    ) -> None:
        if direction not in {"down", "right"}:
            raise ValueError("direction must be 'down' or 'right'")
        if link_style not in {"orthogonal", "straight", "curved"}:
            raise ValueError("link_style must be 'orthogonal', 'straight', or 'curved'")
        for name, value in {
            "layer_spacing": layer_spacing,
            "node_spacing": node_spacing,
            "component_spacing": component_spacing,
            "padding": padding,
        }.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

        self.direction = direction
        self.link_style = link_style
        self.layer_spacing = layer_spacing
        self.node_spacing = node_spacing
        self.component_spacing = component_spacing
        self.padding = padding
        self.file = File(file_name=file_name, file_path=str(file_path))
        self.page = Page(file=self.file, name="Flowchart")
        self.objects: List[FlowChartNode] = []
        self.links: List[Edge] = []
        self._routed_paths: Tuple[Tuple[Point, ...], ...] = ()

    @property
    def file_name(self) -> str:
        return self.file.file_name

    @file_name.setter
    def file_name(self, value: str) -> None:
        self.file.file_name = value

    @property
    def file_path(self) -> str:
        return self.file.file_path

    @file_path.setter
    def file_path(self, value: PathInput) -> None:
        self.file.file_path = str(value)

    def add_object(self, obj: "FlowChartNode") -> None:
        """Register a typed node with this chart and its page."""

        if not isinstance(obj, FlowChartNode):
            raise TypeError("FlowChart only accepts FlowChartNode objects")
        if obj.flowchart is not self:
            raise ValueError("The node belongs to a different FlowChart")
        if obj not in self.objects:
            obj.page = self.page
            self.objects.append(obj)

    def _connect(
        self, source: "FlowChartNode", target: "FlowChartNode", label: Optional[str]
    ) -> Edge:
        if not isinstance(target, FlowChartNode):
            raise TypeError("FlowChart links must target a FlowChartNode")
        if source.flowchart is not self or target.flowchart is not self:
            raise ValueError("FlowChart links cannot cross between charts")

        for edge in self.links:
            if edge.source is source and edge.target is target and edge.label == label:
                return edge

        if source.max_outgoing is not None:
            outgoing = [edge for edge in self.links if edge.source is source]
            if len(outgoing) >= source.max_outgoing:
                if source.max_outgoing == 0:
                    raise ValueError(
                        f"{type(source).__name__} nodes cannot have outgoing links"
                    )
                raise ValueError(
                    f"{type(source).__name__} nodes allow only "
                    f"{source.max_outgoing} outgoing link"
                )

        edge = Edge(
            page=self.page,
            source=source,
            target=target,
            label=label,
            waypoints=self.link_style,
            line_end_target="classic",
            endFill_target=True,
        )
        self.links.append(edge)
        return edge

    def auto_layout(self) -> None:
        """Position all nodes and route all links using a best-effort graph layout."""

        if not self.objects:
            self._routed_paths = ()
            return

        node_ids = {
            node: f"node:{index:08d}" for index, node in enumerate(self.objects)
        }
        sizes = {
            node_ids[node]: (int(node.width), int(node.height)) for node in self.objects
        }
        graph_edges = [
            (node_ids[edge.source], node_ids[edge.target]) for edge in self.links
        ]
        positions = layout_directed_graph(
            list(node_ids.values()),
            graph_edges,
            sizes,
            direction=self.direction,
            layer_spacing=self.layer_spacing,
            node_spacing=self.node_spacing,
            component_spacing=self.component_spacing,
        )
        origin = (
            self.padding + ROUTING_FRAME_MARGIN,
            self.padding + ROUTING_FRAME_MARGIN,
        )
        object_by_id: Dict[str, Object] = {}
        for node, node_id in node_ids.items():
            x, y = positions[node_id]
            node.position = (x + origin[0], y + origin[1])
            object_by_id[node_id] = node

        self._routed_paths = route_edges(
            object_by_id,
            [
                (node_ids[edge.source], node_ids[edge.target], edge)
                for edge in self.links
            ],
            direction=self.direction,
        )
        self._fit_page()

    def _fit_page(self) -> None:
        if not self.objects:
            return
        maximum_x = max(node.position[0] + node.width for node in self.objects)
        maximum_y = max(node.position[1] + node.height for node in self.objects)
        route_points = [point for edge in self.links for point in edge.geometry.points]
        if route_points:
            maximum_x = max(maximum_x, max(point.x for point in route_points))
            maximum_y = max(maximum_y, max(point.y for point in route_points))
        self.page.width = max(850, maximum_x + self.padding)
        self.page.height = max(1100, maximum_y + self.padding)

    def write(self, **kwargs: object) -> str:
        """Write the flowchart's Draw.io file and return its path."""

        return self.file.write(**kwargs)


class FlowChartNode(Object):
    """Base class for nodes owned by a :class:`FlowChart`."""

    library_shape = "process"
    max_outgoing: Optional[int] = None

    def __init__(
        self, *, flowchart: FlowChart, value: str = "", **kwargs: object
    ) -> None:
        if not isinstance(flowchart, FlowChart):
            raise TypeError("flowchart must be a FlowChart")
        if "page" in kwargs:
            raise TypeError("FlowChart nodes receive their page from flowchart")
        super().__init__(value=value, **kwargs)
        self.format_as_library_object("flowchart", self.library_shape)
        self.apply_attribute_dict(kwargs)
        self.value = value
        self._flowchart = flowchart
        flowchart.add_object(self)

    @property
    def flowchart(self) -> FlowChart:
        return self._flowchart

    def connect(self, target: "FlowChartNode", label: Optional[str] = None) -> Edge:
        """Connect this node to another node in the same flowchart."""

        return self.flowchart._connect(self, target, label)


class Start(FlowChartNode):
    """Entry point for a flowchart, with one outgoing link."""

    library_shape = "start_1"
    max_outgoing = 1


class Process(FlowChartNode):
    """A processing step with one outgoing link."""

    library_shape = "process"
    max_outgoing = 1


class Decision(FlowChartNode):
    """A branching step with typed Yes and No links."""

    library_shape = "decision"

    def connect(self, target: FlowChartNode, label: Optional[str] = None) -> Edge:
        if label is None or not label.strip():
            raise ValueError("Decision.connect() requires a non-empty branch label")
        if label.casefold() == "yes":
            return self.yes(target)
        if label.casefold() == "no":
            return self.no(target)
        return super().connect(target, label)

    def yes(self, target: FlowChartNode) -> Edge:
        """Create this decision's single Yes branch."""

        return self._typed_branch(target, "Yes")

    def no(self, target: FlowChartNode) -> Edge:
        """Create this decision's single No branch."""

        return self._typed_branch(target, "No")

    def _typed_branch(self, target: FlowChartNode, label: str) -> Edge:
        for edge in self.flowchart.links:
            if edge.source is self and edge.label == label:
                if edge.target is target:
                    return edge
                raise ValueError(f"Decision already has a {label} branch")
        return self.flowchart._connect(self, target, label)


class End(FlowChartNode):
    """Terminal flowchart node that cannot have outgoing links."""

    library_shape = "terminator"
    max_outgoing = 0


__all__ = ["FlowChart", "FlowChartNode", "Start", "Process", "Decision", "End"]
