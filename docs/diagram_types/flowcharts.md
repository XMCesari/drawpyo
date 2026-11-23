# Flowcharts

`FlowChart` provides typed nodes, semantic links, and automatic layout for process
flows. It supports branches, merges, loops, and disconnected sections.

## Create a flowchart

Create the chart first, then pass it to each node. Nodes register themselves with
the chart automatically.

```python
from drawpyo.diagram_types import Decision, End, FlowChart, Process, Start

chart = FlowChart(
    file_path="output",
    file_name="Approval.drawio",
    direction="down",
)

start = Start(flowchart=chart, value="Start")
approved = Decision(flowchart=chart, value="Approved?")
revise = Process(flowchart=chart, value="Revise request")
end = End(flowchart=chart, value="Complete")

start.connect(approved)
approved.yes(end)
approved.no(revise)
revise.connect(approved)

chart.auto_layout()
chart.write()
```

`auto_layout()` places every node, routes links around node bounds, and expands
the page when necessary. Calling it again is safe and produces the same layout
for the same node insertion order.

## Node and link behavior

| Node | Shape | Outgoing links |
| --- | --- | --- |
| `Start` | Flowchart start | One via `connect()` |
| `Process` | Rounded process | One via `connect()` |
| `Decision` | Decision diamond | One each via `yes()` and `no()`, plus labeled branches via `connect()` |
| `End` | Terminator | None |

All link methods return the generated `Edge`, so its formatting can be adjusted
after creation. Repeating the same connection returns the existing edge. Links
between different `FlowChart` instances are rejected.

Decision convenience methods use `Yes` and `No` edge labels:

```python
yes_edge = approved.yes(end)
no_edge = approved.no(revise)
fallback = approved.connect(end, label="Escalate")
```

## Layout options

| Parameter | Effect | Default |
| --- | --- | --- |
| `direction` | Primary flow direction: `down` or `right` | `down` |
| `link_style` | `orthogonal`, `straight`, or `curved` | `orthogonal` |
| `layer_spacing` | Space between graph layers | `80` |
| `node_spacing` | Space between nodes in one layer | `40` |
| `component_spacing` | Space between disconnected sections | `100` |
| `padding` | Space around page content | `40` |

Layout is best-effort: incomplete charts, multiple starts or ends, disconnected
nodes, merges, and loops are all accepted. Running layout replaces any manual
node positions.

## Customize nodes

Node constructors accept the same formatting keyword arguments as `Object`.
Explicit arguments override the built-in flowchart shape defaults.

```python
review = Process(
    flowchart=chart,
    value="Manual review",
    width=160,
    fillColor="#dae8fc",
)
```
