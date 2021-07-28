import micropip
await micropip.install("pyodide-html")

import uuid

import js
import pandas as pd
import plotly.express as px
import pyodide
from pyodide import to_js
import pyodide_html as html


def radio_group(*options, **attributes):
    # ensure that we will always have a name for the radio inputs, create one if there's none
    attributes['name'] = attributes.get('name', uuid.uuid4().hex)

    radio = html.div()

    # Create a custom "change" event for our radio div
    radio_change_event = js.CustomEvent.new('change')

    def on_click(event):
        radio.__internal_value = event.target.value

    for child in options:
        # We assume child is a string here:
        radio.add(
            html.input(
                type="radio", value=child, onclick=on_click, name=attributes['name']
            ),
            html.label(child, for_=child),
        )

        # Todo: Accept `child = dict(label=..., value=..., checked=...)`

    def on_change(value):
        """
        Mark the radio item(s) to be checked if the value of the radio group changes.
        """

        radio.querySelector(f'input[value="{value}"]').checked = True
        radio.__internal_value = value
        radio.dispatchEvent(radio_change_event)

    # Override the getter/setter for our radio 
    js.Object.defineProperty(
        radio,
        "value",
        js.Object.fromEntries(
            to_js({"get": lambda: radio.__internal_value, "set": on_change,})
        ),
    )

    # add attributes at the end to trigger changes
    radio.add(**attributes)

    return radio


def dropdown(options, value=None, **attributes):
    return html.select(
        *[
            html.option(
                opt, 
                value=opt, 
                selected=opt == value
            ) 
            for opt in options
        ],
        **attributes
    )


# load dataset
df = pd.read_csv(pyodide.open_url('https://plotly.github.io/datasets/country_indicators.csv'))
available_indicators = df['Indicator Name'].unique()
unique_yrs = df['Year'].unique()

# we can give a title to our app
js.document.head.appendChild(html.title("Pyodide App with Plotly"))

# Let's create the actual layout of the app
container = html.div(
    html.div(
        xaxis_col := dropdown(
            available_indicators, value="Fertility rate, total (births per woman)"
        ),
        xaxis_type := radio_group("Linear", "Log", id="xaxis-type", value="Linear"),
        style="width: 48%; display: inline-block",
    ),
    html.div(
        yaxis_col := dropdown(
            available_indicators, value='Life expectancy at birth, total (years)'
        ),
        yaxis_type := radio_group("Linear", "Log", value="Linear"),
        style="width: 48%; display: inline-block; float: right"
    ),
    plot_div := html.div(),
    year_slider := html.input(
        type="range", min=0, max=len(unique_yrs)-1, value=len(unique_yrs)-1, step=1,
    )
)

def update_figure(event=None):
    dff = df[df['Year'] == unique_yrs[int(year_slider.value)]]

    x = dff[dff['Indicator Name'] == xaxis_col.value]['Value']
    y = dff[dff['Indicator Name'] == yaxis_col.value]['Value']
    hover = dff[dff['Indicator Name'] == yaxis_col.value]['Country Name']

    fig = px.scatter(x=x, y=y, hover_name=hover)

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    fig.update_xaxes(title=xaxis_col.value,
                     type='linear' if xaxis_type.value == 'Linear' else 'log')

    fig.update_yaxes(title=yaxis_col.value,
                     type='linear' if yaxis_type.value == 'Linear' else 'log')


    parsed = js.JSON.parse(fig.to_json())
    js.Plotly.newPlot(plot_div, parsed.data, parsed.layout)


# Add an event listener for all the inputs listening to change
for ele in [xaxis_type, xaxis_col, yaxis_type, yaxis_col, year_slider]:
    ele.addEventListener("change", update_figure)


# We can finally add our container to the js div
js.document.body.appendChild(container)

# initial update
update_figure()