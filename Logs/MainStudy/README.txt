####################################
## Usage of data analysis scripts ##
####################################

## Adding a new participant ##
Create participant / ID inside "data" folder
Create a directory named "raw" inside this and move all the participant's runs inside (practice, baseline, and staircase runs).

## Splitting data into individual runs ##
Run "python LogFileSplitter.py ..\data\Main_Study\P1\raw\P1StaircasePartX.csv" for each of Part1,2 etc. 
Results will be stored in the created "processed" folder

## Participant analysis ##
Run "python dataAnalysis.py ..\data\Main_Study\P_ID".
Outputs individual graphs in "figures", also summary PDF and CSV for data.

## Group summary ##
Run "python groupSummary.py". Outputs a CSV with combined stats and a CSV with means for all participants combined.


