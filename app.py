import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import pandas as pd

df = pd.read_csv('data/wedinos_alerts_2024.csv', sep='\t', encoding='utf-8')
df['intent'] = df['intent'].apply(str.lower)
for idx, row in df.iterrows():
    if 'diazepam' in row['intent']:
        df.at[idx, row['intent']] = 'diazepam'
df['major'] = df['major'].apply(str.lower)
df2 = df.dropna(subset=['longitude', 'latitude']).reset_index(drop=True)

# Initialize the app - incorporate css
external_stylesheets = ['https://brp.org.uk/files/main_style.css']
app = Dash(external_stylesheets=external_stylesheets)
fig = go.Figure()

# Requires Dash 2.17.0 or later
app.layout = [html.Div(className='container', children=[
    html.Div([
        html.H1(children='Nitazene Map: Jan–Dec 2024 (WEDINOS)', style={'textAlign':'center'}),
        html.P(children='Select a drug of intent from the dropdown to filter the map.', style={'textAlign':'left'}),
        dcc.Dropdown(df2.intent.unique(), '', id='dropdown-selection'),
        dcc.Graph(figure={}, id='graph-content'),
        dash_table.DataTable(data=df.to_dict('records'), page_size=10)
    ])
])]

@callback(
    Output(component_id='graph-content', component_property='figure'),
    Input(component_id='dropdown-selection', component_property='value')
)

def update_graph(col_chosen):
    filtered_df = df2[df2.intent.str.contains(col_chosen)]
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
                lon=filtered_df['longitude'],
                lat=filtered_df['latitude'],
                text=filtered_df['major']+' (intent: '+filtered_df['intent']+')', 
                hoverinfo='text',
                mode='markers',
                marker=dict(size=5, opacity=0.8)
            ))

    fig.update_geos(resolution=50, fitbounds="locations")
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
