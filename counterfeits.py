import yaml
import json
import re
import pandas as pd
from argparse import ArgumentParser
from datetime import datetime as dt
from map import dateFilter
from matplotlib.pyplot import subplots

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
with open(config['substringsPath'], 'r', encoding='utf-8') as f:
    substrings_dict = json.load(f)
substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' not in str(k)}
not_substring_dict = {k: v for k, v in substrings_dict.items() if 'not_' in str(k)} # To rule out any overlapping substrings (e.g. benzo – benzocaine)

data_path = config['dataPath']
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
### New – checking if benzos were counterfeit or not
# 27.06.26 added  and (row['minor']=='') to not counterfeit condition
def checkStatus(df, intent, dates=''):
    "Adds columns to a dataframe indicating if benzos were sold as benzos and if they were counterfeit or not"

    df['minor'] = df['minor'].fillna('')
    df['major'] = df['major'].fillna('')
    df['label'] = df['label'].fillna('')
    if dates!='':
        datelist = []
        for i in dates.split('-'):
            datelist.append(dt.strftime(dt.strptime(i,'%d%m%y'),'%Y-%m-%d'))
        df = dateFilter(df,datelist[0],datelist[1])
    else:
        print('NB: No date provided to checkStatus function. Please double-check that you filtered by dates prior if needed.')
    #print(df)
    
    for idx, row in df.iterrows():
        if any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict[intent]):
            sold_as='1'
            if all(substring not in str.lower(row['major']+' '+str.lower(row['minor'])) for substring in substring_dict[intent]):
                not_class='1'
            else:
                not_class='0'

            try: # try-except to avoid errors with missing testing data
                # checking if sample contents match intent/label and there are no other minor components
                if ((str.lower(row['major']) in str.lower(row['intent']+' '+str.lower(row['label']))) or (str.lower(row['intent']) in str.lower(row['major'])) or (str.lower(row['label']) in str.lower(row['major']))) and ((row['minor']=='') or ((str.lower(row['major'])==str.lower(row['minor'])) and row['major']!='')):
                    status='not counterfeit'
                elif ('unable to identify' in str.lower(row['major'])):
                    status='inconclusive'
                # checking diazepam spellings
                elif intent == 'benzo' and any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['diazepam']):
                    if ('diazepam' in str.lower(row['major'])) and row['minor']=='':
                        status='not counterfeit'
                    else:
                        status='counterfeit'
                # checking xanax spellings
                elif intent == 'benzo' and any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['alprazolam']):
                    if ('alprazolam' in str.lower(row['major'])) and (row['minor']==''):
                        status='not counterfeit'    
                    else:
                        status='counterfeit'
                # checking clonazepam spellings
                elif intent == 'benzo' and any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['clonazepam']):
                    if ('clonazepam' in str.lower(row['major'])) and (row['minor']==''):
                        status='not counterfeit'
                    else:
                        status='counterfeit'
                elif intent == 'benzo' and ('benzo' in str.lower(row['intent']+' '+str.lower(row['label']))):
                    if any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['diazepam']):
                        if ('diazepam' in str.lower(row['major'])) and (row['minor']==''):
                            status='not counterfeit'
                        else:
                            status='counterfeit'
                    elif any(substring in str.lower(row['major']) for substring in substring_dict[intent]) and (row['minor']==''):
                        status='not counterfeit'
                    else:
                        status='counterfeit'
                elif intent == 'vape' and (str.lower(row['major'])=='nicotine') and (str.lower(row['minor'])==''):
                    status='not counterfeit'
                elif intent == 'vape' and any(substring in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['cannabinoid']):
                    if any(substring in str.lower(row['major']) for substring in ['thc','tetrahydrocannabinol']) and (row['minor']==''):
                        status='not counterfeit'
                    else:
                        status='counterfeit'
                elif intent == 'ketamine' and (str.lower(row['major'])=='ketamine') and (str.lower(row['minor'])=='') and all(substring not in str.lower(row['intent']+' '+str.lower(row['label'])) for substring in substring_dict['arylcyclohexamine']):
                    status='not counterfeit'
                elif intent == 'mdma' and (str.lower(row['major'])=='mdma') and (str.lower(row['minor'])==''):
                    status='not counterfeit'    
                else:
                    status='counterfeit'
                    #print(row['intent'],': ',row['major'],'with',row['minor'])
            except:
                status='inconclusive'
        else:
            sold_as='0'

        # TO UPDATE: Pandas doesn't like this, even though it works
        df.loc[idx,'sold_as'] = sold_as
        df.loc[idx,'status'] = status
        df.loc[idx,'class-mismatch'] = not_class
    total = len(df)
    #print(df)
    total_benzo_intent = len(df[df['sold_as'] == '1'])
    total_not_classs = len(df[df['sold_as'] == '0'])
    total_counterfeit_benzos = len(df[(df['sold_as'] == '1') & (df['status'] == 'counterfeit')])
    total_correct_benzos = len(df[(df['sold_as'] == '1') & (df['status'] == 'not counterfeit')])
    unknown_benzos = len(df[(df['sold_as'] == '1') & (df['status'] == 'inconclusive')])
    total_not_classs = len(df[df['sold_as'] == '0'])
    non_benzos = len(df[df['class-mismatch'] == '1'])
    print(f'Between {dates},',total_benzo_intent,'out of',total,f'samples mentioning {intent} were sold as {intent} ({(100*total_benzo_intent/total):.1f}%), of which:')
    print('-',total_correct_benzos,f'{intent} contained what they were sold as ({(100*total_correct_benzos/total_benzo_intent):.1f}%)')
    print('-',total_counterfeit_benzos,f'{intent} were counterfeit ({(100*total_counterfeit_benzos/total_benzo_intent):.1f}%)')
    print('-',unknown_benzos,f'samples sold as {intent} were inconclusive ({(100*unknown_benzos/total_benzo_intent):.1f}%)')
    print('-',total_not_classs,f'samples containing {intent} were not sold as {intent} ({(100*total_not_classs/total):.1f}%)')
    print('-',non_benzos,f'samples sold as {intent} did not contain any {intent} ({(100*non_benzos/total):.1f}%)')
    array = [total, total_benzo_intent, total_not_classs, total_counterfeit_benzos, total_correct_benzos, unknown_benzos, non_benzos]
    dictMetrics = {
        'Total': total_benzo_intent,
        'As sold': total_correct_benzos,
        'Mis-sold': total_counterfeit_benzos,
        'Contains but not sold as': total_not_classs,
        'Withdrawal risk': non_benzos,
        'Inconclusive': unknown_benzos,
        'Total including not sold as': total
    }
    return df, dictMetrics

