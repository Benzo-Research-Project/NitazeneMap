# last update: 27/07/2026 – AJ
from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import pandas as pd
import folium
from branca.element import Element, MacroElement, Template
from datetime import datetime, date
from utils.map import getCategories, concernMap, dateFilter
from utils.counterfeits import checkStatus, getContents, getUniqueContents
import pgeocode
nomi = pgeocode.Nominatim('gb')
import yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Read in the data

strDaterange = config['dateRange']
fileDirectory = {
    'Benzos': 'wedinos_benzos_intent.csv', #f'wedinos_benzos_intent_{strDaterange}.csv'
    'Opioids': 'wedinos_opioids_intent.csv',
    'Vapes': 'wedinos_vapes_intent.csv',
    'Cocaine': 'wedinos_cocaines_intent.csv'
}
defaultCategory = list(fileDirectory.keys())[0]

#fileurl = f"{config['dataPath']}/wedinos_benzos_intent_{strDaterange}.csv"
fileurl = f"{config['gitDataRepo']}/{fileDirectory[defaultCategory]}"
try:
    df = pd.read_csv(fileurl, sep=',', encoding='utf-8', index_col=0) # default to benzos
except:
    print('***Could not get data from Github, using backup...')
    df = pd.read_csv(f"{config['dataPath']}/{fileDirectory[defaultCategory].replace('.csv','')}_{strDaterange}.csv", sep=',', encoding='utf-8', index_col=0) # default to benzos
dates = df['date_received'].copy()
minDate = date(2024, 1, 1)
maxDate = pd.to_datetime(dates).max().date()
#strDaterange = fileDirectory[defaultCategory].split('_')[-1].split('.')[0]
defaultIntent = defaultCategory if defaultCategory[-1]!='s' else defaultCategory[:-1]
dfStatus, statusDict = checkStatus(df, str.lower(defaultIntent), dates=strDaterange)
dfContents = getContents(dfStatus, str.lower(defaultIntent), dates=strDaterange, counterfeits=True, save=False)
dfUniqueContents = getUniqueContents(dfContents, str.lower(defaultIntent), dates=strDaterange, counterfeits=True, save=False)

keepColumns = ['date_received','postcode','intent','label','colour','form','consumption_method','effects','major','minor']

with open('changelog.md','r') as f:
    lines = f.readlines()
    changelog = ''.join(lines)

# Initialize the app - incorporate css
external_stylesheets = ['https://brp.org.uk/files/main_style.css', f"{config['assetsPath']}/dash_stylesheet.css"]
external_scripts=[f"{config['assetsPath']}/share.js"]

app = Dash(__name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"property": "og:title", "content": "DrugMapUK | National Supply Monitoring Dashboard"},
        {"name": "title", "content": "DrugMapUK | National Supply Monitoring Dashboard"},
        {"property": "og:description", "content": "A dashboard for visualising national drug checking data to identify areas or substances carrying increased risk of drug-related harms. Powered by the Benzo Research Project, Release and WEDINOS."},
        {"name": "description", "content": "A dashboard for visualising national drug checking data to identify areas or substances carrying increased risk of drug-related harms. Powered by the Benzo Research Project, Release and WEDINOS."},
        {"charset": "UTF-8"},
        {"name": "theme-color", "content": "#eee"}
    ],
    external_stylesheets=external_stylesheets,
    assets_folder=config['assetsPath'],
    external_scripts=external_scripts
)
app.title = "DrugMapUK | National Supply Monitoring Dashboard"

m = folium.Map(
        location=[53.989955, -3.151694],  # center of the map
        zoom_start=6,  # dezoom
        tiles='cartodb positron'  # background style
    )
m.get_root().header.add_child(Element("""
    <style>
        html, body { margin: 0 !important; padding: 0; width: 100%; height: 100%; overflow: hidden; }
        .folium-map-container { width: 100% !important; height: 100% !important; padding-bottom: 0 !important; }
    </style>
    """))
