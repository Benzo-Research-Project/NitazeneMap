# Dynamic Scraper for WEDINOS Data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Single page scraper for WEDINOS Data
from bs4 import BeautifulSoup
import json
import re
# Other imports
from argparse import ArgumentParser
import yaml
import time
import pandas as pd
import pgeocode
nomi = pgeocode.Nominatim('gb')
import numpy as np
from join import joinJSON, convertDates
from glob import glob
import os
from datetime import datetime as dt
from map import dateFilter

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

with open(config['substringsPath'], 'r', encoding='utf-8') as f:
    substrings_dict = json.load(f)
substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' not in str(k)}
not_substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' in str(k)} # To rule out any overlapping substrings (e.g. benzo – benzocaine)
#substring_dict = {
#    'opioids': config['opioid_substring_list'],
#    'benzos': config['benzo_substring_list'],
#    'cocaine': config['cocaine_substring_list'],
#    'cathinones': config['cathinones_substring_list'],
#    'diazepams': config['diazepam_substring_list'],
#    'alprazolams': config['alprazolam_substring_list'],
#    'clonazepams': config['clonazepam_substring_list'],
#    'nitazenes': config['nitazene_substring_list'],
#    'orphines': config['orphine_substring_list'],
#    'adrenergics': config['adrenergic_list'],
#    'miscbenzos': config['othernovelbenzos_list'],
#    'heroin': config['heroin_substring_list'],
#    'vapes': config['vapes_substring_list']
#}


#not_substring_dict = {
#    'opioids': config['not_opioid_substring_list'],
#    'benzos': config['not_benzo_substring_list'],
#    'cocaine': ['placeholder'],
#    'cathinones': ['placeholder'],
#    'diazepams': config['not_benzo_substring_list'],
#    'alprazolams': config['not_benzo_substring_list'],
#    'clonazepams': config['not_benzo_substring_list'],
#    'nitazenes': ['placeholder'],
#    'orphines': ['placeholder'],
#    'adrenergics': ['placeholder'],
#    'miscbenzos': config['not_benzo_substring_list'],
#    'heroin': ['placeholder'],
#    'vapes': ['placeholder']
#}
types_list = ['benzo', 'opioid', 'vape', 'cocaine', 'ketamine', 'mdma', 'heroin', 'gabapentinoid', 'zdrug']

save_data = config['saveData']
not_benzo_substring_list = config['not_benzo_substring_list']
col=["date_received","postcode","intent","label","colour","form","consumption_method","effects","major","minor","latitude","longitude"]
allJSON = max(glob(f'{config['dataPath']}/wedinos_alerts_ALL*'), key=os.path.getctime).split('/')[-1]

def scrape(num_pages, url="https://wedinos.wales/sample/"): # old: https://wedinos.org/sample-results
    driver = webdriver.Chrome()
    driver.get(url)

    current_page = 0
    max_pages = num_pages #367 was number of pages for 1 Jan to 4 Dec 2024, 250+21+28+8 for Jan-Aug and Sept 2025
    all_pages = []
    time.sleep(5)

    while current_page < max_pages:
        try:
            # After loading all items, scrape the data
            all_pages.append(driver.page_source)
                
            load_more_button = driver.find_element(By.XPATH, "//nav[@id='sample-results-pagination']/a[@class='phw-pagination__next']") # By.XPATH, "//a[text()='Next']"
            load_more_button.click()
            time.sleep(3)  # Give time for content to load
            current_page += 1
        except:
            break

    driver.quit()
    return all_pages

