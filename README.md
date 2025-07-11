Steps to setup:

1. Run "git clone <link from github repo>"
2. Copy over api credentials from email into a .env file in the main folder
3. copy over all_minifigs.csv into processed_data
4. run "pip3 install -r requirements.txt" to install any missing packages

To run, in the main folder do "python run.py". This will scan for minifigs in batches of 100, 
appending to arbitrage/minifig_opprotunities.csv, and then running another batch until out of 
API calls for the day.
