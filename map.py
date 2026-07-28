import time
import pandas as pd
import folium
from folium import plugins
import pgeocode
nomi = pgeocode.Nominatim('gb')
import numpy as np
from matplotlib.pyplot import subplots
import yaml
import json
import re
from argparse import ArgumentParser
from matplotlib import colormaps as cm
import matplotlib.colors as colors
from datetime import datetime as dt

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

save_data = config['saveData']
data_path = config['dataPath']
plots_path = config['plotsPath']

with open(config['substringsPath'], 'r', encoding='utf-8') as f:
    substrings_dict = json.load(f)
substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' not in str(k)}
not_substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' in str(k)} # To rule out any overlapping substrings (e.g. benzo – benzocaine)

#opioid_substring_list = config['opioid_substring_list']
#benzo_substring_list = config['benzo_substring_list']
#cocaine_substring_list = config['cocaine_substring_list']
#cathinones_substring_list = config['cathinones_substring_list']
#diazepam_substring_list = config['diazepam_substring_list']
#alprazolam_substring_list = config['alprazolam_substring_list']
#clonazepam_substring_list = config['clonazepam_substring_list']
#nitazene_substring_list = config['nitazene_substring_list']
#orphine_substring_list = config['orphine_substring_list']
#adrenergic_list = config['adrenergic_list']
#othernovelbenzos_list = config['othernovelbenzos_list']
#SCRA_substring_list = config['SCRA_substring_list']
#cannabinoids_substring_list = config['cannabinoids_substring_list']
#psychedelics_substring_list = config['psychedelics_substring_list']
#cuttingagents_substring_list = config['cuttingagents_substring_list']

#df_benzo_month = df_benzo.loc[df_benzo['date_received'].dt.month == 5]

def counterfeit_map(df, filename, intent_list, result_list, include_all=False, save=False, plots_path=plots_path):
    # Initialize map
    m = folium.Map(
        location=[53.989955, -3.151694],  # center of the map
        zoom_start=5,  # dezoom
        tiles='cartodb positron'  # background style 
    )
    #folium.TileLayer('cartodb positron', control=False).add_to(m)
    cluster = plugins.MarkerCluster(name=intent_list[0]).add_to(m)
    cluster_2 = plugins.MarkerCluster(name=result_list[0]).add_to(m)
    # Add all the individual earthquakes to the map
    for idx, row in df.iterrows():
        if type(row['minor']) == float:
            row['minor'] = str('')
        if len(row['minor']) ==0:
            #popup = f"{row['postcode']} – Sold as {row['intent']}, tested as {row['major']}"
            popup = f"""
                <h1>{idx}</h1>
                <p>
                Postcode: <b>{row['postcode']}</b><br/>
                Date: <b>{row['date_received']}</b><br/>
                Form: <b>{row['colour']} {row['form']}</b><br/>
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
                Form: <b>{row['colour']} {row['form']}</b><br/>
                Sold as: <b>{row['intent']}</b><br/>
                Tested as: <b>{row['major']}</b> with <b>{row['minor']}</b><br/>
                </p>
                """
        
        color = '#1e3d77' if any(substring in str.lower(row['intent']) for substring in intent_list) and any(substring in str.lower(row['major']) or str.lower(row['minor']) for substring in result_list) else '#ffde5b'
        try:
            if any(substring in str.lower(row['intent']) for substring in intent_list) and any(substring in str.lower(row['major']) or str.lower(row['minor']) for substring in result_list):
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=15,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.5,
                    weight=1,
                    popup=popup,
                    lazy=True
                ).add_to(cluster)
            elif include_all == True:
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=15,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.5,
                    weight=1,
                    popup=popup,
                    lazy=True
                ).add_to(cluster_2)
        except:
            pass
    if save:
        m.save(f'data/{filename}_map.html')
    return m

