import pytest

from drawpyo.diagram_types.tree import NodeObject, TreeDiagram, TreeGroup


class CustomTreeGroup(TreeGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.centered_parent = False

    def center_parent(self):
        self.centered_parent = True
        super().center_parent()


def _tree_with_parent_and_child(**kwargs):
    tree = TreeDiagram(**kwargs)
    parent = NodeObject(tree=tree, value="parent")
    child = NodeObject(tree=tree, value="child")
    parent.add_child(child)
    return tree


def test_auto_layout_uses_tree_group_by_default():
    tree = _tree_with_parent_and_child()

    top_group = tree.auto_layout()

    assert isinstance(top_group, TreeGroup)
    assert type(top_group) is TreeGroup


def test_auto_layout_uses_factory_for_every_group():
    groups = []

    def group_factory(*, tree):
        group = CustomTreeGroup(tree=tree)
        groups.append(group)
        return group

    tree = _tree_with_parent_and_child(group_factory=group_factory)
    top_group = tree.auto_layout()

    assert top_group is groups[0]
    assert len(groups) == 3
    assert len({id(group) for group in groups}) == len(groups)
    assert all(isinstance(group, CustomTreeGroup) for group in groups)
    assert all(group.tree is tree for group in groups)
    assert sum(group.centered_parent for group in groups) == 1


def test_tree_diagram_rejects_non_callable_group_factory():
    with pytest.raises(TypeError, match="group_factory must be callable"):
        TreeDiagram(group_factory=None)


def test_tree_diagram_accepts_existing_file_and_page_name():
    from drawpyo import File

    shared_file = File(file_path="/tmp", file_name="multi.drawio")
    tree_a = TreeDiagram(file=shared_file, page_name="Overview")
    tree_b = TreeDiagram(file=shared_file, page_name="Details")

    assert tree_a.file is shared_file
    assert tree_b.file is shared_file
    assert tree_a.file_name == "multi.drawio"
    assert tree_a.file_path == "/tmp"
    assert len(shared_file.pages) == 2
    assert [p.name for p in shared_file.pages] == ["Overview", "Details"]
    assert tree_a.page.name == "Overview"
    assert tree_b.page.name == "Details"


def test_tree_diagram_page_name_without_existing_file():
    tree = TreeDiagram(file_name="single.drawio", page_name="Main Tree")

    assert tree.file_name == "single.drawio"
    assert tree.page.name == "Main Tree"
    assert len(tree.file.pages) == 1


@pytest.mark.parametrize(
    "extra_kwargs",
    [
        {"file_name": "other.drawio"},
        {"file_path": "/tmp"},
        {"file_name": "other.drawio", "file_path": "/tmp"},
    ],
)
def test_tree_diagram_rejects_file_with_file_name_or_path(extra_kwargs):
    from drawpyo import File

    shared_file = File()
    with pytest.raises(ValueError, match="Cannot specify 'file' together with"):
        TreeDiagram(file=shared_file, **extra_kwargs)


def test_tree_diagram_rejects_non_file_instance():
    with pytest.raises(TypeError, match="file must be a File instance"):
        TreeDiagram(file="not_a_file")