fig = m.get_root().render()
pie = px.pie(names=['As sold', 'Mis-sold'], values=[statusDict['As sold'],statusDict['Mis-sold']])
pie.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
bar = px.bar(dfUniqueContents.head(20), y='Count', labels={"Count": "Counterfeit samples", "Compound": "Compound"}, title='Most common counterfeits:')
bar.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })

# Requires Dash 2.17.0 or later
app.layout = [html.Div(className='wsite-section-wrap', children=[
    html.Div(className='wsite-section wsite-body-section', children=[html.Div(className='wsite-section-content', children=[
        html.Div(style={'display':'block','height':'20px','width':'100%'}),
        html.Div(id='nav', children=[
                            html.Div(className='container', children=[
                                html.A('\u00D7', className='closeBtn', href='#'),
                                html.A('Get your drugs tested', href='https://wedinos.wales/sample-testing/', target='_blank', title='WEDINOS Sample Testing', className='bitcount-single-400 nav-items'),
                                html.A('Know your drugs', href='https://www.release.org.uk/drugs-law/drugs-a-to-z', target='_blank', title='Drugs A-Z', className='bitcount-single-400 nav-items'),
                                html.A('Find support', href='https://brp.org.uk/help', target='_blank', title='Find the right support', className='bitcount-single-400 nav-items'),
                            ]),
                            html.Div(className='sticky-bottom container', children=[
                                html.P(children=['DrugMap',html.Sup('UK'),' is powered by the ',html.Wbr(),html.A(href='https://brp.org.uk', target='_blank', children='Benzo Research Project', style={'whiteSpace': 'nowrap'}), ' & ', html.A(href='https://www.release.org.uk', target='_blank', children='Release'),'.',
                                                                            html.Br(),'All data owned by ',html.A(href='https://wedinos.wales', target='_blank', children='WEDINOS'),'.'])
                            ])
        ]),
        html.Div(className='main-wrap container', style={'borderRadius': '20px'}, children=[
                html.Div(className='wsite-section-elements dm-header', children=[
                    html.A(children=[html.Img(src='assets/drugmaplogo.png',
                            alt='A black map pin with a scored white pill in the centre.',
                            id='dm-logo',
                            disable_n_clicks=True)], href='#nav'),
                    html.H1(children=['DrugMap',html.Sup(children='UK')], className='bitcount-single-400'),
                    html.P(className='dm-subtitle bitcount-single-400', children=[html.Span(children=['National Supply Monitoring Dashboard', 
                                                                                  html.Span(':',className='dm-subtitle-separator'), 'Powered by the ',html.A(href='https://brp.org.uk', target='_blank', children='Benzo Research Project'), ' & ', html.A(href='https://www.release.org.uk', target='_blank', children='Release'), 
                                                                                  html.Span(':',className='dm-subtitle-separator'), 'Data source: ', html.A(href='https://wedinos.wales', target='_blank', children='WEDINOS'),
                                                                                  html.Span(':',className='dm-subtitle-separator'), f'Version {config['versionNo']}'
                                                                                  ])]),
                    
                    html.Button(id="shareButton",className="shareButton",style={"backgroundImage": "url('assets/shareicon.png')"}, children=[html.Span(style={"display": "none"},children=['share'])]),
                    html.P(id="shareResult",style={"display":"none"}, children=[])
                ]),
                html.Div(className='wsite-section-elements dm-selection', children=[
                    html.Div(className='dm-selection-flexwrap',children=[
                        html.Div(className='dm-selection-dates', children=[
                            html.P(children='Dates:', style={'textAlign':'left','margin':'0px'}),
                            html.Div(className='datepickerwrapper',children=[
                                dcc.DatePickerRange(
                                    id='date-picker-range',
                                    min_date_allowed=minDate,
                                    max_date_allowed=maxDate,
                                    initial_visible_month=maxDate,
                                    #start_date=minDate, # filtering gets really clunky with this set
                                    end_date=maxDate,
                                    display_format='DD MMM YYYY',
                                    updatemode='bothdates',
                                    style={'borderRadius': '10px'}
                                )]),
                            #html.Style(".DateInput_input {fontSize: 16px; line-height: 1em; font-family: 'League Spartan', sans-serif; font-weight:500}"),
                            html.Div(id='output-container-date-picker-range', style={'borderRadius': '10px'}),
                        ]),
                        html.Div(style={'padding': 10, 'flex': 1, 'minWidth': '200px'}, children=[
                            html.P(children='Sample intent:', style={'textAlign':'left','margin':'0px'}),
                            dcc.Dropdown(list(fileDirectory.keys()), defaultCategory, id='dropdown-selection', style={'borderRadius': '10px'})
                        ]),
                        html.Div(style={'padding': 10, 'flexShrink': 0, 'minWidth': '75px'}, children=[
                            dcc.Checklist(options=[{'label': ' Show All', 'value': 'checked'}],
                                        value=[],
                                        id='checklist-selection',
                                        inline=True,
                                        style={'fontFamily':'Montserrat'})
                        ]),
                    ]),
                    dcc.Tabs([
                        dcc.Tab(label='Map', className='custom-tab', selected_className='custom-tab--selected', children=[
                            html.Div(id='mapwrapper',style={'height':'500px','width':'100%','boxSizing':'border-box','borderRadius':'10px','transform':'translateZ(0px)','overflow':'hidden'}, children=[
                                html.Iframe(srcDoc=fig, width='100%', height='100%', id='graph-content', allow='fullscreen', style={'width':'100%','height':'100%','overflow': 'hidden','display': 'block','margin': '0','border':'0','padding':'0'}) #'aspectRatio': '16.385 / 10',
                            ]),
                        ]),
                        dcc.Tab(label='Graphs', className='custom-tab', selected_className='custom-tab--selected', children=[
                            html.Div(className='dm-flex-wrap', children=[
                                html.Div(className='ppl-flex-wrap', children=[
                                    html.Div(className='dm-flex-child dm-bar', children=[
                                        dcc.Graph(id='counterfeits-graph', figure=bar)
                                    ]),
                                    html.Div(className='dm-flex-child dm-pie', children=[
                                        dcc.Graph(id='counterfeits-pie', figure=pie)
                                    ])
                                ]),
                                html.P(className="notice", children=['Note: The bar graph does not yet correct for alternative spellings, leading to potential under/overcounting of certain compounds (e.g. phenacetin/phenacetine). As-sold is defined as whether a sample contains only the sample intent; mis-sold is defined as any sample either not containing the sample intent, or containing the sample intent plus other impurities, contaminants, or adulterants.'])       
                            ]),
                        ]),
                        dcc.Tab(label='Table', className='custom-tab', selected_className='custom-tab--selected', children=[
                            html.Div(className='dm-flex-wrap', children=[
                                html.Div(className='dm-table-scroll', children=[
                                    dash_table.DataTable(id='records-table', 
                                                        data=df[df.columns.intersection(keepColumns)].to_dict('records'), 
                                                        page_size=13,
                                                        sort_action='native'),
                                    html.Br(),html.Br(),
                                    html.Button("⤓ Excel file", id="btn_xlsx", className='bitcount-single-400'),
                                    dcc.Download(id="download-dataframe-xlsx")
                                ])
                            ])
                        ])
                    ]),
                ]),
            ])
        ]),
    html.Div(className='wsite-footer', children=[
        html.Div(className='container', children=[
            html.Div(className='wsite-section-elements', style={'padding': '20px'}, children=[
                html.P(children=["© Copyright 2026 DrugMap", html.Sup("UK")," – ",html.Wbr(),html.A(href="https://brp.org.uk",target="_blank",children=["Benzo Research Project"], style={'whiteSpace': 'nowrap'})," & ",html.A(href="https://www.release.org.uk",target="_blank",children=["Release"]),
                                 html.Br(),
                                 html.P(style={'fontSize':'10px'}, children=["All raw data used by DrugMap", html.Sup("UK")," is owned by WEDINOS, for informational purposes only, and does not claim to be a representative sample of the UK's drug supply. Locations are placed randomly within the postcode district of each result (e.g. EC1).",
                                 html.Br(),html.Br(),f'Version {config['versionNo']}',html.Br(),f'Dataset last updated: {maxDate.strftime("%d %b %Y")}.'])
                ]),
                html.Div(className='changelog', children=[
                    #html.H3('Changelog', className='changelog-title bitcount-single-400'),
                    dcc.Checklist(options=[{'label': ' Changelog', 'value': 'show'}],
                                  value=[],
                                  id='changelog-toggle',
                                  inline=True,
                                  inputClassName='changelog-input',
                                  labelClassName='changelog-label bitcount-single-400'),
                    html.Div(id="changelog-body",children=[html.P(children=[dcc.Markdown(changelog)])])
                ])
            ])
        ])
    ])
])])]