def dateFilter(df, from_date, to_date):
    'from_date and to_date must be in YYYY-MM-DD format'
    if len(from_date) == len(to_date) == 10:
        print(f'{len(df[(df['date_received'] >= from_date) & (df['date_received'] <= to_date)])} results included between {from_date} and {to_date}.')
        return df[(df['date_received'] >= from_date) & (df['date_received'] <= to_date)]
    else:
        print('ERROR: Date filtering failed. Input dates are not in YYYY-MM-DD format.')
        print(from_date, to_date)
        return df

def getCategories(type_arg):
    type = str.lower(type_arg)
    if type and 'opioid' in type:
        categories = {
            'Nitazenes': substring_dict['nitazene'],
            'Orphines': substring_dict['orphine'],
            'α2-adrenergic agonists': substring_dict['adrenergic'],
            'Benzos': substring_dict['benzo'][1:], #removing 'benzo'
            'Ketamine': ['ketamine'],
            'Promethazine': ['promethazine']
        }
    elif type and 'vape' in type:
        categories = {
            'SCRAs': substring_dict['SCRA'],
            'Cannabinoids': substring_dict['cannabinoid'],
            'Psychedelics': substring_dict['psychedelic'],
            'Opioids': substring_dict['opioid'][1:], #removing 'oxy'
            'Ketamine': ['ketamine']
        }
    elif type and 'benzo' in type: 
        categories = {
            'Nitazenes': substring_dict['nitazene'],
            'Medetomidine': ['medetomidine'],
            'Tramadol': ['tramadol'],
            'Methamphetamine': ['methamphetamine'],
            'Promethazine': ['promethazine'],
            'Ethylbromazolam': ['ethylbromazolam'],
            'Other novel benzos': substring_dict['othernovelbenzo'],
            'Bromazolam': ['bromazolam'],
            'Etizolam': ['etizolam']
        }
    elif type and 'cocaine' in type:
        categories = {
            'Nitazenes': substring_dict['nitazene'],
            'Opioids': substring_dict['opioid'][1:], #removing 'oxy'
            'α2-adrenergic agonists': substring_dict['adrenergic'],
            'Amphetamines': ['amphetamine'],
            'Cathinones': substring_dict['cathinone'],
            'Ketamine': ['ketamine'],
            'Cutting agents': substring_dict['cuttingagent'],
            'Impurities': substring_dict['cocaineimpurities']
        }
    else:
        categories = {
            'Orphines': substring_dict['orphine'],
            'Nitazenes': substring_dict['nitazene'],
            'α2-adrenergic agonists': substring_dict['adrenergic'],
            'Benzos': substring_dict['benzo'][1:],
            'SCRAs': substring_dict['SCRA'],
            'Cannabinoids': substring_dict['cannabinoid'],
            'Psychedelics': substring_dict['psychedelic']
        }
    return categories

