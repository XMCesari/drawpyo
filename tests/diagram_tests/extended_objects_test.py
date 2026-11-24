"""Tests for extended diagram objects."""

import xml.etree.ElementTree as ET

import drawpyo
import pytest


def test_table_builds_header_rows_and_geometry(empty_page: drawpyo.Page) -> None:
    table = drawpyo.diagram.Table(
        page=empty_page,
        position=(40, 60),
        headers=["Name", "Owner"],
        rows=[["API", "Backend"], ["Database", "Platform"]],
        column_widths=[100, 160],
        row_height=35,
        header_height=40,
    )

    assert table.headers == ["Name", "Owner"]
    assert table.rows == [["API", "Backend"], ["Database", "Platform"]]
    assert table.position == (40, 60)
    assert (table.width, table.height) == (260, 110)
    assert len(table.children) == 3

    expected_y_and_height = [(0, 40), (40, 35), (75, 35)]
    for row, (expected_y, expected_height) in zip(
        table.children, expected_y_and_height
    ):
        assert row.parent is table
        assert row.position_rel_to_parent == (0, expected_y)
        assert (row.width, row.height) == (260, expected_height)
        assert [cell.geometry.x for cell in row.children] == [0, 100]
        assert [cell.width for cell in row.children] == [100, 160]
        assert all(cell.height == expected_height for cell in row.children)
        assert all(cell.parent is row for cell in row.children)

    assert table in empty_page.objects
    assert all(row in empty_page.objects for row in table.children)
    assert all(
        cell in empty_page.objects for row in table.children for cell in row.children
    )


def test_table_without_headers_infers_columns_from_rows(
    empty_page: drawpyo.Page,
) -> None:
    table = drawpyo.diagram.Table(
        page=empty_page,
        rows=[["A", "B", "C"]],
    )

    assert table.headers == []
    assert table.rows == [["A", "B", "C"]]
    assert table.column_widths == [120, 120, 120]
    assert (table.width, table.height) == (360, 30)
    assert len(table.children) == 1


def test_table_can_start_without_data_rows(empty_page: drawpyo.Page) -> None:
    header_table = drawpyo.diagram.Table(page=empty_page, headers=["A", "B"])
    width_table = drawpyo.diagram.Table(page=empty_page, column_widths=[90, 110])

    assert header_table.rows == []
    assert (header_table.width, header_table.height) == (240, 30)
    assert width_table.headers == []
    assert width_table.rows == []
    assert (width_table.width, width_table.height) == (200, 0)


def test_table_mutations_update_values_geometry_and_page(
    empty_page: drawpyo.Page,
) -> None:
    table = drawpyo.diagram.Table(
        page=empty_page,
        headers=["Name", "State"],
        rows=[["API", "Active"]],
    )
    initial_page_count = len(empty_page.objects)

    table.add_row(["Database", "Planned"])
    assert table.rows == [["API", "Active"], ["Database", "Planned"]]
    assert table.height == 90
    assert len(empty_page.objects) == initial_page_count + 3

    table.set_cell(0, 1, "Completed")
    assert table.rows[0] == ["API", "Completed"]
    assert table.height == 90

    removed_row = table.children[-1]
    removed_cells = list(removed_row.children)
    table.remove_row(1)
    assert table.rows == [["API", "Completed"]]
    assert table.height == 60
    assert removed_row not in table.children
    assert removed_row not in empty_page.objects
    assert all(cell not in empty_page.objects for cell in removed_cells)


def test_assigning_table_page_moves_complete_hierarchy() -> None:
    first_page = drawpyo.Page()
    second_page = drawpyo.Page()
    table = drawpyo.diagram.Table(
        headers=["Name", "State"],
        rows=[["API", "Active"]],
    )
    components = [
        table,
        *table.children,
        *(cell for row in table.children for cell in row.children),
    ]

    table.page = first_page
    assert all(component in first_page.objects for component in components)
    assert all(component.page is first_page for component in components)

    table.page = second_page
    assert all(component not in first_page.objects for component in components)
    assert all(component in second_page.objects for component in components)
    assert all(component.page is second_page for component in components)


