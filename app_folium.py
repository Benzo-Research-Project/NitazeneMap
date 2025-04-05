import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import pandas as pd
import folium
from folium import plugins
import math 

# Read in the data
df = pd.read_csv('data/wedinos_alerts_2024.csv', sep='\t', encoding='utf-8')
df['intent'] = df['intent'].apply(str.lower)
for idx, row in df.iterrows():
    if 'diazepam' in row['intent']:
        df.at[idx, row['intent']] = 'diazepam'
df['major'] = df['major'].apply(str.lower)
df2 = df.dropna(subset=['longitude', 'latitude']).reset_index(drop=True)
df.set_index(df.columns[0], inplace=True)
df2.set_index(df2.columns[0], inplace=True)

# Initialize the app - incorporate css
external_stylesheets = ['https://brp.org.uk/files/main_style.css']
app = Dash(external_stylesheets=external_stylesheets)

m = folium.Map(
        location=[53.989955, -3.151694],  # center of the map
        zoom_start=6,  # dezoom
        tiles='cartodb positron'  # background style
    )
fig = m._repr_html_()

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
                        multiple=True
                    ),
                    html.Div(id='output-data-upload')
                ]),
                html.Div(style={'padding': 10, 'flex': 1}, children=[
                    html.P(children='Select a drug of intent from the dropdown to filter the map.', style={'textAlign':'left','margin':'0px'}),
                    dcc.Dropdown(df2.intent.unique(), '', id='dropdown-selection', style={'borderRadius': '10px'})
                ]),
            ]),
            html.Div(style={'borderRadius':'10px'}, children=[
                html.Iframe(srcDoc=fig, width='100%', height='750', style={'borderRadius': '10px','border':'none','overflow': 'hidden','display': 'inline-block'}, id='graph-content')
            ]),
        ]),html.Br(),
        html.Div(style={'overflowX': 'scroll','padding': 10}, children=[
            dash_table.DataTable(data=df.to_dict('records'), page_size=10)
        ]),html.Br(),html.Br(),
        html.P(children='Last updated: 15 December 2024. Locations are placed randomly within the postcode district of each result (e.g. EC1). Data is displayed for informational purposes only, and is owned by WEDINOS. Data does not include results after 4 December 2024 due to WEDINOS experiencing technical issues.', style={'textAlign':'left', 'font-size': '0.8em'})
    ])
])]

@callback(
    Output(component_id='graph-content', component_property='srcDoc'),
    Input(component_id='dropdown-selection', component_property='value')
)

def update_graph(col_chosen):
    filtered_df = df2[df2.intent.str.contains(col_chosen)]
    m = folium.Map(
        location=[53.989955, -3.151694],  # center of the map
        zoom_start=6,  # dezoom
        tiles='cartodb positron'  # background style
    )
    marker_cluster = plugins.MarkerCluster(name="nitazenes").add_to(m)
    benzo_cluster = plugins.MarkerCluster(name="counterfeit_benzos").add_to(m)
    # Add all the individual points to the map
    for idx, row in filtered_df.iterrows():
        if type(row['minor']) == float:
            #popup = f"{row['postcode']} – Sold as {row['intent']}, tested as {row['major']}"
            popup = f"""
                <h1>{idx}</h1>
                <p>
                Postcode: <b>{row['postcode']}</b><br/>
                Date: <b>{row['date_received']}</b><br/>
                Sold as: <b>{row['intent']}</b><br/>
                Tested as: <b>{row['major']}</b><br/>
                </p>
                """

        else:
            #popup = f"{row['postcode']} – Sold as {row['intent']}, tested as {row['major']} with {row['minor']}"
            popup = f"""
                <h1>{idx}</h1>
                <p>
                Postcode: <b>{row['postcode']}</b><br/>
                Date: <b>{row['date_received']}</b><br/>
                Sold as: <b>{row['intent']}</b><br/>
                Tested as: <b>{row['major']}</b> with <b>{row['minor']}</b><br/>
                </p>
                """
        
        color = '#1e3d77' if ('diazepam' in str.lower(row['intent'])) or ('temazepam' in str.lower(row['intent'])) or ('bromazolam' in str.lower(row['intent'])) or ('etizolam' in str.lower(row['intent'])) or ('valium' in str.lower(row['intent'])) or ('alprazolam' in str.lower(row['intent'])) or ('xanax' in str.lower(row['intent'])) or ('bensedin' in str.lower(row['intent'])) or ('msj' in str.lower(row['intent'])) or ('benzodine' in str.lower(row['intent'])) else '#ffde5b'
        try:
            if ('diazepam' in str.lower(row['intent'])) or ('temazepam' in str.lower(row['intent'])) or ('bromazolam' in str.lower(row['intent'])) or ('etizolam' in str.lower(row['intent'])) or ('valium' in str.lower(row['intent'])) or ('alprazolam' in str.lower(row['intent'])) or ('xanax' in str.lower(row['intent'])) or ('bensedin' in str.lower(row['intent'])) or ('msj' in str.lower(row['intent'])) or ('benzodine' in str.lower(row['intent'])):
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=15,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.5,
                    weight=1,
                    popup=popup
                ).add_to(benzo_cluster)
            else:
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=15,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.5,
                    weight=1,
                    popup=popup
                ).add_to(marker_cluster)
        except:
            pass
    fig = m._repr_html_()
        
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