def concernMap(df, categories, filename='',include_all=False, save=False, sort_by_form=True):
    # Initialize map
    m = folium.Map(
        location=[53.989955, -3.151694],  # center of the map
        zoom_start=5,  # dezoom
        tiles='cartodb positron'  # background style
    )

    num_categories = len(categories.keys())
    colormap = cm['rainbow_r'].resampled(num_categories)
    category_colors = {}
    for i, cat_name in enumerate(categories.keys()):
        rgba = colormap(i)
        category_colors[cat_name] = colors.rgb2hex(rgba)

    fallback_color = '#1e3d77'
    
    cluster_dict = {}
    cluster_count = {}
    for cat_name in categories.keys():
        cluster_dict[cat_name] = plugins.MarkerCluster(name=cat_name).add_to(m)
        cluster_count[cat_name] = 0
    
    if include_all:
        other_cluster = plugins.MarkerCluster(name="Other Compounds").add_to(m)
    
    #featureGroups = {}
    #if sort_by_form:
        #df['form'] = df['form'].fillna('Not stated')
        #for i in set(df['form']):
            #featureGroups[i] = folium.FeatureGroup(name=i)
    
    # Add all the individual samples to the map
    num_points = 0
    for idx, row in df.iterrows():
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
        minor_str = str(row['minor']).lower() if pd.notna(row['minor']) else ""
        major_str = str(row['major']).lower() if pd.notna(row['major']) else ""
        form_str = str(row['form']) if pd.notna(row['form']) else ""
        intent_str = str(row['intent']).lower() if pd.notna(row['intent']) else ""
        
        if not minor_str:
            #popup = f"{row['postcode']} – Sold as {row['intent']}, tested as {row['major']}"
            popup = f"""
                <h1>{idx}</h1>
                <p>
                Postcode: <b>{row['postcode']}</b><br/>
                Date: <b>{row['date_received']}</b><br/>
                Form: <b>{row['colour']} {row['form']}</b><br/>
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
                Form: <b>{row['colour']} {row['form']}</b><br/>
                Sold as: <b>{row['intent']}</b><br/>
                Tested as: <b>{row['major']}</b> with <b>{row['minor']}</b><br/>
                </p>
                """
        assigned_cluster = None
        marker_color = fallback_color # fallback colour

        for cat_name, substrings in categories.items():
            if any(sub.lower() in major_str or sub.lower() in minor_str for sub in substrings):
                assigned_cluster = cluster_dict[cat_name]
                marker_color = category_colors[cat_name] # Match pin color to cluster group
                cluster_count[cat_name]+=1
                break  

        if assigned_cluster is not None:
            marker = folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=10,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.7,
                weight=1,
                popup=popup,
                lazy=True
            )
            marker.add_to(assigned_cluster)
            num_points+=1
            #if sort_by_form:
                #marker.add_to(featureGroups.get(form_str))
        elif include_all==True:
            marker=folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=10,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.7,
                weight=1,
                popup=popup,
                lazy=True
            )
            marker.add_to(other_cluster)
            num_points+=1
            #if sort_by_form:
                #marker.add_to(featureGroups.get(form_str))
        
    legend_html = f'''
         <div id='big-legend-wrap' style="position: fixed; 
                     bottom: 10px; left: 10px; width: 240px; max-height: 320px; 
                     overflow-y: auto; border:2px solid grey; z-index:9999; font-size:12px;
                     background-color:white; opacity: 0.90; padding: 10px;
                     border-radius: 10px; font-family: sans-serif;">
            <input type="checkbox" id="legend">
            <label for="legend"></label>
            <b style="font-size: 14px; margin-top:0; position: sticky; top: 0;">Compound Found</b>
            <div class="menu-content">
    '''
    for cat, col in category_colors.items():
        legend_html += f'<p style="margin: 4px 0;"><i class="fa fa-circle" style="color:{col}; margin-right: 4px;"></i> {cat} ({cluster_count[cat]})</p>'
    if include_all:
        legend_html += f'<p style="margin: 4px 0;"><i class="fa fa-circle" style="color:{fallback_color}; margin-right: 4px;"></i> Other ({num_points-sum(cluster_count.values())})</p>'
    
    if filename!='':
        dates = []
        for d in filename.split('_')[-1].replace('.csv','').split('-'):
            if len(d)==4:
                dates.append(dt.strptime(d, '%Y'))
            else:
                dates.append(dt.strptime(d, "%d%m%y").date())
        if len(dates)==2 and dates[0].year==dates[1].year:
            dateString = dates[0].strftime("%d %b")+' — '+dates[1].strftime("%d %b %Y")
        elif len(dates)==2:
            dateString = dates[0].strftime("%d %b %Y")+' — '+dates[1].strftime("%d %b %Y")
        elif len(dates[0].strftime("%Y"))==4:
            dateString = dates[0].strftime("%Y")
        else:
            dateString = ''
            print('No dates found!')
    else:
        dates = df['date_received'].copy()
        dates = pd.to_datetime(dates)
        dateString = dates.min().strftime("%d %b %Y")+' — '+dates.max().strftime("%d %b %Y")
    legend_html += f'''
            <p style="border-top: 1px solid #eee; padding-top: 4px; margin: 4px 0 0 0; font-size: 10px;">Colour = highest-priority compound at location.
            <br/>Mapped {num_points} samples tested by <a href="https://wedinos.wales" target="_blank">WEDINOS</a>:<br/>{dateString}</p>
            </div>
        </div>'''
    legend_html +='''
        <style>
        .menu-content {
            max-height: 0;
            overflow: hidden;
        }
        input#legend {
            display: none;
        }
        input + label:after {
            content: '▲';
        }
        input:checked + label:after {
            content: '▼';
        }
        input:checked ~ .menu-content {
            max-height: 100%;
        }
        @media (max-width: 600px) {
            #big-legend-wrap {
                display: none;
            }
        }
        '''
    
    for i, cat_name in enumerate(category_colors.keys()): 
        print(i, cat_name)
        legend_html += f'.leaflet-control-layers-overlays > label:nth-child({i+1}) input'+'{accent-color: '+category_colors[cat_name]+'''; } 
        '''
    
    legend_html += '''
                    .leaflet-touch .leaflet-control-layers-toggle {
                        width: 30px !important;
                        height: 30px !important;
                    }
                    .leaflet-retina .leaflet-control-layers-toggle {
                        background-image: url(assets/filtericon.jpg);
                        background-size: 26px 26px !important;
                    }
                    .leaflet-touch .leaflet-bar a {
                        text-decoration: none;
                    }
                    '''

    legend_html += '</style>'
    m.get_root().html.add_child(folium.Element(legend_html))

    #if sort_by_form:
        #for fg in featureGroups.values():
            #m.add_child(fg)
    plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    folium.LayerControl().add_to(m)
    
    #if sort_by_form:
        #plugins.GroupedLayerControl(
            #groups={'Sample form': list(featureGroups.values())},
            #collapsed=False,
        #).add_to(m)

    # Define your text and styling (adjust position with top, bottom, left, right) #border-radius: 5px; border: 1px solid grey; 
    watermark_html = """
        <a href="https://brp.org.uk" target="_blank" title="Powered by the Benzo Research Project">
            <img style="position: fixed; height: 14px; width: 14px;
                    bottom: 0px; right: 246.63px; 
                    z-index:9990;" 
                    src='https://brp.org.uk/uploads/1/3/9/0/139000106/custom_themes/134408445896420373/files/images/brp_logo.png'/>
        </a>
    """

    # Add the element to the map root
    m.get_root().html.add_child(folium.Element(watermark_html))

    if save:
        m.save(f'{plots_path}/{filename}_map.html')
    

    print(f'Mapped {num_points} samples including:')
    for cat, num in cluster_count.items():
        print(f'{cat}: {num}')
        
    return m

