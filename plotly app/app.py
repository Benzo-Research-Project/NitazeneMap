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
df2.set_index(df.columns[0], inplace=True)

# Initialize the app - incorporate css
external_stylesheets = ['https://brp.org.uk/files/main_style.css']
app = Dash(external_stylesheets=external_stylesheets)
fig = go.Figure()

# Requires Dash 2.17.0 or later
app.layout = [html.Div(className='wsite-section-wrap', style={"width":"100%"}, children=[
    html.Div(className='container', children=[
        html.Div(style={'width':'100%','display': 'inline-block'}, children=[
            html.H1(children='Nitazene Map: Jan–Dec 2024 (WEDINOS)', style={'textAlign':'center'}),
            html.Div(style={'display': 'flex', 'flexDirection': 'row'},children=[
                html.Div(style={'padding': 10, 'flex': 1}, children=[
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        # Allow multiple files to be uploaded
                        multiple=False
                    ),
                    html.Div(id='output-data-upload')
                ]),
                html.Div(style={'padding': 10, 'flex': 1}, children=[
                    html.P(children='Select a drug of intent from the dropdown to filter the map.', style={'textAlign':'left','margin':'0px'}),
                    dcc.Dropdown(df2.intent.unique(), '', id='dropdown-selection', style={'borderRadius': '10px'})
                ]),
            ]),
            html.Div(
                #style={'width':'100%','border': '3px solid #eee','borderRadius':'10px','transform':'translateZ(0px)','overflow':'hidden','display':'inline-block'}, 
                children=[
                dcc.Graph(figure={}, style={'width': '100%'}, id='graph-content'),
            ]),
        html.Div(style={'overflowX': 'scroll','padding': 10}, children=[
            dash_table.DataTable(data=df2.to_dict('records'), page_size=10)
        ]),html.Br(),html.Br(),
        html.P(children='Dataset last updated: 15 December 2024. Locations are placed randomly within the postcode district of each result (e.g. EC1). Data is displayed for informational purposes only, and is owned by WEDINOS. Data does not include results after 4 December 2024 due to WEDINOS experiencing technical issues.', style={'textAlign':'left', 'font-size': '0.8em'})
    ])
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
                marker=dict(size=7, opacity=0.8)
            ))
    fig.update_layout(margin={"t": 20, "b": 20, "l": 20, "r": 20})
    fig.update_geos(resolution=50, 
                    fitbounds="locations",
                    projection_type="mercator")
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
