import xml.etree.ElementTree as ET
import pytest

import drawpyo
from drawpyo.diagram import Object, Pool, Swimlane


def test_swimlane_vertical_and_horizontal_styles():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    v_lane = Swimlane(
        title="Vertical", orientation="vertical", start_size=30, page=page
    )
    h_lane = Swimlane(
        title="Horizontal", orientation="horizontal", start_size=24, page=page
    )

    assert "swimlane" in v_lane.style
    assert "horizontal=1" in v_lane.style
    assert "startSize=30" in v_lane.style

    assert "swimlane" in h_lane.style
    assert "horizontal=0" in h_lane.style
    assert "startSize=24" in h_lane.style


def test_swimlane_add_and_remove_item():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)
    lane = Swimlane(title="Backend", page=page)
    task = Object(value="API Call", page=page)

    lane.add_item(task, position_rel_to_parent=(20, 40))
    assert task.parent is lane
    assert task in lane.children
    assert task.position_rel_to_parent == (20, 40)

    lane.remove_item(task)
    assert task.parent is None
    assert task not in lane.children


def test_pool_horizontal_stacks_lanes_and_autosizes():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    pool = Pool(
        title="Order Process",
        lanes=["Customer", "Sales", "Fulfillment"],
        orientation="horizontal",
        start_size=30,
        lane_size=100,
        lane_length=400,
        page=page,
    )

    assert len(pool.lanes) == 3
    assert [lane.value for lane in pool.lanes] == ["Customer", "Sales", "Fulfillment"]
    assert pool.width == 430
    assert pool.height == 300
    assert [lane.geometry.x for lane in pool.lanes] == [30, 30, 30]
    assert [lane.geometry.y for lane in pool.lanes] == [0, 100, 200]
    assert "childLayout=stackLayout" in pool.style
    assert "horizontal=0" in pool.style
    assert "horizontalStack=0" in pool.style

    pool.remove_lane("Sales")
    assert [lane.value for lane in pool.lanes] == ["Customer", "Fulfillment"]
    assert pool.height == 200
    assert [lane.geometry.y for lane in pool.lanes] == [0, 100]

    # Verify exported XML is well-formed
    root = ET.fromstring(file.xml)
    swimlane_cells = [
        c for c in root.iter("mxCell") if "swimlane" in (c.get("style") or "")
    ]
    assert len(swimlane_cells) == 3  # 1 pool + 2 remaining lanes


def test_pool_vertical_stacks_lanes_side_by_side():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    pool = Pool(
        title="Columns",
        lanes=["Todo", "Done"],
        orientation="vertical",
        start_size=30,
        lane_size=150,
        lane_length=300,
        page=page,
    )

    assert pool.width == 300
    assert pool.height == 330
    assert [lane.geometry.x for lane in pool.lanes] == [0, 150]
    assert [lane.geometry.y for lane in pool.lanes] == [30, 30]
    assert "horizontal=1" in pool.style
    assert "horizontalStack=1" in pool.style


def test_invalid_orientation_and_lane_type_raise():
    with pytest.raises(ValueError, match="orientation"):
        Swimlane(orientation="diagonal")
    with pytest.raises(ValueError, match="orientation"):
        Pool(orientation="diagonal")

    pool = Pool()
    with pytest.raises(TypeError, match="lane must be a string title or a Swimlane"):
        pool.add_lane(123)  # type: ignore[arg-type]


def test_pool_add_existing_swimlane_aligns_orientation_and_remove_cleans_children():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    pool = Pool(
        title="Process",
        orientation="horizontal",
        start_size=30,
        lane_size=100,
        lane_length=400,
        collapsible=0,
        page=page,
    )
    assert "collapsible=0" in pool.style

    # Default Swimlane has orientation="vertical"; adding to a horizontal Pool aligns it
    lane = Swimlane(title="Existing", collapsible=1, page=page)
    assert "collapsible=1" in lane.style
    pool.add_lane(lane, size=120)
    assert lane.orientation == "horizontal"
    assert lane.horizontal == 0
    assert "horizontal=0" in lane.style

    task = Object(value="Step 1", page=page)
    lane.add_item(task)
    assert task in page.objects

    pool.remove_lane(lane)
    assert pool.lanes == []
    assert task not in page.objects
    assert task.parent is None
    assert pool.width == 430
    assert pool.height == 100