def main():
    '''
    Map data from WEDINOS.
    Args:
    -f = data file to map in .csv format
    -t = type of input data (opioid/benzo)
    -a = (optional) include all samples, y/n
    '''
    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", type=str, metavar="FILENAME",
                        help="data file to map in .csv format")
    #parser.add_argument("-d", "--daterange", type=str, metavar="DATERANGE",
                        #help="date range (month range e.g. 1-9)") # currently doesn't do anything
    parser.add_argument("-t", "--type", type=str, metavar="TYPE",
                        help="type of input data (opioid/benzo)")
    parser.add_argument("-a", "--includeall", type=str, metavar="INCLUDEALL",
                        help="(optional) include all, y/n") 
    #parser.add_argument("-s", "--sortby", type=str, metavar="SORTBY",
                        #help="(optional) form – sort datapoints by sample form") # currently doesn't do anything

    args = parser.parse_args()

    df = pd.read_csv(f'{data_path}/{args.filename}', index_col=0)
    filename = f'{args.filename}'.split('.csv')[0] #+f'_{args.daterange}'
    include_all = True if args.includeall == 'y' else False
    #sortby = True if args.sortby == 'form' else False
    concernMap(df, getCategories(args.type), filename=filename, include_all=include_all, save=save_data) #, sort_by_form=sortby

if __name__ == "__main__":
    main()