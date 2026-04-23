#### 23-04-26: THIS VERSION IS DEPRECIATED – USE scraper.py ####
# Dynamic Scraper for WEDINOS Data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Single page scraper for WEDINOS Data
import requests
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

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

benzo_substring_list = config['benzo_substring_list']
diazepam_substring_list = config['diazepam_substring_list']
alprazolam_substring_list = config['alprazolam_substring_list']
clonazepam_substring_list = config['clonazepam_substring_list']
nitazene_substring_list = config['nitazene_substring_list']
save_data = config['saveData']

col=["date_received","postcode","intent","label","colour","form","consumption_method","effects","major","minor","latitude","longitude"]

def scrape(num_pages, url="https://wedinos.org/sample-results"):
    driver = webdriver.Chrome()
    driver.get(url)

    current_page = 0
    max_pages = num_pages #367 was number of pages for 1 Jan to 4 Dec 2024, 250+21+28+8 for Jan-Aug and Sept 2025
    all_pages = []

    while current_page < max_pages:
        try:
            # After loading all items, scrape the data
            all_pages.append(driver.page_source)
                
            load_more_button = driver.find_element(By.XPATH, "//a[text()='Next']")
            load_more_button.click()
            time.sleep(3)  # Give time for content to load
            current_page += 1
        except:
            break

    driver.quit()
    return all_pages

def parse(all_pages, daterange, save_data=save_data):
    all_alerts = []
    for page in all_pages:
        soup = BeautifulSoup(page, "html.parser")
        alerts = soup.find_all("div", class_="alert alert-danger")
        #all_alerts.append(alerts)
        for alert in alerts:
            try:
                tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
                code = str(alert).split('<span style="font-size: 1.4em; font-weight: 700">',1)[1].split('</span>',1)[0]
                date_received = str(alert).split('Date Received: <span style="color: black">',1)[1].split('</span>',1)[0]
                postcode = str(alert).split('Postcode: <span style="color: black">',1)[1].split(' - </span>',1)[0]
                intent = str(alert).split('Purchase Intent: <span style="color: black">',1)[1].split('</span>',1)[0]
                label = str(alert).split('Package Label: <span style="color: black">',1)[1].split('</span>',1)[0]
                colour = str(alert).split('Sample Colour: <span style="color: black">',1)[1].split('</span>',1)[0]
                form = str(alert).split('Sample Form: <span style="color: black">',1)[1].split('</span>',1)[0]
                consumption_method = str(alert).split('Consumption Method: <span style="color: black">',1)[1].split('</span>',1)[0]
                effects = str(alert).split('Self-Reported Effects: <span style="color: black">',1)[1].split('</span>',1)[0]
                major = tag_re.sub('', str(alert).split('Sample Upon Analysis (Major): <span style="color: black">',1)[1].split('</span>',1)[0])
                minor = tag_re.sub('', str(alert).split('Sample Upon Analysis (Minor): <span style="color: black">',1)[1].split('</span>',1)[0])
                print(f"{postcode}: Sold as {intent} ({label}), was actually {major}.")
                myAlertData = {
                    "date_received": date_received,
                    "postcode": postcode,
                    "intent": intent,
                    "label": label,
                    "colour": colour,
                    "form": form,
                    "consumption_method": consumption_method,
                    "effects": effects,
                    "major": major,
                    "minor": minor
                }
                all_alerts.append({code: myAlertData})
            except Exception as e:
                print(f"Error processing alert: {e}")
                pass
    if save_data:
        with open('data/wedinos_alerts_'+daterange+'.json', 'w', encoding='utf-8') as f:
            json.dump(all_alerts, f, ensure_ascii=False, indent=4)
    return all_alerts

def getFilteredDataframe(all_alerts, daterange, substring_list=benzo_substring_list, save_data=save_data):
    df = pd.DataFrame(columns=col)
    for alert in all_alerts:
        for i in alert:
            if any(substring in (str.lower(alert[i]['intent'].lower()) or str.lower(alert[i]['major'].lower()) or str.lower(alert[i]['minor'].lower())) for substring in substring_list):
                try:
                    if str(nomi.query_postal_code(alert[i]['postcode'])['latitude']) != 'nan':
                        lat, long = float(nomi.query_postal_code(alert[i]['postcode'])['latitude']), float(nomi.query_postal_code(alert[i]['postcode'])['longitude'])
                    else:
                        pcode = alert[i]['postcode'][:3]
                        lat, long = float(nomi.query_postal_code(pcode)['latitude']), float(nomi.query_postal_code(pcode)['longitude'])
                except:
                    print(f"Error with postcode {alert[i]['postcode']}, using default coordinates.")
                    lat, long = 0, 0 # Alternative if this messes up the map: Default to London coordinates if postcode lookup fails 51.509865, -0.118092

                alert[i]['latitude'] = lat
                alert[i]['longitude'] = long
                df.loc[i] = pd.Series(alert[i])
                print(i,alert[i]['date_received'], alert[i]['postcode'],'– Sold as', alert[i]['intent'], ', tested as',alert[i]['major'], 'with' if(len(alert[i]['minor'])>=1) else '', alert[i]['minor'])
    print(df.head(5))
    if save_data:
        df.to_csv('data/wedinos_'+substring_list[0]+'s_'+daterange+'.csv', sep=',', encoding='utf-8')
    return df

def main():
    '''
    Scrape and parse data from WEDINOS.
    Args:
    -n = number of pages to scrape
    -d = dates scanned in DDMMYYYY-DDMMYYYY format
    -f = alerts file to reparse (optional: only needed to reparse saved alert .json files, if leaving -n blank)
    '''
    parser = ArgumentParser()
    parser.add_argument("-n", "--num", type=int,
                        help="number of pages to scrape", metavar="NUM")
    parser.add_argument("-d", "--daterange", type=str, metavar="DATERANGE",
                        help="dates scanned in DDMMYYYY-DDMMYYYY format") # could probably automate this in future
    parser.add_argument("-f", "--alertsfile", type=str, metavar="ALERTSFILE",
                        help="alerts file to reparse")

    args = parser.parse_args()
    if args.num:
        all_pages = scrape(args.num)
        all_alerts = parse(all_pages, args.daterange)
    elif args.alertsfile:
        with open('data/'+args.alertsfile+'.json', 'r', encoding='utf-8') as f:
            all_alerts = json.load(f)
    
    df_benzo = getFilteredDataframe(all_alerts, args.daterange, substring_list=benzo_substring_list)
    df_nit = getFilteredDataframe(all_alerts, args.daterange, substring_list=nitazene_substring_list)

if __name__ == "__main__":
    main()