import pandas as pd
import numpy as np
import yaml
import re
from argparse import ArgumentParser

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
save_data = config['saveData']
data_path = config['dataPath']

def joinData(df, df_all):
    for idx, row in df.iterrows():
        if idx in df_all.index:
            print(f"Duplicate index found: {idx}, skipping.")
        else:
            df_all.loc[idx] = row
    return df_all


def main():
    '''
    Join two datasets together and remove duplicates.
    Args:
    -f1 = file path for scraped data (e.g. wedinos_benzos_010126-030526.csv)
    -f2 = file path for scraped data to join to f1 (e.g. wedinos_benzos_290426-300626.csv)'''
    parser = ArgumentParser()
    parser.add_argument("-f1", "--file1", type=str, metavar="FILE1",
                        help="file name for scraped wedinos data – must be inside data folder")
    parser.add_argument("-f2", "--file2", type=str, metavar="FILE2",
                        help="file name for scraped wedinos data – must be inside data folder")

    args = parser.parse_args()
    df_all = pd.read_csv(f'{data_path}/{args.file1}', index_col=0)
    df = pd.read_csv(f'{data_path}/{args.file2}', index_col=0)
    df_joined = joinData(df, df_all)
    if save_data:
        filename1 = args.file1.split('-')[0] # returns wedinos_benzos_DDMMYY
        filename2 = args.file2.split('-')[1] # returns DDMMYY.csv
        df_joined.to_csv(f'{data_path}/{filename1}-{filename2}', sep=',', encoding='utf-8')

if __name__ == "__main__":
    main()