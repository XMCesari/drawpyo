import xml.etree.ElementTree as ET

import drawpyo
from drawpyo.diagram import Object


def test_object_url_link_wraps_in_user_object_and_escapes_xml():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)
    obj = Object(
        value="Docs",
        page=page,
        link="https://example.com/search?a=1&b=2",
    )

    xml_str = obj.xml
    assert "<UserObject " in xml_str
    assert 'link="https://example.com/search?a=1&amp;b=2"' in xml_str
    assert "</UserObject>" in xml_str

    root = ET.fromstring(file.xml)
    user_objs = list(root.iter("UserObject"))
    assert len(user_objs) == 1
    assert user_objs[0].get("label") == "Docs"
    assert user_objs[0].get("link") == "https://example.com/search?a=1&b=2"


def test_object_page_link_uses_drawio_page_id_format():
    file = drawpyo.File()
    page1 = drawpyo.Page(file=file, name="Overview")
    page2 = drawpyo.Page(file=file, name="Details")
    obj = Object(value="Go to Details", page=page1, link=page2)

    expected = f"data:page/id,{page2.id}"
    assert f'link="{expected}"' in obj.xml

    root = ET.fromstring(file.xml)
    user_objs = list(root.iter("UserObject"))
    assert len(user_objs) == 1
    assert user_objs[0].get("link") == expected


def test_object_link_combines_with_tag_and_tooltip_and_can_be_cleared():
    file = drawpyo.File()
    page = drawpyo.Page(file=file)
    obj = Object(
        value="Node",
        page=page,
        tag="important",
        tooltip="Click to open",
        link="https://drawpyo.example.org",
    )

    xml_str = obj.xml
    assert 'tags="important"' in xml_str
    assert 'tooltip="Click to open"' in xml_str
    assert 'link="https://drawpyo.example.org"' in xml_str

    obj.link = None
    obj.tag = None
    obj.tooltip = None
    assert "<UserObject" not in obj.xml
