import os

import drawpyo
from drawpyo.diagram import TextFormat
from drawpyo.utils.standard_colors import StandardColor


output_directory = os.environ.get(
    "DRAWPYO_OUTPUT_DIR",
    os.path.join(os.path.expanduser("~"), "Test Drawpyo Charts"),
)
os.makedirs(output_directory, exist_ok=True)

file = drawpyo.File(
    file_path=output_directory,
    file_name="Test Generated Tables.drawio",
)
page = drawpyo.Page(file=file, name="Extended Object Tables")

header_format = TextFormat(
    bold=True,
    align="center",
    verticalAlign="middle",
    fontColor=StandardColor.WHITE,
)
cell_format = TextFormat(
    align="left",
    verticalAlign="middle",
    spacingLeft=8,
)

status_table = drawpyo.diagram.Table(
    page=page,
    position=(80, 80),
    headers=["Name", "Owner", "Status"],
    rows=[
        ["API", "Backend", "Active"],
        ["Database", "Platform", "Planned"],
    ],
    column_widths=[180, 140, 120],
    row_height=36,
    header_height=42,
    border_color=StandardColor.GRAY6,
    background_color=StandardColor.WHITE,
    header_background_color=StandardColor.BLUE6,
    header_text_format=header_format,
    cell_text_format=cell_format,
)

# Showcase the mutation API. Changes are reflected in the objects already on
# the page and in the final exported diagram.
status_table.add_row(["Cache", "Backend", "Active"])
status_table.set_cell(0, 2, "Completed")
status_table.remove_row(1)

# Headers are optional. This table infers its two columns from the first row.
drawpyo.diagram.Table(
    page=page,
    position=(80, 260),
    rows=[
        ["Development", "dev"],
        ["Production", "main"],
    ],
    column_widths=[180, 160],
    row_height=34,
    border_color=StandardColor.GRAY4,
    background_color=StandardColor.GRAY1,
    cell_text_format=cell_format,
)

output_path = file.write()
print(f"Wrote table showcase to {output_path}")
