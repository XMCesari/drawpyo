from typing import List as ListType, Optional, Any, Union
from .objects import Object, object_from_library

# These classes extend the basic diagram classes (Object or Edge) with a little bit of custom functionality for ergonomics or ease of use.


class List(Object):
    def __init__(
        self, title: str = "List", list_items: ListType[str] = [], **kwargs: Any
    ) -> None:
        """The List object wraps the basic Object type but allows easier managing of a list object and its members. All of the arguments and keyword arguments for Object are available here as well.

        Args:
            title (str, optional): The name in the heading of the list. Defaults to "List".
            list_items (list of strings, optional): A Python list of strings denoting the items. Defaults to empty.
        """
        super().__init__(value=title, **kwargs)
        self.format_as_library_object(library="general", obj_name="list")
        self.autosizing: bool = kwargs.get("autosizing", True)
        self.width: Union[int, float] = kwargs.get("width", 120)
        self.list_items: Optional[List[str]] = list_items

    @property
    def list_items(self) -> ListType[str]:
        """A Python list of strings of the objects in the list.

        Returns:
            list of strings: The list items
        """
        return [child.value for child in self.children]

    @list_items.setter
    def list_items(self, value: ListType[str]) -> None:
        if not isinstance(value, list):
            raise TypeError("list_items must be a list!")
        self.children = []
        for item in value:
            self.add_item(item)

    def add_item(self, item_text: str) -> None:
        """This function creates a new Draw.io text item and adds it to the end of the list.

        Args:
            item_text (string): The name of the item to add.
        """
        new_item = object_from_library(
            library="general", obj_name="list_item", page=self.page
        )
        new_item.value = item_text
        new_item.parent = self
        new_item.width = self.width
        new_item.geometry.y = len(self.list_items) * new_item.height
        if self.autosizing:
            self.autosize()

    def remove_item(self, item_text: str) -> None:
        """This function removes any list items matching the text passed into the function.

        Args:
            item_text (string): The text of the list item to remove.
        """
        for child in self.children:
            if child.value == item_text:
                self.remove_object(child)
                self.page.remove_object(child)
                del child
        if self.autosizing:
            self.autosize()

    def autosize(self) -> None:
        """This function resizes the parent List object to match the length of the list of items. It also restacks the list items to fill any gaps from deleted items."""
        y_pos = self.startSize
        for child in self.children:
            child.geometry.y = y_pos
            y_pos = y_pos + child.height
        self.height = self.startSize + sum(child.height for child in self.children)
        self.width = min(child.width for child in self.children)

    @property
    def width(self) -> Union[int, float]:
        """The width of the object. The difference between List's width and Object's width is that when the List.width is set all of the child objects will be set to the same width.

        Returns:
            Union[int, float]: The width of the list object
        """
        return self.geometry.width

    @width.setter
    def width(self, value: Union[int, float]) -> None:
        for child in self.children:
            child.width = value
        self.geometry.width = value
        self.update_parent()


class PieSlice(Object):
    def __init__(
        self,
        value: str = "",
        slice_value: float = 2.0,
        **kwargs: Any,
    ) -> None:
        """The PieSlice object wraps the basic Object type but allows easier managing of a pie chart slice. All of the arguments and keyword arguments for Object are available here as well.

        Args:
            title (str, optional): The name of the pie slice. Defaults to "Slice".
            slice_value (float, optional): The numeric value of the pie slice. Defaults to 1.0.
            startAngle (float, optional): The starting angle of the pie slice in degrees. Defaults to 0.0.
        """
        super().__init__(value=value, **kwargs)
        self.format_as_library_object(library="infographics", obj_name="pie")
        self._style_attributes.append("startAngle")
        self._style_attributes.append("endAngle")
        self.slice_value: float = slice_value
        self.size: Union[int, float] = kwargs.get("size", 120)
        self.startAngle: float = kwargs.get("startAngle", 0.0)
        self.endAngle: float = (self.startAngle + slice_value) % 1

    @property
    def size(self) -> Union[int, float]:
        """The size (width and height) of the pie slice.

        Returns:
            Union[int, float]: The size
        """
        return self.geometry.width

    @size.setter
    def size(self, value: Union[int, float]) -> None:
        self.geometry.width = float(value)
        self.geometry.height = float(value)
        self.update_parent()


class Swimlane(Object):
    """A Draw.io swimlane container object with a header bar."""

    def __init__(
        self,
        title: str = "Swimlane",
        orientation: str = "vertical",
        start_size: Union[int, float] = 23,
        **kwargs: Any,
    ) -> None:
        if orientation not in ("vertical", "horizontal"):
            raise ValueError(
                f"orientation must be 'vertical' or 'horizontal', got {orientation!r}"
            )
        kwargs.setdefault("width", 200)
        kwargs.setdefault("height", 200)
        super().__init__(value=title, **kwargs)
        self.baseStyle = "swimlane"
        for attr in ("startSize", "horizontal", "collapsible"):
            if attr not in self._style_attributes:
                self._style_attributes.append(attr)
        self.orientation: str = orientation
        self.startSize: Union[int, float] = start_size
        # In Draw.io, horizontal=1 means a horizontal (top) header (vertical lane);
        # horizontal=0 means a vertical (left) header (horizontal lane).
        self.horizontal: int = 1 if orientation == "vertical" else 0
        self.collapsible: int = kwargs.get("collapsible", 0)

    def add_item(
        self,
        obj: Object,
        position_rel_to_parent: Optional[tuple] = None,
    ) -> Object:
        """Add an Object inside this swimlane."""
        if self.page is not None and obj.page is None:
            obj.page = self.page
        obj.parent = self
        if position_rel_to_parent is not None:
            obj.position_rel_to_parent = position_rel_to_parent
        return obj

    def remove_item(self, obj: Object) -> None:
        """Remove an Object from this swimlane."""
        if obj in self.children:
            self.remove_object(obj)