def getContents(df, intent, dates='', counterfeits=True, save=config['saveData'], outpath = config['outPath']):
    if counterfeits:
        df = df.loc[(df['sold_as'] == '1') & (df['status'] == 'counterfeit')]
    contentsColumn = []
    for idx, row in df.iterrows():
        if row['minor'] == '':
            if 'no active' in str.lower(row['major']):
                contentsColumn.append('No Active Component')
            else:
                contentsColumn.append(row['major'])
        else:
            contentsColumn.append(row['major'] + ' with ' + row['minor'])
    
    #df['complete contents'] = contentsColumn
    #Contents = df['complete contents'].value_counts()
    contentsColumn = [re.sub(r' \(.*?\)', '', file) for file in contentsColumn]
    dfC = pd.DataFrame({'complete contents':contentsColumn})
    Contents = dfC['complete contents'].value_counts()
    if save:
        all_or_counterfeit = 'counterfeit' if counterfeits else 'all'
        filename = f'wedinos_{all_or_counterfeit}{intent}s_{dates}.csv'
        Contents.to_csv(f'{outpath}/{filename}', sep=',', encoding='utf-8')
    return Contents

def getUniqueContents(contents, intent, dates='', counterfeits=True, save=config['saveData'], outpath = config['outPath']):
    df = pd.DataFrame(contents)
    contents_list = []
    for i in df.index:
        if (', ' not in i) and (' with ' not in i):
            contents_list.append(i)
        else:
            if ' with ' in i:
                i_list = i.split(' with ')
                for j in i_list:
                    if ', ' in j:
                        j = j.split(', ')
                        for k in j:
                            contents_list.append(k)
                    else:
                        contents_list.append(j)
            if ', ' in i:
                i_list = i.split(', ')
                for j in i_list:
                    if ' with ' in j:
                        j = j.split(' with ')
                        for k in j:
                            contents_list.append(k)
                    else:
                        contents_list.append(j)
    uniqueContents = list(set(contents_list))
    contentsDict = dict.fromkeys(uniqueContents)
    contentsDict = {key: 0 for key in contentsDict}
    for idx, row in df.iterrows():
        for i in uniqueContents:
            if i in idx:
                contentsDict[i] = contentsDict[i]+int(row['count'])
    uniqueCounts = pd.DataFrame(contentsDict.items(), columns=['Compound','Count']).set_index('Compound').sort_values('Count', ascending=False)
    if save:
        all_or_counterfeit = 'counterfeit' if counterfeits else 'all'
        filename = f'wedinos_unique_{all_or_counterfeit}{intent}s_{dates}.csv'
        uniqueCounts.to_csv(f'{outpath}/{filename}', sep=',', encoding='utf-8')
    return uniqueCounts

