"""Private deterministic layout and routing helpers for directed diagrams."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from ..diagram.edges import Edge
from ..diagram.objects import Object


Point = Tuple[float, float]
ROUTING_CLEARANCE = 10
ROUTING_GAP = ROUTING_CLEARANCE * 2 + 8
ROUTING_FRAME_MARGIN = ROUTING_CLEARANCE * 3
_BEND_PENALTY = 24
_CROSSING_PENALTY = 300
_OVERLAP_PENALTY = 250


@dataclass(frozen=True)
class _Rectangle:
    left: float
    top: float
    right: float
    bottom: float

    def expanded(self, amount: float) -> "_Rectangle":
        return _Rectangle(
            self.left - amount,
            self.top - amount,
            self.right + amount,
            self.bottom + amount,
        )


class _RouteOccupancy:
    """Spatial index for already-routed horizontal and vertical segments."""

    def __init__(self) -> None:
        self.horizontal: Dict[float, List[Tuple[float, float]]] = {}
        self.vertical: Dict[float, List[Tuple[float, float]]] = {}

    def add(self, path: Sequence[Point]) -> None:
        for first, second in zip(path, path[1:]):
            if first[1] == second[1]:
                bounds = tuple(sorted((first[0], second[0])))
                self.horizontal.setdefault(first[1], []).append(bounds)
            else:
                bounds = tuple(sorted((first[1], second[1])))
                self.vertical.setdefault(first[0], []).append(bounds)

    def penalty(self, first: Point, second: Point) -> float:
        penalty = 0.0
        if first[1] == second[1]:
            left, right = sorted((first[0], second[0]))
            for other_left, other_right in self.horizontal.get(first[1], ()):
                overlap = max(0.0, min(right, other_right) - max(left, other_left))
                if overlap:
                    penalty += _OVERLAP_PENALTY + overlap * 4
            for x, ranges in self.vertical.items():
                if left < x < right and any(
                    top < first[1] < bottom for top, bottom in ranges
                ):
                    penalty += _CROSSING_PENALTY
        else:
            top, bottom = sorted((first[1], second[1]))
            for other_top, other_bottom in self.vertical.get(first[0], ()):
                overlap = max(0.0, min(bottom, other_bottom) - max(top, other_top))
                if overlap:
                    penalty += _OVERLAP_PENALTY + overlap * 4
            for y, ranges in self.horizontal.items():
                if top < y < bottom and any(
                    left < first[0] < right for left, right in ranges
                ):
                    penalty += _CROSSING_PENALTY
        return penalty


def strongly_connected_components(
    node_ids: Iterable[str], edges: Iterable[Tuple[str, str]]
) -> Tuple[Tuple[str, ...], ...]:
    """Return deterministic Tarjan components for a directed graph."""

    nodes = tuple(node_ids)
    adjacency: Dict[str, Set[str]] = {node_id: set() for node_id in nodes}
    for source, target in edges:
        adjacency[source].add(target)

    index = 0
    indexes: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Set[str] = set()
    components: List[Tuple[str, ...]] = []

    def visit(node_id: str) -> None:
        nonlocal index
        indexes[node_id] = index
        lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)

        for target in sorted(adjacency[node_id]):
            if target not in indexes:
                visit(target)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target])
            elif target in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indexes[target])

        if lowlinks[node_id] == indexes[node_id]:
            component = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node_id:
                    break
            components.append(tuple(sorted(component)))

    for node_id in nodes:
        if node_id not in indexes:
            visit(node_id)
    return tuple(sorted(components, key=lambda component: component[0]))


def layout_directed_graph(
    node_ids: Sequence[str],
    edges: Sequence[Tuple[str, str]],
    sizes: Mapping[str, Tuple[int, int]],
    *,
    direction: str,
    layer_spacing: int,
    node_spacing: int,
    component_spacing: int,
    groups: Optional[Sequence[Tuple[str, ...]]] = None,
) -> Dict[str, Tuple[int, int]]:
    """Place a directed graph using SCC condensation and layered ordering."""

    if not node_ids:
        return {}
    if groups is None:
        groups = strongly_connected_components(node_ids, edges)

    super_members: Dict[str, Tuple[str, ...]] = {}
    node_super: Dict[str, str] = {}
    for index, component in enumerate(groups):
        members = tuple(sorted(component))
        key = f"group:{index}:{members[0]}"
        super_members[key] = members
        for node_id in members:
            node_super[node_id] = key
    missing = set(node_ids) - set(node_super)
    if missing:
        raise ValueError(f"Layout groups omitted nodes: {', '.join(sorted(missing))}")

    adjacency: Dict[str, Set[str]] = {key: set() for key in super_members}
    reverse: Dict[str, Set[str]] = {key: set() for key in super_members}
    for source_id, target_id in edges:
        source = node_super[source_id]
        target = node_super[target_id]
        if source != target:
            adjacency[source].add(target)
            reverse[target].add(source)

    components: List[Tuple[str, ...]] = []
    unseen = set(super_members)
    while unseen:
        start = min(unseen, key=lambda key: super_members[key][0])
        stack = [start]
        members = set()
        while stack:
            current = stack.pop()
            if current in members:
                continue
            members.add(current)
            stack.extend(sorted(adjacency[current] | reverse[current], reverse=True))
        unseen.difference_update(members)
        components.append(tuple(sorted(members, key=lambda key: super_members[key][0])))
    components.sort(key=lambda component: super_members[component[0]][0])

    block_sizes: Dict[str, Tuple[int, int]] = {}
    member_offsets: Dict[str, Dict[str, Tuple[int, int]]] = {}
    grid_gap = max(ROUTING_GAP, node_spacing // 2)
    for key, members in super_members.items():
        columns = max(1, math.ceil(math.sqrt(len(members))))
        rows = math.ceil(len(members) / columns)
        cell_width = max(sizes[member][0] for member in members)
        cell_height = max(sizes[member][1] for member in members)
        block_sizes[key] = (
            columns * cell_width + (columns - 1) * grid_gap,
            rows * cell_height + (rows - 1) * grid_gap,
        )
        member_offsets[key] = {
            member: (
                (index % columns) * (cell_width + grid_gap),
                (index // columns) * (cell_height + grid_gap),
            )
            for index, member in enumerate(members)
        }

    positions: Dict[str, Tuple[int, int]] = {}
    component_cross_offset = 0
    for component in components:
        component_set = set(component)
        indegree = {key: len(reverse[key] & component_set) for key in component}
        queue = [
            (super_members[key][0], key)
            for key, degree in indegree.items()
            if degree == 0
        ]
        heapq.heapify(queue)
        layer = {key: 0 for key in component}
        order: List[str] = []
        while queue:
            _, key = heapq.heappop(queue)
            order.append(key)
            for target in sorted(
                adjacency[key] & component_set,
                key=lambda item: super_members[item][0],
            ):
                layer[target] = max(layer[target], layer[key] + 1)
                indegree[target] -= 1
                if indegree[target] == 0:
                    heapq.heappush(queue, (super_members[target][0], target))

        if len(order) != len(component):
            raise ValueError("Layout groups must collapse every directed cycle")
        layers: Dict[int, List[str]] = {}
        for key in order:
            layers.setdefault(layer[key], []).append(key)
        _order_layers(layers, adjacency, reverse, super_members)

        primary_offsets: Dict[int, int] = {}
        primary = 0
        for layer_index in sorted(layers):
            primary_offsets[layer_index] = primary
            maximum = max(
                block_sizes[key][0 if direction == "right" else 1]
                for key in layers[layer_index]
            )
            primary += maximum + max(layer_spacing, ROUTING_GAP)

        component_cross_size = 0
        for layer_index in sorted(layers):
            cross = component_cross_offset
            for key in layers[layer_index]:
                block_width, block_height = block_sizes[key]
                if direction == "right":
                    block_x, block_y = primary_offsets[layer_index], cross
                    cross += block_height + max(node_spacing, ROUTING_GAP)
                else:
                    block_x, block_y = cross, primary_offsets[layer_index]
                    cross += block_width + max(node_spacing, ROUTING_GAP)
                component_cross_size = max(
                    component_cross_size, cross - component_cross_offset
                )
                for member, (offset_x, offset_y) in member_offsets[key].items():
                    positions[member] = (block_x + offset_x, block_y + offset_y)
        component_cross_offset += component_cross_size + max(
            component_spacing, ROUTING_GAP
        )
    return positions


def _order_layers(
    layers: Dict[int, List[str]],
    adjacency: Mapping[str, Set[str]],
    reverse: Mapping[str, Set[str]],
    super_members: Mapping[str, Tuple[str, ...]],
) -> None:
    layer_for = {
        key: layer_index for layer_index, keys in layers.items() for key in keys
    }

    def positions() -> Dict[str, int]:
        return {
            key: index for keys in layers.values() for index, key in enumerate(keys)
        }

    def reorder(
        layer_index: int,
        neighbors: Mapping[str, Set[str]],
        toward_lower_layers: bool,
    ) -> None:
        ranks = positions()

        def sort_key(key: str) -> Tuple[float, str]:
            relevant = [
                neighbor
                for neighbor in neighbors[key]
                if (
                    layer_for[neighbor] < layer_index
                    if toward_lower_layers
                    else layer_for[neighbor] > layer_index
                )
            ]
            barycenter = (
                sum(ranks[item] for item in relevant) / len(relevant)
                if relevant
                else float(ranks[key])
            )
            return barycenter, super_members[key][0]

        layers[layer_index].sort(key=sort_key)

    layer_indexes = sorted(layers)
    for _ in range(4):
        for layer_index in layer_indexes[1:]:
            reorder(layer_index, reverse, True)
        for layer_index in reversed(layer_indexes[:-1]):
            reorder(layer_index, adjacency, False)


def route_edges(
    node_objects: Mapping[str, Object],
    rendered_edges: Sequence[Tuple[str, str, Edge]],
    *,
    direction: str,
) -> Tuple[Tuple[Point, ...], ...]:
    """Route edges orthogonally around node bounds using stable port allocation."""

    if not rendered_edges:
        return ()
    rectangles = {
        node_id: _Rectangle(
            float(obj.position[0]),
            float(obj.position[1]),
            float(obj.position[0] + obj.width),
            float(obj.position[1] + obj.height),
        )
        for node_id, obj in node_objects.items()
    }
    for _, _, edge in rendered_edges:
        edge.geometry.points = []
        edge.jumpStyle = None
        edge.jumpSize = None

    faces: Dict[Tuple[int, str], str] = {}
    endpoint_groups: Dict[Tuple[str, str], List[Tuple[int, str]]] = {}
    for index, (source_id, target_id, _) in enumerate(rendered_edges):
        source_face, target_face = _preferred_faces(
            rectangles[source_id], rectangles[target_id], direction
        )
        for role, node_id, face in (
            ("source", source_id, source_face),
            ("target", target_id, target_face),
        ):
            endpoint = (index, role)
            faces[endpoint] = face
            endpoint_groups.setdefault((node_id, face), []).append(endpoint)

    ports: Dict[Tuple[int, str], Tuple[Point, Point, float]] = {}
    for (node_id, face), endpoints in sorted(endpoint_groups.items()):
        rectangle = rectangles[node_id]

        def endpoint_key(endpoint: Tuple[int, str]) -> Tuple[float, str, int]:
            index, role = endpoint
            source_id, target_id, _ = rendered_edges[index]
            other_id = target_id if role == "source" else source_id
            other = rectangles[other_id]
            other_center = (
                (other.top + other.bottom) / 2
                if face in {"left", "right"}
                else (other.left + other.right) / 2
            )
            return other_center, other_id, index

        endpoints.sort(key=endpoint_key)
        for rank, endpoint in enumerate(endpoints, start=1):
            fraction = rank / (len(endpoints) + 1)
            port, stub = _port_points(rectangle, face, fraction)
            ports[endpoint] = (port, stub, fraction)

    order = sorted(
        range(len(rendered_edges)),
        key=lambda index: _routing_order_key(rendered_edges[index], rectangles),
    )
    obstacles = [
        rectangle.expanded(ROUTING_CLEARANCE) for rectangle in rectangles.values()
    ]
    occupied_paths: List[List[Point]] = []
    occupancy = _RouteOccupancy()
    routed_paths: Dict[int, List[Point]] = {}
    for index in order:
        _, _, edge = rendered_edges[index]
        source_port, source_stub, source_fraction = ports[(index, "source")]
        target_port, target_stub, target_fraction = ports[(index, "target")]
        _set_edge_port(edge, faces[(index, "source")], source_fraction, source=True)
        _set_edge_port(edge, faces[(index, "target")], target_fraction, source=False)
        middle = _find_orthogonal_route(source_stub, target_stub, obstacles, occupancy)
        path = _simplify_path(
            [source_port, source_stub, *middle[1:-1], target_stub, target_port]
        )
        for point in path[1:-1]:
            edge.add_point_pos(point)  # type: ignore[arg-type]
        if any(_paths_cross(path, prior_path) for prior_path in occupied_paths):
            edge.jumpStyle = "arc"
            edge.jumpSize = 6
        occupied_paths.append(path)
        occupancy.add(path)
        routed_paths[index] = path
    return tuple(tuple(routed_paths[index]) for index in range(len(rendered_edges)))


def _preferred_faces(
    source: _Rectangle, target: _Rectangle, direction: str
) -> Tuple[str, str]:
    if source == target:
        return ("right", "bottom") if direction == "right" else ("bottom", "right")
    source_center = (
        (source.left + source.right) / 2,
        (source.top + source.bottom) / 2,
    )
    target_center = (
        (target.left + target.right) / 2,
        (target.top + target.bottom) / 2,
    )
    delta_x = target_center[0] - source_center[0]
    delta_y = target_center[1] - source_center[1]
    if abs(delta_x) >= abs(delta_y):
        return ("right", "left") if delta_x >= 0 else ("left", "right")
    return ("bottom", "top") if delta_y >= 0 else ("top", "bottom")


def _port_points(
    rectangle: _Rectangle, face: str, fraction: float
) -> Tuple[Point, Point]:
    if face == "left":
        y = rectangle.top + (rectangle.bottom - rectangle.top) * fraction
        return (rectangle.left, y), (rectangle.left - ROUTING_CLEARANCE, y)
    if face == "right":
        y = rectangle.top + (rectangle.bottom - rectangle.top) * fraction
        return (rectangle.right, y), (rectangle.right + ROUTING_CLEARANCE, y)
    if face == "top":
        x = rectangle.left + (rectangle.right - rectangle.left) * fraction
        return (x, rectangle.top), (x, rectangle.top - ROUTING_CLEARANCE)
    x = rectangle.left + (rectangle.right - rectangle.left) * fraction
    return (x, rectangle.bottom), (x, rectangle.bottom + ROUTING_CLEARANCE)


def _set_edge_port(edge: Edge, face: str, fraction: float, *, source: bool) -> None:
    coordinates = {
        "left": (0.0, fraction),
        "right": (1.0, fraction),
        "top": (fraction, 0.0),
        "bottom": (fraction, 1.0),
    }[face]
    if source:
        edge.exitX, edge.exitY = coordinates
    else:
        edge.entryX, edge.entryY = coordinates


def _routing_order_key(
    rendered_edge: Tuple[str, str, Edge], rectangles: Mapping[str, _Rectangle]
) -> Tuple[float, str, str]:
    source_id, target_id, _ = rendered_edge
    source = rectangles[source_id]
    target = rectangles[target_id]
    distance = abs(
        (source.left + source.right) / 2 - (target.left + target.right) / 2
    ) + abs((source.top + source.bottom) / 2 - (target.top + target.bottom) / 2)
    return -distance, source_id, target_id


def _find_orthogonal_route(
    start: Point,
    end: Point,
    obstacles: Sequence[_Rectangle],
    occupancy: _RouteOccupancy,
) -> List[Point]:
    frame_margin = ROUTING_CLEARANCE * 2
    xs = {start[0], end[0]}
    ys = {start[1], end[1]}
    for obstacle in obstacles:
        xs.update((obstacle.left, obstacle.right))
        ys.update((obstacle.top, obstacle.bottom))
    xs.update((min(xs) - frame_margin, max(xs) + frame_margin))
    ys.update((min(ys) - frame_margin, max(ys) + frame_margin))

    valid_points = {
        (x, y) for x in xs for y in ys if not _point_inside_obstacle((x, y), obstacles)
    }
    if start not in valid_points or end not in valid_points:
        raise RuntimeError("Unable to place an edge outside node bounds")

    neighbors: Dict[Point, List[Point]] = {point: [] for point in valid_points}
    by_y: Dict[float, List[float]] = {}
    by_x: Dict[float, List[float]] = {}
    for x, y in valid_points:
        by_y.setdefault(y, []).append(x)
        by_x.setdefault(x, []).append(y)
    for y, row in by_y.items():
        row.sort()
        for left, right in zip(row, row[1:]):
            first, second = (left, y), (right, y)
            if _segment_clear(first, second, obstacles):
                neighbors[first].append(second)
                neighbors[second].append(first)
    for x, column in by_x.items():
        column.sort()
        for top, bottom in zip(column, column[1:]):
            first, second = (x, top), (x, bottom)
            if _segment_clear(first, second, obstacles):
                neighbors[first].append(second)
                neighbors[second].append(first)

    start_state = (start, "")
    costs = {start_state: 0.0}
    previous: Dict[Tuple[Point, str], Tuple[Point, str]] = {}
    pending: List[Tuple[float, float, Point, str]] = [
        (_manhattan(start, end), 0.0, start, "")
    ]
    final_state: Optional[Tuple[Point, str]] = None
    while pending:
        _, cost, point, incoming = heapq.heappop(pending)
        state = (point, incoming)
        if cost != costs.get(state):
            continue
        if point == end:
            final_state = state
            break
        for neighbor in sorted(neighbors[point]):
            segment_direction = "h" if neighbor[1] == point[1] else "v"
            bend = _BEND_PENALTY if incoming and incoming != segment_direction else 0
            next_cost = (
                cost
                + _manhattan(point, neighbor)
                + bend
                + occupancy.penalty(point, neighbor)
            )
            next_state = (neighbor, segment_direction)
            if next_cost < costs.get(next_state, math.inf):
                costs[next_state] = next_cost
                previous[next_state] = state
                estimate = next_cost + _manhattan(neighbor, end)
                heapq.heappush(
                    pending, (estimate, next_cost, neighbor, segment_direction)
                )

    if final_state is None:
        raise RuntimeError("Unable to route an edge around node bounds")
    route = []
    state = final_state
    while True:
        route.append(state[0])
        if state == start_state:
            break
        state = previous[state]
    route.reverse()
    return _simplify_path(route)


def _point_inside_obstacle(point: Point, obstacles: Sequence[_Rectangle]) -> bool:
    x, y = point
    return any(
        obstacle.left < x < obstacle.right and obstacle.top < y < obstacle.bottom
        for obstacle in obstacles
    )


def _segment_clear(
    first: Point, second: Point, obstacles: Sequence[_Rectangle]
) -> bool:
    if first[1] == second[1]:
        left, right = sorted((first[0], second[0]))
        y = first[1]
        return not any(
            obstacle.top < y < obstacle.bottom
            and max(left, obstacle.left) < min(right, obstacle.right)
            for obstacle in obstacles
        )
    top, bottom = sorted((first[1], second[1]))
    x = first[0]
    return not any(
        obstacle.left < x < obstacle.right
        and max(top, obstacle.top) < min(bottom, obstacle.bottom)
        for obstacle in obstacles
    )


def _segments_cross(
    first: Point, second: Point, other_first: Point, other_second: Point
) -> bool:
    first_horizontal = first[1] == second[1]
    other_horizontal = other_first[1] == other_second[1]
    if first_horizontal == other_horizontal:
        return False
    horizontal_first, horizontal_second = (
        (first, second) if first_horizontal else (other_first, other_second)
    )
    vertical_first, vertical_second = (
        (other_first, other_second) if first_horizontal else (first, second)
    )
    horizontal_min, horizontal_max = sorted((horizontal_first[0], horizontal_second[0]))
    vertical_min, vertical_max = sorted((vertical_first[1], vertical_second[1]))
    return (
        horizontal_min < vertical_first[0] < horizontal_max
        and vertical_min < horizontal_first[1] < vertical_max
    )


def _paths_cross(first_path: Sequence[Point], second_path: Sequence[Point]) -> bool:
    return any(
        _segments_cross(first, second, other_first, other_second)
        for first, second in zip(first_path, first_path[1:])
        for other_first, other_second in zip(second_path, second_path[1:])
    )


def _manhattan(first: Point, second: Point) -> float:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _simplify_path(path: Sequence[Point]) -> List[Point]:
    simplified: List[Point] = []
    for point in path:
        if simplified and point == simplified[-1]:
            continue
        if len(simplified) >= 2:
            first, second = simplified[-2:]
            if (first[0] == second[0] == point[0]) or (
                first[1] == second[1] == point[1]
            ):
                simplified[-1] = point
                continue
        simplified.append(point)
    return simplified
