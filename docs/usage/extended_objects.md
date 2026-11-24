# Extended Objects
While any of the objects in Draw.io can be created by setting the correct combination of attributes it's not always convenient, particularly when an 'object' is actually a small group of objects. To offer a little more convenience drawpyo has extended objects. These inherit from the Object class but extend it with added functionality, though not quite to the level of the custom diagram types.

Extended objects can mirror Draw.io functionality or provide new object types while retaining the normal `Object` styling and positioning APIs.

## List

A list object is available in the General library in Draw.io. It's simple a small container object with a horizontal label filled with text objects as the list items. The Draw.io app conveniently keeps the list items positioned and in order as you add or remove, also scaling the size of the list container.

![list](../img/object_styles/list.png)

### Creating a List

To create a list in drawpyo, use the `diagram.List` object.

```python
new_list = drawpyo.diagram.List(title="List", page=page, width=200)
```

Like any other Object, the position and geometry can be set during creation as well as various styling attributes.

### Adding Items

There are a few methods of adding items. The easiest would be using the `.add_item()` method.

```python
new_list.add_item("item 1")
new_list.add_item("item B")
new_list.add_item("item iii")
```

This will create a text object, set the List as its parent, position it correctly, and then resize the List object.

You can also access the property `list_items`. It will return a list of strings denoting all the items in the list. But it also has a setter property, so setting it to a list of strings will remove existing items and then go through the creation and resizing process.

### Deleting Items

The easiest way to delete an item is to call the `.remove_item()` method. Pass in the text of the item to remove and it will be strucken from the list then the list resized.

```python
new_list.remove_item("item B")
```

### Resizing the List

The list will be automatically resized to match the contents when the above methods are called. But the resize can also be called manually with the `.autosize()` method.

## Table

`diagram.Table` creates a native Draw.io table whose rows and cells remain individually editable in Draw.io. Tables can include an optional header row and require their column count to be established by headers, an initial data row, or explicit column widths.

### Creating a Table

```python
table = drawpyo.diagram.Table(
    page=page,
    position=(100, 100),
    headers=["Name", "Owner", "Status"],
    rows=[
        ["API", "Backend", "Active"],
        ["Database", "Platform", "Planned"],
    ],
    column_widths=[160, 120, 100],
    row_height=30,
    header_height=35,
)
```

When `column_widths` is omitted, each column is 120 pixels wide. The table width is the sum of its column widths, and its height is recalculated from the header and data rows.

Tables without headers infer their column count from the first data row:

```python
table = drawpyo.diagram.Table(
    page=page,
    rows=[["API", "Backend", "Active"]],
)
```

### Updating Rows and Cells

Data-row and column indices are zero based. Header rows are not included in data-row indices.

```python
table.add_row(["Cache", "Backend", "Active"])
table.set_cell(0, 2, "Completed")
table.remove_row(1)
```

These operations update the live Draw.io objects already associated with the page. Adding or removing a row also resizes and repositions the table.

The current values can be read through `table.headers` and `table.rows`. Both properties return lists of strings.

### Styling and Resizing

Basic table formatting can be supplied during construction or changed later:

```python
table.border_color = "#666666"
table.background_color = "#FFFFFF"
table.header_background_color = "#E6E6E6"
table.column_widths = [180, 140, 100]
table.row_height = 36
table.header_height = 40

table.header_text_format = drawpyo.diagram.TextFormat(
    bold=True,
    align="center",
    verticalAlign="middle",
)
table.cell_text_format = drawpyo.diagram.TextFormat(
    align="left",
    verticalAlign="middle",
)
```

Assigning a style or size property updates all existing applicable cells, and rows added later inherit the current settings.

Tables are rectangular in this initial implementation. Merged cells, row or column spans, column insertion and removal, and automatic sizing based on text content are not supported.