def plotContents(df_counterfeits, intent, dates, counterfeits=True, save=config['saveData'], plotpath = config['plotsPath']):
    all_or_counterfeit = 'counterfeit' if counterfeits else 'all'
    fig, ax = subplots(figsize=(9, 6))
    ax.title.set_text(f'Contents of {all_or_counterfeit} {intent}, {dates}')
    ax.title.set_fontsize(14)
    df_counterfeits.head(20).sort_values().plot(kind='barh', ax=ax)
    ax.set_xlabel('Samples')
    ax.set_ylabel('Contents')
    ax.grid(axis='x',alpha=0.3)
    text = fig.text(0.50, 0.01, 
                'WEDINOS data, collated by Benzo Research Project (2026)', 
                horizontalalignment='center', wrap=True, fontsize=8)
    fig.tight_layout()
    if save:
        fig.savefig(f'{plotpath}/wedinos_{all_or_counterfeit}{intent}s_{dates}.png', dpi=300)
    return fig

def main():
    '''
    Join two datasets together and remove duplicates.
    Args:
    -f = file path for scraped data (e.g. wedinos_benzos_010126-030526.csv)
    -d = filter by date range (e.g. 010126-010226)
    -i = which drug type are you investigating? e.g. benzo/opioid/diazepam
    -c = all/counterfeits/both'''
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", type=str, metavar="FILE",
                        help="file name for scraped wedinos data – must be inside data folder")
    parser.add_argument("-d", "--daterange", type=str, metavar="DATERANGE",
                        help="filter by date range (e.g. 010126-010226)")
    parser.add_argument("-i", "--intent", type=str, metavar="INTENT",
                        help="which drug type are you investigating? e.g. benzo/opioid/diazepam")
    parser.add_argument("-c", "--counterfeits", type=str, metavar="COUNTERFEITS",
                        help="all/counterfeits/both")

    args = parser.parse_args()

    df = pd.read_csv(f'{data_path}/{args.file}', index_col=0)

    intent = args.intent if args.intent[-1]!='s' else args.intent[:-1]
    df_status, array = checkStatus(df, intent, args.daterange)

    if args.counterfeits == 'both' or 'counterfeits':
        contents = getContents(df_status, intent, args.daterange, counterfeits=True)
        plotContents(contents, intent, args.daterange, counterfeits=True)
        getUniqueContents(contents, intent, args.daterange, counterfeits=True)
    
    if args.counterfeits == 'both' or 'all':
        contents = getContents(df_status, intent, args.daterange, counterfeits=False)
        plotContents(contents, intent, args.daterange, counterfeits=False)
        getUniqueContents(contents, intent, args.daterange, counterfeits=False)

if __name__ == "__main__":
    main()