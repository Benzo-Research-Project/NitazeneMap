import pandas as pd
import numpy as np
import yaml
import re
from argparse import ArgumentParser

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
save_data = config['saveData']
data_path = config['dataPath']
dfPostcode = pd.read_csv("data/UK_postcode_areas.csv", index_col=0)

def splitPostcode(postcode):
    if type(postcode)==str:
        return re.split(r'(\d+)',postcode)[0]
    else:
        return 'n/a'
    
def addGeoInfo(df, filename, dfPostcode=dfPostcode, save_data=save_data):
    '''Append WEDINOS results with geographic area/country for filtering.'''
    df['Postcode prefix'] = df['postcode'].apply(splitPostcode)
    dict_list = []
    df2 = pd.DataFrame(columns=['ID','district', 'region', 'country'])
    for idx, row in df.iterrows():
        try:
            row_dict = {'ID':idx,
                        'district':dfPostcode.loc[row['Postcode prefix'],'Postcode district'],
                        'region':dfPostcode.loc[row['Postcode prefix'],'UK region'],
                        'country':dfPostcode.loc[row['Postcode prefix'],'UK country']}
            #df.loc[idx,'Postcode district, UK region, UK country']=dfPostcode.loc[row['Postcode prefix']].values
        except:
            print(f'Sample {idx} does not have a valid postcode area.')
            row_dict = {'ID':idx,
                        'district':'n/a',
                        'region':'n/a',
                        'country':'n/a'}
        dict_list.append(row_dict)
    df2 = pd.DataFrame.from_dict(dict_list)
    df2.set_index('ID', inplace=True)
    print(df2.head(5))
    df_merged = df.merge(df2,left_index=True,right_index=True)
    if save_data:
        filename = filename.replace('.csv','')
        df.to_csv(data_path+'/'+filename+'_regions'+'.csv', sep=',', encoding='utf-8')
    return df_merged

def main():
    '''
    Append geographic region/country data to scraped WEDINOS results.
    Args:
    -f = file path for scraped data (e.g. 'data/wedinos_benzos_2025.csv)
    -c = filter by country (options: England, Wales, Scotland, Northern Ireland, Channel Islands, Isle of Man)'''
    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", type=str, metavar="FILENAME",
                        help="file name for scraped wedinos data – must be inside data folder")
    parser.add_argument("-c", "--country", type=str, metavar="COUNTRY",
                        help="which country to filter by e.g. Scotland")

    args = parser.parse_args()
    df = pd.read_csv(f'{data_path}/{args.filename}', index_col=0)
    dfGeo = addGeoInfo(df, args.filename)
    if args.country:
        filtered_df = dfGeo[dfGeo['country'] == args.country]
        print(f"{len(filtered_df)} out of {len(dfGeo)} ({round(100*len(filtered_df)/len(dfGeo),1)}%) results were found for {args.country}")
        if save_data:
            trimmedFilename = args.filename.replace('.csv','')
            df.to_csv(f'{data_path}/{trimmedFilename}_{args.country}.csv', sep=',', encoding='utf-8')
    
if __name__ == "__main__":
    main()