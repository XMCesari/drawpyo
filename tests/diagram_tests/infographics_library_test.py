import pytest

import drawpyo
from drawpyo.diagram.objects import base_libraries, object_from_library

EXPECTED_INFOGRAPHICS_SHAPES = {
    "pie": ("mxgraph.basic.pie", 120, 120, "fixed"),
    "arc": ("mxgraph.basic.arc", 120, 120, "fixed"),
    "part_conc_ellipse": ("mxgraph.basic.partConcEllipse", 100, 100, "fixed"),
    "parallelogram": ("mxgraph.infographic.parallelogram", 100, 70, None),
    "ribbon_simple": ("mxgraph.infographic.ribbonSimple", 200, 40, None),
    "ribbon_rolled": ("mxgraph.infographic.ribbonRolled", 200, 70, None),
    "ribbon_double_folded": ("mxgraph.infographic.ribbonDoubleFolded", 200, 70, None),
    "ribbon_front_folded": ("mxgraph.infographic.ribbonFrontFolded", 200, 55, None),
    "banner": ("mxgraph.infographic.banner", 260, 70, None),
    "banner_single_fold": ("mxgraph.infographic.bannerSingleFold", 260, 70, None),
    "banner_half_fold": ("mxgraph.infographic.bannerHalfFold", 200, 200, None),
    "bar_callout": ("mxgraph.infographic.barCallout", 200, 70, None),
    "flag": ("mxgraph.infographic.flag", 200, 70, None),
}


def test_infographics_library_contains_all_reference_shapes():
    infographics = base_libraries["infographics"]
    assert set(EXPECTED_INFOGRAPHICS_SHAPES).issubset(infographics.keys())


@pytest.mark.parametrize(
    "shape_name,expected_spec", EXPECTED_INFOGRAPHICS_SHAPES.items()
)
def test_object_from_infographics_library(shape_name: str, expected_spec: tuple):
    expected_shape, expected_width, expected_height, expected_aspect = expected_spec
    file = drawpyo.File()
    page = drawpyo.Page(file=file)

    obj = object_from_library(
        library="infographics", obj_name=shape_name, page=page, value="Label"
    )

    assert obj.shape == expected_shape
    assert obj.width == expected_width
    assert obj.height == expected_height
    assert f"shape={expected_shape}" in obj.style
    assert f"shape={expected_shape}" in obj.xml
    if expected_aspect is not None:
        assert obj.aspect == expected_aspect
        assert f"aspect={expected_aspect}" in obj.style
        assert f"aspect={expected_aspect}" in obj.xml
    else:
        assert obj.aspect is None
        assert "aspect=" not in obj.style
