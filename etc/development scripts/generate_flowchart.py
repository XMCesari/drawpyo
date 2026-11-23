from pathlib import Path

from drawpyo.diagram_types import Decision, End, FlowChart, Process, Start


output_path = Path(__file__).resolve().parents[1] / "reference drawio charts"

chart = FlowChart(
    file_path=output_path,
    file_name="Coffee Order Flowchart.drawio",
    direction="down",
    link_style="orthogonal",
)

order_received = Start(flowchart=chart, value="Order received")
review_order = Process(flowchart=chart, value="Review order")
ingredients_available = Decision(
    flowchart=chart,
    value="Ingredients available?",
)
prepare_drink = Process(flowchart=chart, value="Prepare drink")
suggest_substitute = Process(flowchart=chart, value="Suggest substitute")
serve_order = End(flowchart=chart, value="Serve order")

order_received.connect(review_order)
review_order.connect(ingredients_available)
ingredients_available.yes(prepare_drink)
ingredients_available.no(suggest_substitute)
prepare_drink.connect(serve_order)
suggest_substitute.connect(ingredients_available)

chart.auto_layout()
written_path = chart.write()

print(f"Flowchart written to {written_path}")