def parse(all_pages, join, save_data=save_data):
    all_alerts = []
    dates = []
    for page in all_pages:
        soup = BeautifulSoup(page, "html.parser")
        alerts = soup.find_all("article", class_="sample-results__result")
        #print(alerts)
        #all_alerts.append(alerts)
        for alert in alerts:
            try:
                tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
                code = str(alert).split('<h2 class="nhsuk-u-margin-top-4 nhsuk-u-margin-bottom-2 nhsuk-heading-m">',1)[1].split('</h2>',1)[0]
                date_received = str(alert).split('<p>Date received - ',1)[1].split('</p>',1)[0]
                postcode = tag_re.sub('', str(alert).split('''<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Postcode</th>''',1)[1].split('</td>',1)[0])
                intent = tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Purchase intent</th>',1)[1].split('</td>',1)[0])
                label = tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Package label</th>',1)[1].split('</td>',1)[0])
                colour = tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Sample colour</th>',1)[1].split('</li>',1)[0])
                form = tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Sample form</th>',1)[1].split('</td>',1)[0])
                consumption_method = tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Consumption method',1)[1].split('</td>',1)[0])
                effects = list(filter(None, tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Self-reported effects',1)[1].split('</ul>',1)[0]).split('\n')))
                major = list(filter(None, tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Sample upon analysis (major)</th>',1)[1].split('</ul>',1)[0]).split('\n'))) # needs splitting by <li class="nhsuk-u-font-size-16"><a class="substanceLink" href="
                minor = list(filter(None, tag_re.sub('', str(alert).split('<th class="nhsuk-u-font-size-16 nhsuk-u-padding-top-2 nhsuk-u-padding-bottom-2">Sample upon analysis (minor)</th>',1)[1].split('</td>',1)[0]).split('\n'))) # needs splitting by 
                minor_processed = ", ".join(str(x) for x in minor)
                
                myAlertData = {
                    "date_received": date_received,
                    "postcode": ' '.join(postcode.split()),
                    "intent": ' '.join(intent.split()),
                    "label": ' '.join(label.split()),
                    "colour": ' '.join(colour.split()),
                    "form": ' '.join(form.split()),
                    "consumption_method": ' '.join(consumption_method.split()),
                    "effects": ", ".join(str(x) for x in effects[1:]), # removes first blank item in effects list
                    "major": ", ".join(str(x) for x in major),
                    "minor": minor_processed if minor_processed.lower() != "not stated" else ""
                }
                print(f"{myAlertData['postcode']}: Sold as {myAlertData['intent']} ({myAlertData['label']}), was actually {myAlertData['major']}.")
                all_alerts.append({code: myAlertData})
                
                try:
                    date = dt.strptime(date_received, '%d/%m/%Y')
                except:
                    date = dt.strptime(date_received, '%d %b %Y')

                dates.append(date)
            except Exception as e:
                print(f"Error processing alert: {e}")
                pass
    if save_data:
        daterange = f'{min(dates).strftime('%d%m%y')}-{max(dates).strftime('%d%m%y')}'
        with open(f'{config['dataPath']}/wedinos_alerts_{daterange}.json', 'w', encoding='utf-8') as f:
            json.dump(all_alerts, f, ensure_ascii=False, indent=4)

        if join=='y': # indented inside if save as it has to call the scraped file from path
            time.sleep(2)
            print(f'Joining scraped data to {allJSON}...')
            joinJSON([allJSON,f'wedinos_alerts_{daterange}.json'], config['dataPath'], save_data=save_data)
    return all_alerts

def getFilteredDataframe(all_alerts, component_type, daterange='', intent_only=False, save_data=save_data): #not_substring_list=['placeholder'], 
    substring_list = substring_dict[component_type]
    not_substring_list = not_substring_dict['not_'+component_type]
    df = pd.DataFrame(columns=col)
    for alert in all_alerts:
        for i in alert:
            # Removing conflicting substrings before filtering
            intentcontentString = str.lower(alert[i]['intent'].lower())+' '+str.lower(alert[i]['major'].lower())+' '+str.lower(alert[i]['minor'].lower())
            intentString = str.lower(alert[i]['intent'].lower())
            for conflictString in not_substring_list:
                intentcontentString = intentcontentString.replace(conflictString,'')
                intentString = intentString.replace(conflictString,'')
                
            # Filtering by substrings
            if (intent_only==False and any(substring in intentcontentString for substring in substring_list)) or (intent_only==True and any(substring in intentString for substring in substring_list)):
                try:
                    if str(nomi.query_postal_code(alert[i]['postcode'])['latitude']) != 'nan':
                        lat, long = float(nomi.query_postal_code(alert[i]['postcode'])['latitude']), float(nomi.query_postal_code(alert[i]['postcode'])['longitude'])
                    else:
                        pcode = alert[i]['postcode'][:3]
                        lat, long = float(nomi.query_postal_code(pcode)['latitude']), float(nomi.query_postal_code(pcode)['longitude'])
                except:
                    print(f"Error with postcode {alert[i]['postcode']}, using default coordinates.")
                    lat, long = 0, 0 # Alternative if this messes up the map: Default to London coordinates if postcode lookup fails 51.509865, -0.118092
                
                alert[i]['minor'] = alert[i]['minor'] if str.lower(alert[i]['minor'])!='not stated' else ''
                alert[i]['latitude'] = lat
                alert[i]['longitude'] = long
                df.loc[i] = pd.Series(alert[i])
                print(i,alert[i]['date_received'], alert[i]['postcode'],'– Sold as', alert[i]['intent'], ', tested as',alert[i]['major'], 'with' if(len(alert[i]['minor'])>=1) else '', alert[i]['minor'])
    print(df.head(5))

    df = convertDates(df)
    if daterange!='':
        datelist = []
        for i in daterange.split('-'):
            datelist.append(dt.strftime(dt.strptime(i,'%d%m%y'),'%Y-%m-%d'))
        df = dateFilter(df,datelist[0],datelist[1])
    dates = f'{df['date_received'].min().strftime('%d%m%y')}-{df['date_received'].max().strftime('%d%m%y')}'

    if intent_only:
        filename = f'{config['dataPath']}/wedinos_{component_type}s_intent_{dates}.csv'
    else:
        filename = f'{config['dataPath']}/wedinos_{component_type}s_all_{dates}.csv'
    if save_data:
        df.to_csv(filename, sep=',', encoding='utf-8')
        print(f'Saved {len(df)} sample results as {filename}.')
    return df

def main():
    '''
    Scrape and parse data from WEDINOS.
    Args:
    -n = number of pages to scrape
    -d = filter by dates in DDMMYY-DDMMYY format
    -f = alerts file to reparse (optional: only needed to reparse saved alert .json files, if leaving -n blank)
    -t = type of drugs to filter for (benzos/opioids/alprazolam/diazepam/heroin/nitazenes/adrenergics/orphines/miscbenzos); all = all drugmapuk categories
    -i = filter by intent only? y/n
    '''#-j = join scraped data to master file? y/n (seems to be broken, check samples haven't gone missing)
    parser = ArgumentParser()
    parser.add_argument("-n", "--num", type=int,
                        help="number of pages to scrape", metavar="NUM")
    parser.add_argument("-d", "--daterange", type=str, metavar="DATERANGE",
                        help="dates scanned in DDMMYY-DDMMYY format") # could probably automate this in future
    parser.add_argument("-f", "--alertsfile", type=str, metavar="ALERTSFILE",
                        help="alerts file to reparse")
    parser.add_argument("-t", "--type", type=str, metavar="TYPE",
                        help="type of drugs to filter for (benzos/opioids/alprazolam/diazepam/heroin/nitazenes/adrenergics/orphines/miscbenzos); all = all drugmapuk categories")
    parser.add_argument("-i", "--intent", type=str, metavar="INTENT",
                        help="filter by intent only? y/n")
    parser.add_argument("-j", "--join", type=str, metavar="JOIN",
                        help="join scraped data to master file? y/n")
    start_time = dt.now()
    args = parser.parse_args()
    if args.num:
        all_pages = scrape(args.num)
        all_alerts = parse(all_pages, args.join)
        print('Scrape and parse duration: {}'.format(dt.now() - start_time))
    elif args.alertsfile:
        suffix = '' if '.json' in args.alertsfile else '.json'
        with open(f'{config['dataPath']}/{args.alertsfile}{suffix}', 'r', encoding='utf-8') as f:
            all_alerts = json.load(f)

    if args.intent == 'y':
        intent_only=True
    else:
        intent_only=False
    daterange = args.daterange if args.daterange else ''
    if args.type=='all':
        for type in types_list:
            getFilteredDataframe(all_alerts, type, daterange=daterange, intent_only=intent_only)

    elif args.type:
        type = args.type if args.type[-1]!='s' else args.type[:-1]
        getFilteredDataframe(all_alerts, type, daterange=daterange, intent_only=intent_only)
    
    end_time = dt.now()
    print('Total duration: {}'.format(end_time - start_time))
if __name__ == "__main__":
    main()