def test_table_layout_and_styles_can_be_updated(empty_page: drawpyo.Page) -> None:
    table = drawpyo.diagram.Table(
        page=empty_page,
        headers=["A", "B"],
        rows=[["1", "2"]],
    )

    table.column_widths = [80, 140]
    table.row_height = 45
    table.header_height = 25
    table.border_color = "#123456"
    table.background_color = "#ABCDEF"
    table.header_background_color = "#FEDCBA"
    table.header_text_format = drawpyo.diagram.TextFormat(bold=True, align="left")
    table.cell_text_format = drawpyo.diagram.TextFormat(align="right")

    assert (table.width, table.height) == (220, 70)
    assert [cell.width for cell in table.children[0].children] == [80, 140]
    assert table.children[0].height == 25
    assert table.children[1].height == 45
    assert table.strokeColor == "#123456"
    assert all(cell.fillColor == "#FEDCBA" for cell in table.children[0].children)
    assert all(cell.fillColor == "#ABCDEF" for cell in table.children[1].children)
    assert all(cell.text_format.align == "left" for cell in table.children[0].children)
    assert all(cell.text_format.bold for cell in table.children[0].children)
    assert all(cell.text_format.align == "right" for cell in table.children[1].children)

    table.add_row(["3", "4"])
    assert [cell.width for cell in table.children[-1].children] == [80, 140]
    assert table.children[-1].height == 45
    assert all(cell.fillColor == "#ABCDEF" for cell in table.children[-1].children)
    assert all(
        cell.text_format.align == "right" for cell in table.children[-1].children
    )


@pytest.mark.parametrize(
    ("kwargs", "exception"),
    [
        ({}, ValueError),
        ({"headers": "A"}, TypeError),
        ({"headers": ["A", 1]}, TypeError),
        ({"rows": "A"}, TypeError),
        ({"rows": [["A", "B"], ["C"]]}, ValueError),
        ({"headers": ["A"], "rows": [["A", "B"]]}, ValueError),
        ({"headers": ["A"], "column_widths": [0]}, ValueError),
        ({"headers": ["A"], "row_height": True}, ValueError),
        ({"headers": ["A"], "header_height": -1}, ValueError),
        ({"headers": ["A"], "border_color": 1}, TypeError),
        ({"headers": ["A"], "header_text_format": "bold"}, TypeError),
    ],
)
def test_table_rejects_invalid_constructor_input_without_page_mutation(
    empty_page: drawpyo.Page, kwargs: dict, exception: type[Exception]
) -> None:
    initial_objects = list(empty_page.objects)

    with pytest.raises(exception):
        drawpyo.diagram.Table(page=empty_page, **kwargs)

    assert empty_page.objects == initial_objects


def test_table_mutations_validate_before_changing_state(
    empty_page: drawpyo.Page,
) -> None:
    table = drawpyo.diagram.Table(
        page=empty_page,
        headers=["A", "B"],
        rows=[["1", "2"]],
    )
    original_rows = table.rows
    original_objects = list(empty_page.objects)

    with pytest.raises(ValueError):
        table.add_row(["too short"])
    with pytest.raises(IndexError):
        table.remove_row(-1)
    with pytest.raises(IndexError):
        table.set_cell(4, 0, "x")
    with pytest.raises(IndexError):
        table.set_cell(0, 4, "x")
    with pytest.raises(TypeError):
        table.set_cell(0, 0, 42)
    with pytest.raises(ValueError):
        table.column_widths = [100]

    assert table.rows == original_rows
    assert empty_page.objects == original_objects


def test_table_exports_native_drawio_hierarchy(tmp_path) -> None:
    file = drawpyo.File(file_path=str(tmp_path), file_name="table.drawio")
    page = drawpyo.Page(file=file)
    table = drawpyo.diagram.Table(
        page=page,
        headers=["Name", "Status"],
        rows=[["API & UI", "Active"]],
        column_widths=[150, 90],
    )

    output_path = file.write()
    root = ET.parse(output_path)
    table_xml = root.find(f".//mxCell[@id='{table.id}']")
    assert table_xml is not None
    assert table_xml.get("parent") == "1"
    assert "shape=table" in table_xml.get("style", "")
    assert "container=1" in table_xml.get("style", "")
    assert "childLayout=tableLayout" in table_xml.get("style", "")

    row_xml = root.find(f".//mxCell[@id='{table.children[0].id}']")
    assert row_xml is not None
    assert row_xml.get("parent") == str(table.id)
    assert "shape=tableRow" in row_xml.get("style", "")

    cell = table.children[1].children[0]
    cell_xml = root.find(f".//mxCell[@id='{cell.id}']")
    assert cell_xml is not None
    assert cell_xml.get("parent") == str(table.children[1].id)
    assert cell_xml.get("value") == "API & UI"
    assert "shape=partialRectangle" in cell_xml.get("style", "")
    geometry = cell_xml.find("mxGeometry")
    assert geometry is not None
    assert geometry.get("width") == "150"
    assert geometry.get("height") == "30"
