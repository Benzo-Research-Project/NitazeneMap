# NitazeneMap
### Description
This is a work in progress package used to monitor and visualise UK drug supply trends using Python and a web API, with a particular focus on nitazenes and counterfeit benzodiazepines. 

All data used in this package is owned by WEDINOS and should not be interpreted as a representative sample. The use of this package is for informational purposes only. 

### Maintained by: 
AJ Martin, Benzo Research Project

### Contact:
aj@brp.org.uk

## Instructions
### 1. Installation
1. Clone this repository
2. Set up a virtual environment:
  ```console
cd /path/to/repository
python -m venv .venv
source .venv/bin/activate
  ```
3. Install dependencies:
  ```console
pip install -r requirements.txt
  ```
### 2. Data scraping
1. Amend configurations in config.yaml, such as whether to save scraped data (saveData: True/False) and where to save it to (dataPath: (default is the data file))
2. Run the script:
  ```console
python scraper.py -n [number of pages to scrape] -d [DDMMYYY–DDMMYYYY]
  ```
  Args:
  
      -n = number of pages to scrape (check the website first, e.g. using the filtering options)
      
      -d = dates scanned in DDMMYYYY-DDMMYYYY format (note: this is currently used for file naming only)
      
      -f = (optional) alerts file to reparse (optional: only needed to reparse saved alert .json files, if leaving -n blank)

### 3. Joining datasets together
1. Amend configurations in config.yaml, such as whether to save amended data (saveData: True/False) and where to pull data from and save to (dataPath: (default is the data file))
2. Run the script, for example:
  ```console
python join.py -f1 [data file 1] -f2 [data file 2]
  ```
  Args:
  
      -f1 = file path for scraped data (e.g. wedinos_benzos_010126-030526.csv)

      -f2 = file path for scraped data to join to f1 (e.g. wedinos_benzos_290426-300626.csv)
  
  Returns a joined file with duplicates removed (e.g. wedinos_benos_010126-300626.csv).

### 4. Filtering by country
1. Amend configurations in config.yaml, such as whether to save amended data (saveData: True/False) and where to pull data from and save to (dataPath: (default is the data file))
2. Run the script, for example:
  ```console
python geofilter.py -f wedinos_benzos_february_2026.csv -c Scotland
  ```
  Args:
  
      -f = file path for scraped data (e.g. 'data/wedinos_benzos_2025.csv)
      
      -c = (optional) filter by country (options: England, Wales, Scotland, Northern Ireland, Channel Islands, Isle of Man)
