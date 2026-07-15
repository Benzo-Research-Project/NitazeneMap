import pandas as pd
import numpy as np
import yaml
import json
import re
from argparse import ArgumentParser
from datetime import datetime as dt

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
save_data = config['saveData']
data_path = config['dataPath']

def joinData(args, data_path):
    df_all = pd.read_csv(f'{data_path}/{args.file1}', index_col=0)
    df = pd.read_csv(f'{data_path}/{args.file2}', index_col=0)
    for idx, row in df.iterrows():
        if idx in df_all.index:
            print(f"Duplicate index found: {idx}, skipping.")
        else:
            df_all.loc[idx] = row
    return df_all

def joinJSON(args, data_path, year_restrict, save_data=save_data):
    try:
        files = [args.file1, args.file2]
    except:
        # if files are inputted as a list of strings
        files = args

    td = dict()
    keys = []
    for file in files:
        with open(f'{data_path}/{file}') as fd:
            jsonFile = json.load(fd)
            print(f'{len(jsonFile)} entries in {file}...')
            
            for entry in jsonFile:
                for key, value in entry.items():
                    if (year_restrict and year_restrict in value['date_received']) or not year_restrict:
                        td[key] = value
                        keys.append(key)
                    elif year_restrict and not year_restrict in value['date_received']:
                        print(f'Removing {key} – not in {year_restrict}...')
                    else:
                        print('ERROR')
                        break

    if len(set(keys))<len(keys):
        print('Duplicates removed successfully!')
    else:
        print('WARNING: Duplicates were not found. You may have a gap in your data.')
    final_output = [{key: value} for key, value in td.items()]
    if save_data:
        try:
            if year_restrict:
                jsonFilename = f'wedinos_alerts_{year_restrict}.json'
            else:
                jsonFilename = f'{args.file1.split('-')[0]}-{args.file2.split('-')[1]}'
        except:
            print('NOTE: file will be saved as merged.json. Remember to update the filename')
            jsonFilename = 'merged.json'
        with open(f"{data_path}/{jsonFilename}", "w") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=4)
    
    return td

def convertDates(df_joined):
    dates=[]
    for idx, row in df_joined.iterrows():
        try:
            dates.append(dt.strptime(row['date_received'], '%d/%m/%Y'))
        except:
            dates.append(dt.strptime(row['date_received'], '%d %b %Y'))
    df_joined['date_received']=dates
    df_joined = df_joined.sort_values(by='date_received')
    return df_joined

def main():
    '''
    Join two datasets together and remove duplicates.
    Args:
    -f1 = file path for scraped data (e.g. wedinos_benzos_010126-030526.csv)
    -f2 = file path for scraped data to join to f1 (e.g. wedinos_benzos_290426-300626.csv)
    -d = (optional) standardise date format and sort by date (yes/no)
    -y = (optional) year to restrict joining jsons to, e.g. 2025'''
    parser = ArgumentParser()
    parser.add_argument("-f1", "--file1", type=str, metavar="FILE1",
                        help="file name for scraped wedinos data – must be inside data folder")
    parser.add_argument("-f2", "--file2", type=str, metavar="FILE2",
                        help="file name for scraped wedinos data – must be inside data folder")
    parser.add_argument("-d", "--dateconvert", type=str, metavar="DATECONVERT",
                        help="(optional) standardise date format and sort by date (y/n)")
    parser.add_argument("-y", "--year", type=str, metavar="YEAR",
                        help="(optional) year to restrict joining jsons to, e.g. 2025")

    args = parser.parse_args()

    if args.file1.split('.')[1] == 'json':
        joinJSON(args, data_path, args.year)
    
    elif args.file1.split('.')[1] == 'csv':
        df_joined = joinData(args)
        if args.dateconvert=='y':
            convertDates(df_joined)

        if save_data:
            filename1 = args.file1.split('-')[0] # returns wedinos_benzos_DDMMYY
            try:
                filename2 = args.file2.split('-')[1] # returns DDMMYY.csv
                print(filename2)
            except:
                filename2 = 'DDMMYY.csv'
                print(args.file2, 'Could not split filename2, you may need to amend the filename')
                print(filename2)
            
            df_joined.to_csv(f'{data_path}/{filename1}-{filename2}', sep=',', encoding='utf-8')
    else:
        print('''ERROR: Incompatible data types, please provide a pair of csv or json files. 
            Remember to place input files in the data folder (not in any subfolders).''')
if __name__ == "__main__":
    main()