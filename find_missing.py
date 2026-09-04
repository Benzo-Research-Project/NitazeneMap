import pandas as pd
import json
from argparse import ArgumentParser
import yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def findMissingIDs(jsonFile, excel_file):
    index_excel = excel_file.index.values
    index_json = []
    for entry in jsonFile:
        index_json.append(list(entry.keys())[0])
        #for key, value in entry.items():
    print(f'Excel: {len(index_excel)} samples')
    print(f'JSON: {len(index_json)} samples')

    set_excel = set(item.lower().strip() for item in index_excel)
    set_json = set(item.lower().strip() for item in index_json)

    missing_ids = list(set_excel - set_json)
    dfMissing = excel_file.loc[excel_file.index.isin(missing_ids)]

    print(f'{len(missing_ids)} samples from the provided .xlsx not found in the .json file.')
    dfMissing['S_CTLReceipt'] = pd.to_datetime(dfMissing['S_CTLReceipt'])
    print(f'Earliest missing sample was received on {dfMissing['S_CTLReceipt'].min()}')
    return dfMissing

def main():
    '''
    Find missing samples.
    Args:
    -f = alerts file (.json)
    -e = excel file (.xlsx)
    '''#-j = join scraped data to master file? y/n (seems to be broken, check samples haven't gone missing)
    parser = ArgumentParser()
    parser.add_argument("-f", "--alertsfile", type=str, metavar="ALERTSFILE",
                        help="alerts file")
    parser.add_argument("-e", "--excelfile", type=str, metavar="EXCELFILE",
                        help="excel file")
    args = parser.parse_args()

    if args.alertsfile and args.excelfile:
        suffix = '' if '.json' in args.alertsfile else '.json'
        suffix2 = '' if '.xlsx' in args.excelfile else '.xlsx'
        with open(f'{config['dataPath']}/{args.alertsfile}{suffix}', 'r', encoding='utf-8') as f:
            all_alerts = json.load(f)
        excel_file = pd.read_excel(f'{config['dataPath']}/{args.excelfile}{suffix2}', index_col=0)

        dfMissing = findMissingIDs(all_alerts, excel_file)

        if config['saveData']:
            dfMissing.to_excel(f'{config['dataPath']}/MISSING_{args.excelfile}{suffix2}')
        else:
            print(dfMissing)
    #findMissingIDs(df, id_list)

if __name__ == "__main__":
    main()