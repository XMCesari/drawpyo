from xml.etree import ElementTree

import pytest

from drawpyo.diagram.edges import Edge
from drawpyo.diagram_types import (
    Decision,
    End,
    FlowChart,
    FlowChartNode,
    Process,
    Start,
)


def _looping_chart(**kwargs):
    chart = FlowChart(**kwargs)
    start = Start(flowchart=chart, value="Start")
    decision = Decision(flowchart=chart, value="Ready?")
    process = Process(flowchart=chart, value="Prepare")
    end = End(flowchart=chart, value="Done")
    start.connect(decision)
    decision.yes(end)
    decision.no(process)
    process.connect(decision)
    return chart, start, decision, process, end


def _overlaps(first, second):
    first_left, first_top = first.position
    second_left, second_top = second.position
    return max(first_left, second_left) < min(
        first_left + first.width, second_left + second.width
    ) and max(first_top, second_top) < min(
        first_top + first.height, second_top + second.height
    )


def test_nodes_register_and_apply_default_shapes_and_overrides():
    chart = FlowChart(file_name="Example.drawio", file_path="output")
    start = Start(flowchart=chart, value="Begin", width=140, fillColor="#ffffff")
    process = Process(flowchart=chart, value="Work")
    decision = Decision(flowchart=chart, value="Choose")
    end = End(flowchart=chart, value="Finish")

    assert chart.objects == [start, process, decision, end]
    assert all(node.page is chart.page for node in chart.objects)
    assert start.width == 140
    assert start.fillColor == "#ffffff"
    assert start.shape == "mxgraph.flowchart.start_1"
    assert process.rounded == 1
    assert decision.shape == "mxgraph.flowchart.decision"
    assert end.shape == "mxgraph.flowchart.terminator"
    assert chart.file_name == "Example.drawio"
    assert chart.file_path == "output"


def test_links_are_typed_registered_and_idempotent():
    chart = FlowChart()
    start = Start(flowchart=chart)
    process = Process(flowchart=chart)
    decision = Decision(flowchart=chart)
    end = End(flowchart=chart)

    first = start.connect(process)
    duplicate = start.connect(process)
    process_edge = process.connect(decision, label="Next")
    yes_edge = decision.yes(end)
    no_edge = decision.no(process)
    custom = decision.connect(end, label="Maybe")

    assert duplicate is first
    assert all(isinstance(edge, Edge) for edge in chart.links)
    assert chart.links == [first, process_edge, yes_edge, no_edge, custom]
    assert yes_edge.label == "Yes"
    assert no_edge.label == "No"
    assert custom.label == "Maybe"
    assert all(edge.page is chart.page for edge in chart.links)


def test_link_semantics_reject_conflicts_and_invalid_targets():
    chart = FlowChart()
    other_chart = FlowChart()
    start = Start(flowchart=chart)
    first = Process(flowchart=chart)
    second = Process(flowchart=chart)
    decision = Decision(flowchart=chart)
    end = End(flowchart=chart)
    foreign = End(flowchart=other_chart)

    start.connect(first)
    with pytest.raises(ValueError, match="only 1 outgoing"):
        start.connect(second)
    decision.yes(first)
    with pytest.raises(ValueError, match="already has a Yes"):
        decision.yes(second)
    with pytest.raises(ValueError, match="non-empty branch label"):
        decision.connect(second)
    with pytest.raises(ValueError, match="cannot have outgoing"):
        end.connect(first)
    with pytest.raises(ValueError, match="cannot cross"):
        decision.no(foreign)
    with pytest.raises(TypeError, match="FlowChartNode"):
        first.connect(object())


@pytest.mark.parametrize("direction", ["down", "right"])
def test_auto_layout_handles_loops_branches_and_disconnected_nodes(direction):
    chart, start, decision, process, end = _looping_chart(direction=direction)
    detached = Process(flowchart=chart, value="Detached")

    chart.auto_layout()

    assert len({node.position for node in chart.objects}) == len(chart.objects)
    assert all(
        not _overlaps(first, second)
        for index, first in enumerate(chart.objects)
        for second in chart.objects[index + 1 :]
    )
    assert len(chart._routed_paths) == len(chart.links)
    assert all(path for path in chart._routed_paths)
    if direction == "down":
        assert start.position[1] < decision.position[1]
    else:
        assert start.position[0] < decision.position[0]
    assert detached.position != start.position
    assert chart.page.width >= 850
    assert chart.page.height >= 1100
    ElementTree.fromstring(chart.file.xml)


def test_auto_layout_is_repeatable_without_duplicating_links_or_waypoints():
    chart, *_ = _looping_chart()

    chart.auto_layout()
    first_positions = [node.position for node in chart.objects]
    first_paths = chart._routed_paths
    first_point_counts = [len(edge.geometry.points) for edge in chart.links]
    chart.auto_layout()

    assert [node.position for node in chart.objects] == first_positions
    assert chart._routed_paths == first_paths
    assert [len(edge.geometry.points) for edge in chart.links] == first_point_counts
    assert len(chart.links) == 4


def test_empty_single_node_and_self_loop_are_supported():
    empty = FlowChart()
    empty.auto_layout()
    assert empty._routed_paths == ()

    single = Process(flowchart=FlowChart(), value="Only")
    single.flowchart.auto_layout()
    assert single.position == (70, 70)

    loop_chart = FlowChart()
    loop = Process(flowchart=loop_chart, value="Retry")
    loop.connect(loop)
    loop_chart.auto_layout()
    assert len(loop_chart._routed_paths) == 1
    assert len(loop_chart._routed_paths[0]) >= 4


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"direction": "left"}, "direction"),
        ({"link_style": "diagonal"}, "link_style"),
        ({"layer_spacing": 0}, "positive integer"),
        ({"node_spacing": True}, "positive integer"),
    ],
)
def test_invalid_options_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        FlowChart(**kwargs)


def test_node_requires_a_flowchart_and_flowchart_rejects_plain_objects():
    with pytest.raises(TypeError, match="flowchart must be"):
        FlowChartNode(flowchart=object())
    with pytest.raises(TypeError, match="only accepts"):
        FlowChart().add_object(object())


def test_write_delegates_to_file(tmp_path):
    chart, *_ = _looping_chart(file_path=tmp_path, file_name="Flow.drawio")
    chart.auto_layout()

    written = chart.write()

    assert written == str(tmp_path / "Flow.drawio")
    assert (tmp_path / "Flow.drawio").is_file()