@callback(
    Output(component_id='graph-content', component_property='srcDoc'),
    Output(component_id='records-table', component_property='data'),
    Output(component_id='counterfeits-graph', component_property='figure'),
    Output(component_id='counterfeits-pie', component_property='figure'),
    Input(component_id='dropdown-selection', component_property='value'),
    Input(component_id='date-picker-range', component_property='start_date'),
    Input(component_id='date-picker-range', component_property='end_date'),
    Input(component_id='checklist-selection', component_property='value')
)
def update_dash(col_chosen, start_date, end_date, checklist_value):
    categories = getCategories(col_chosen)
    #fileurl = f'data/{fileDirectory[col_chosen]}'
    fileurl = f"{config['gitDataRepo']}/{fileDirectory[col_chosen]}"
    try:
        df = pd.read_csv(fileurl, sep=',', encoding='utf-8', index_col=0)
    except:
        print('***Could not get data from Github, using backup...')
        df = pd.read_csv(f"{config['dataPath']}/{fileDirectory[col_chosen].replace('.csv','')}_{strDaterange}.csv", sep=',', encoding='utf-8', index_col=0) # default to benzos

    intent = col_chosen if col_chosen[-1]!='s' else col_chosen[:-1]
    if start_date:
        df = dateFilter(df, start_date, end_date) # filtering dates
    # making map
    include_all = 'checked' in checklist_value
    m = concernMap(df, categories, include_all=include_all, save=False)
    fig = m.get_root().render() # m._repr_html_()

    # making counterfeit charts
    dfStatus, statusDict = checkStatus(df, str.lower(intent))
    dfContents = getContents(dfStatus, str.lower(intent), counterfeits=True, save=False)
    dfUniqueContents = getUniqueContents(dfContents, str.lower(intent), counterfeits=True, save=False)
    pie = px.pie(names=['As sold', 'Mis-sold'], values=[statusDict['As sold'],statusDict['Mis-sold']])
    pie.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    bar = px.bar(dfUniqueContents.head(20), y='Count', title='Most common counterfeits:', labels={"Count": "Counterfeit samples", "Compound": "Compound"})
    bar.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig, df[df.columns.intersection(keepColumns)].to_dict('records'), bar, pie
    #df.drop(columns=['sold_as', 'status', 'class-mismatch', 'latitude', 'longitude'])
@callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    daterange = [df['date_received'].min(),df['date_received'].max()]
    datelist = []
    for i in daterange:
        datelist.append(datetime.strftime(datetime.strptime(i,'%Y-%m-%d'),'%d%m%y'))
    filename=str.lower(f'wedinos_{datelist[0]}_{datelist[1]}.xlsx')
    return dcc.send_data_frame(df[df.columns.intersection(keepColumns)].to_excel, filename, sheet_name="Results")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