class Pool(Object):
    """A Draw.io swimlane pool that stacks Swimlane children horizontally or vertically."""

    def __init__(
        self,
        title: str = "Pool",
        lanes: Optional[ListType[Union[str, Swimlane]]] = None,
        orientation: str = "horizontal",
        start_size: Union[int, float] = 30,
        lane_size: Union[int, float] = 120,
        lane_length: Union[int, float] = 400,
        autosizing: bool = True,
        **kwargs: Any,
    ) -> None:
        if orientation not in ("horizontal", "vertical"):
            raise ValueError(
                f"orientation must be 'horizontal' or 'vertical', got {orientation!r}"
            )
        self.orientation: str = orientation
        self.lane_size: Union[int, float] = lane_size
        self.lane_length: Union[int, float] = lane_length
        self.autosizing: bool = autosizing

        if orientation == "horizontal":
            kwargs.setdefault("width", start_size + lane_length)
            kwargs.setdefault("height", lane_size)
        else:
            kwargs.setdefault("width", lane_size)
            kwargs.setdefault("height", start_size + lane_length)

        super().__init__(value=title, **kwargs)
        self.baseStyle = "swimlane"
        for attr in (
            "childLayout",
            "startSize",
            "horizontal",
            "horizontalStack",
            "resizeParent",
            "resizeParentMax",
            "resizeLast",
            "collapsible",
            "marginBottom",
        ):
            if attr not in self._style_attributes:
                self._style_attributes.append(attr)

        self.childLayout: str = "stackLayout"
        self.startSize: Union[int, float] = start_size
        self.horizontal: int = 0 if orientation == "horizontal" else 1
        self.horizontalStack: int = 0 if orientation == "horizontal" else 1
        self.resizeParent: int = 1
        self.resizeParentMax: int = 0
        self.resizeLast: int = 0
        self.collapsible: int = kwargs.get("collapsible", 1)
        self.marginBottom: int = 0

        if lanes:
            for lane in lanes:
                self.add_lane(lane)

    @property
    def lanes(self) -> ListType[Swimlane]:
        """Return all Swimlane children belonging to this pool."""
        return [child for child in self.children if isinstance(child, Swimlane)]

    def add_lane(
        self,
        lane: Union[str, Swimlane],
        size: Optional[Union[int, float]] = None,
    ) -> Swimlane:
        """Add a lane by title or Swimlane instance and restack lanes."""
        lane_dim = size if size is not None else self.lane_size
        if isinstance(lane, str):
            lane_obj = Swimlane(
                title=lane,
                orientation=self.orientation,
                page=self.page,
                width=(
                    self.lane_length if self.orientation == "horizontal" else lane_dim
                ),
                height=(
                    lane_dim if self.orientation == "horizontal" else self.lane_length
                ),
            )
        elif isinstance(lane, Swimlane):
            lane_obj = lane
            if self.page is not None and lane_obj.page is None:
                lane_obj.page = self.page
            if size is not None:
                if self.orientation == "horizontal":
                    lane_obj.height = lane_dim
                else:
                    lane_obj.width = lane_dim
        else:
            raise TypeError("lane must be a string title or a Swimlane instance.")

        lane_obj.parent = self
        self.layout_lanes()
        return lane_obj

    def remove_lane(self, lane: Union[str, Swimlane]) -> None:
        """Remove a lane by Swimlane instance or matching title and restack."""
        targets = (
            [child for child in self.lanes if child.value == lane]
            if isinstance(lane, str)
            else [lane] if lane in self.lanes else []
        )
        for target in targets:
            self.remove_object(target)
            if self.page is not None and target in self.page.objects:
                self.page.remove_object(target)
        self.layout_lanes()

    def layout_lanes(self) -> None:
        """Stack lanes sequentially inside the pool and optionally resize the pool."""
        lanes = self.lanes
        if not lanes:
            return

        if self.orientation == "horizontal":
            y_offset: Union[int, float] = 0
            max_width = max(lane.width for lane in lanes)
            for lane in lanes:
                lane.width = max_width
                lane.geometry.x = self.startSize
                lane.geometry.y = y_offset
                y_offset += lane.height
            if self.autosizing:
                self.width = self.startSize + max_width
                self.height = y_offset
        else:
            x_offset: Union[int, float] = 0
            max_height = max(lane.height for lane in lanes)
            for lane in lanes:
                lane.height = max_height
                lane.geometry.x = x_offset
                lane.geometry.y = self.startSize
                x_offset += lane.width
            if self.autosizing:
                self.width = x_offset
                self.height = self.startSize + max_height
