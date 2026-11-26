from copy import deepcopy
from typing import Any, List as ListType, Optional, Union

from ..utils.standard_colors import StandardColor
from .objects import Object, object_from_library
from .text_format import TextFormat

__all__ = ["List", "PieSlice", "Table"]

Number = Union[int, float]
Color = Union[str, StandardColor]

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


class Table(Object):
    """An editable Draw.io table with optional column headers.

    ``Table`` uses Draw.io's native table, row, and cell hierarchy. Data-row
    indices are zero based and do not include the optional header row.

    Args:
        headers: Optional list of column headings.
        rows: Optional rectangular list of data rows.
        column_widths: Width of each column. Defaults to 120 pixels per column.
        row_height: Height of each data row. Defaults to 30 pixels.
        header_height: Header row height. Defaults to ``row_height``.
        border_color: Table border color. Defaults to black.
        background_color: Data-cell background color. Defaults to white.
        header_background_color: Header-cell background color. Defaults to gray.
        header_text_format: Formatting copied to each header cell.
        cell_text_format: Formatting copied to each data cell.

    All keyword arguments accepted by :class:`Object`, including ``page`` and
    ``position``, are also accepted.
    """

    DEFAULT_COLUMN_WIDTH = 120

    def __init__(
        self,
        headers: Optional[ListType[str]] = None,
        rows: Optional[ListType[ListType[str]]] = None,
        *,
        column_widths: Optional[ListType[Number]] = None,
        row_height: Number = 30,
        header_height: Optional[Number] = None,
        border_color: Color = "#000000",
        background_color: Color = "#FFFFFF",
        header_background_color: Color = "#F5F5F5",
        header_text_format: Optional[TextFormat] = None,
        cell_text_format: Optional[TextFormat] = None,
        **kwargs: Any,
    ) -> None:
        normalized_headers = self._validate_values(headers, "headers", optional=True)
        normalized_rows = self._validate_rows(rows)

        column_count = self._determine_column_count(
            normalized_headers, normalized_rows, column_widths
        )
        for row in normalized_rows:
            if len(row) != column_count:
                raise ValueError("all rows must contain the same number of cells")
        if normalized_headers and len(normalized_headers) != column_count:
            raise ValueError("headers must match the table's column count")

        if column_widths is None:
            normalized_widths = [self.DEFAULT_COLUMN_WIDTH] * column_count
        else:
            if not isinstance(column_widths, list):
                raise TypeError("column_widths must be a list")
            if len(column_widths) != column_count:
                raise ValueError("column_widths must match the table's column count")
            normalized_widths = [
                self._validate_dimension(value, "column width")
                for value in column_widths
            ]

        normalized_row_height = self._validate_dimension(row_height, "row_height")
        normalized_header_height = self._validate_dimension(
            row_height if header_height is None else header_height, "header_height"
        )
        self._validate_color(border_color, "border_color")
        self._validate_color(background_color, "background_color")
        self._validate_color(header_background_color, "header_background_color")
        self._validate_text_format(header_text_format, "header_text_format")
        self._validate_text_format(cell_text_format, "cell_text_format")

        self._column_count = column_count
        self._column_widths = normalized_widths
        self._row_height = normalized_row_height
        self._header_height = normalized_header_height
        self._border_color = border_color
        self._background_color = background_color
        self._header_background_color = header_background_color
        self._header_text_format = deepcopy(
            header_text_format
            if header_text_format is not None
            else TextFormat(bold=True, align="center", verticalAlign="middle")
        )
        self._cell_text_format = deepcopy(
            cell_text_format
            if cell_text_format is not None
            else TextFormat(align="left", verticalAlign="middle", spacingLeft=4)
        )
        self._header_row: Optional[Object] = None
        self._data_row_objects: ListType[Object] = []

        value = kwargs.pop("value", "")
        super().__init__(value=value, **kwargs)
        self.format_as_library_object(library="general", obj_name="table")
        self.strokeColor = border_color
        self.fillColor = background_color

        if normalized_headers:
            self._header_row = self._create_row(normalized_headers, is_header=True)
        for row in normalized_rows:
            self._data_row_objects.append(self._create_row(row, is_header=False))
        self._layout()

    @property
    def page(self) -> Optional[Any]:
        """The page containing the table and all of its generated objects."""

        return self._page

    @page.setter
    def page(self, page: Optional[Any]) -> None:
        previous_page = getattr(self, "_page", None)
        if previous_page is not None and previous_page is not page:
            if self in previous_page.objects:
                previous_page.remove_object(self)
        if page is not None:
            page.add_object(self)
        self._page = page

        if not hasattr(self, "_data_row_objects"):
            return
        rows = list(self._data_row_objects)
        if self._header_row is not None:
            rows.insert(0, self._header_row)
        for row in rows:
            components = [row, *row.children]
            for component in components:
                component_page = component.page
                if component_page is not None and component_page is not page:
                    if component in component_page.objects:
                        component_page.remove_object(component)
                component.page = page

    @page.deleter
    def page(self) -> None:
        self.page = None

    @staticmethod
    def _validate_values(
        values: Optional[ListType[str]], name: str, *, optional: bool = False
    ) -> ListType[str]:
        if values is None and optional:
            return []
        if not isinstance(values, list):
            raise TypeError(f"{name} must be a list")
        if any(not isinstance(value, str) for value in values):
            raise TypeError(f"{name} values must be strings")
        return list(values)

    @classmethod
    def _validate_rows(
        cls, rows: Optional[ListType[ListType[str]]]
    ) -> ListType[ListType[str]]:
        if rows is None:
            return []
        if not isinstance(rows, list):
            raise TypeError("rows must be a list")
        return [cls._validate_values(row, "row") for row in rows]

    @staticmethod
    def _determine_column_count(
        headers: ListType[str],
        rows: ListType[ListType[str]],
        column_widths: Optional[ListType[Number]],
    ) -> int:
        if headers:
            column_count = len(headers)
        elif rows:
            column_count = len(rows[0])
        elif isinstance(column_widths, list):
            column_count = len(column_widths)
        else:
            column_count = 0
        if column_count == 0:
            raise ValueError(
                "table column count requires headers, a data row, or column_widths"
            )
        return column_count

    @staticmethod
    def _validate_dimension(value: Number, name: str) -> Number:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be a positive number")
        return value

    @staticmethod
    def _validate_color(value: Color, name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string or StandardColor")

    @staticmethod
    def _validate_text_format(value: Optional[TextFormat], name: str) -> None:
        if value is not None and not isinstance(value, TextFormat):
            raise TypeError(f"{name} must be a TextFormat")

    @staticmethod
    def _validate_index(value: int, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise IndexError(f"{name} is out of range")

    def _create_row(self, values: ListType[str], *, is_header: bool) -> Object:
        row = object_from_library(
            library="general",
            obj_name="table_row",
            page=self.page,
        )
        row.parent = self
        for value in values:
            cell = object_from_library(
                library="general",
                obj_name="table_cell",
                page=self.page,
                value=value,
                fillColor=(
                    self._header_background_color
                    if is_header
                    else self._background_color
                ),
                text_format=deepcopy(
                    self._header_text_format if is_header else self._cell_text_format
                ),
            )
            cell.parent = row
            cell.strokeColor = "inherit"
        return row

    def _layout(self) -> None:
        table_width = sum(self._column_widths)
        y_position: Number = 0
        rows: ListType[tuple[Object, Number]] = []
        if self._header_row is not None:
            rows.append((self._header_row, self._header_height))
        rows.extend((row, self._row_height) for row in self._data_row_objects)

        for row, height in rows:
            row.geometry.x = 0
            row.geometry.y = y_position
            row.geometry.width = table_width
            row.geometry.height = height
            x_position: Number = 0
            for cell, width in zip(row.children, self._column_widths):
                cell.geometry.x = x_position
                cell.geometry.y = 0
                cell.geometry.width = width
                cell.geometry.height = height
                x_position += width
            y_position += height

        self.geometry.width = table_width
        self.geometry.height = y_position
        self.update_parent()

    @property
    def headers(self) -> ListType[str]:
        """Return the header values, or an empty list when there is no header."""

        if self._header_row is None:
            return []
        return [cell.value for cell in self._header_row.children]

    @property
    def rows(self) -> ListType[ListType[str]]:
        """Return a copy of the data-row values."""

        return [[cell.value for cell in row.children] for row in self._data_row_objects]

    def add_row(self, values: ListType[str]) -> None:
        """Append a data row and resize the table."""

        normalized_values = self._validate_values(values, "row")
        if len(normalized_values) != self._column_count:
            raise ValueError("row must match the table's column count")
        self._data_row_objects.append(
            self._create_row(normalized_values, is_header=False)
        )
        self._layout()

    def remove_row(self, row_index: int) -> None:
        """Remove a zero-based data row and resize the table."""

        self._validate_index(row_index, "row_index")
        try:
            row = self._data_row_objects.pop(row_index)
        except IndexError:
            raise IndexError("row_index is out of range") from None

        for cell in list(row.children):
            row.remove_object(cell)
            if self.page is not None and cell in self.page.objects:
                self.page.remove_object(cell)
        self.remove_object(row)
        if self.page is not None and row in self.page.objects:
            self.page.remove_object(row)
        self._layout()

    def set_cell(self, row_index: int, column_index: int, value: str) -> None:
        """Set a data-cell value using zero-based row and column indices."""

        self._validate_index(row_index, "row_index")
        self._validate_index(column_index, "column_index")
        if not isinstance(value, str):
            raise TypeError("cell value must be a string")
        try:
            row = self._data_row_objects[row_index]
        except IndexError:
            raise IndexError("row_index is out of range") from None
        try:
            row.children[column_index].value = value
        except IndexError:
            raise IndexError("column_index is out of range") from None

    @property
    def column_widths(self) -> ListType[Number]:
        return list(self._column_widths)

    @column_widths.setter
    def column_widths(self, values: ListType[Number]) -> None:
        if not isinstance(values, list):
            raise TypeError("column_widths must be a list")
        if len(values) != self._column_count:
            raise ValueError("column_widths must match the table's column count")
        normalized = [
            self._validate_dimension(value, "column width") for value in values
        ]
        self._column_widths = normalized
        self._layout()

    @property
    def row_height(self) -> Number:
        return self._row_height

    @row_height.setter
    def row_height(self, value: Number) -> None:
        self._row_height = self._validate_dimension(value, "row_height")
        self._layout()

    @property
    def header_height(self) -> Number:
        return self._header_height

    @header_height.setter
    def header_height(self, value: Number) -> None:
        self._header_height = self._validate_dimension(value, "header_height")
        self._layout()

    @property
    def border_color(self) -> Color:
        return self._border_color

    @border_color.setter
    def border_color(self, value: Color) -> None:
        self._validate_color(value, "border_color")
        self._border_color = value
        self.strokeColor = value

    @property
    def background_color(self) -> Color:
        return self._background_color

    @background_color.setter
    def background_color(self, value: Color) -> None:
        self._validate_color(value, "background_color")
        self._background_color = value
        self.fillColor = value
        for row in self._data_row_objects:
            for cell in row.children:
                cell.fillColor = value

    @property
    def header_background_color(self) -> Color:
        return self._header_background_color

    @header_background_color.setter
    def header_background_color(self, value: Color) -> None:
        self._validate_color(value, "header_background_color")
        self._header_background_color = value
        if self._header_row is not None:
            for cell in self._header_row.children:
                cell.fillColor = value

    @property
    def header_text_format(self) -> TextFormat:
        return deepcopy(self._header_text_format)

    @header_text_format.setter
    def header_text_format(self, value: TextFormat) -> None:
        if not isinstance(value, TextFormat):
            raise TypeError("header_text_format must be a TextFormat")
        self._header_text_format = deepcopy(value)
        if self._header_row is not None:
            for cell in self._header_row.children:
                cell.text_format = deepcopy(value)

    @property
    def cell_text_format(self) -> TextFormat:
        return deepcopy(self._cell_text_format)

    @cell_text_format.setter
    def cell_text_format(self, value: TextFormat) -> None:
        if not isinstance(value, TextFormat):
            raise TypeError("cell_text_format must be a TextFormat")
        self._cell_text_format = deepcopy(value)
        for row in self._data_row_objects:
            for cell in row.children:
                cell.text_format = deepcopy(value)
