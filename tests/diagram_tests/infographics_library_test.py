import pytest

import drawpyo
from drawpyo.diagram.objects import base_libraries, object_from_library

EXPECTED_INFOGRAPHICS_SHAPES = {
    "pie": "mxgraph.basic.pie",
    "arc": "mxgraph.basic.arc",
    "part_conc_ellipse": "mxgraph.basic.partConcEllipse",
    "parallelogram": "mxgraph.infographic.parallelogram",
    "ribbon_simple": "mxgraph.infographic.ribbonSimple",
    "ribbon_rolled": "mxgraph.infographic.ribbonRolled",
    "ribbon_double_folded": "mxgraph.infographic.ribbonDoubleFolded",
    "ribbon_front_folded": "mxgraph.infographic.ribbonFrontFolded",
    "banner": "mxgraph.infographic.banner",
    "banner_single_fold": "mxgraph.infographic.bannerSingleFold",
    "banner_half_fold": "mxgraph.infographic.bannerHalfFold",
    "bar_callout": "mxgraph.infographic.barCallout",
    "flag": "mxgraph.infographic.flag",
}


def test_infographics_library_contains_all_reference_shapes():
    infographics = base_libraries["infographics"]
    assert set(EXPECTED_INFOGRAPHICS_SHAPES).issubset(infographics.keys())


@pytest.mark.parametrize(
    "shape_name,expected_shape", EXPECTED_INFOGRAPHICS_SHAPES.items()
)
def test_object_from_infographics_library(shape_name: str, expected_shape: str):
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    obj = object_from_library(
        library="infographics", obj_name=shape_name, page=page, value="Label"
    )

    assert obj.shape == expected_shape
    assert f"shape={expected_shape}" in obj.style
    assert obj.width > 0
    assert obj.height > 0
