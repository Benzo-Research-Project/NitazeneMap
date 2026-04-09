# NitazeneMap
### Description
This is a work in progress package used to monitor and visualise UK drug supply trends using Python and a web API, with a particular focus on nitazenes and counterfeit benzodiazepines. 

All data used in this notebook is owned by WEDINOS and should not be interpreted as a representative sample. The use of this notebook is for informational purposes only. 

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
      
