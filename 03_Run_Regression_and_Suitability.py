#---------------------------------------------------------------
#				03_Run_Regression_and_Suitability.py
#---------------------------------------------------------------
import os, pdb
import pandas as pd 
import numpy as np
import Urban_Tree_Functions as urbanTreeLib

tableDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v10_Output_Tables'
figureDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v10_Output_Figures'

inTable = os.path.join(tableDir, 'CBG_Table_v10_forGEE.csv')
outTable = os.path.join(tableDir, 'Suitability_Table_CBG_v10_limit.csv')
outTable_forGEE = os.path.join(tableDir, 'Suitability_Table_CBG_v10_limit_forGEE.csv')

#---------Options-----------
minObs_regression = 11
minObs_cityStats = 4
et_and_ac_numbers = {\
	'06': {'ET_Low': 0.02479, 'ET_High': 0.08643, 'AC_Low': 44.4778, 'AC_High': 52.581},
	'08': {'ET_Low': 0.03611, 'ET_High': 0.1242, 'AC_Low': 48.7995, 'AC_High': 83.5534},
	'09': {'ET_Low': 0.04741, 'ET_High': 0.1243, 'AC_Low': 61.3145, 'AC_High': 86.7047},
	'10': {'ET_Low': 0.06151, 'ET_High': 0.1254, 'AC_Low': 68.6975, 'AC_High': 89.3157},
	'14': {'ET_Low': 0.05992, 'ET_High': 0.13174, 'AC_Low': 71.3986, 'AC_High': 88.0552},
	'15': {'ET_Low': 0.10555, 'ET_High': 0.14603, 'AC_Low': 77.0708, 'AC_High': 85.4442},
	'16': {'ET_Low': 0.03113, 'ET_High': 0.08378, 'AC_Low': 32.7731, 'AC_High': 77.0708}\
}

#------------------------------------------------------------------
#			Prep Data
#------------------------------------------------------------------
allData = pd.read_csv(inTable)

# Drop Paradise
allData = allData[allData['NAME'] != 'Paradise, CA']

# Canopy Acreage and Percentage
allData['PolyArea_M2'] = allData['PolyArea_Acres'].divide(0.000247105)
allData['canopyAcres'] = allData['PolyArea_Acres'].multiply(allData['canopyPercent'])
allData['potentialCanopyAcres'] = allData['canopyAcres'].add(allData['PotAreaAcr'])
allData['potentialCanopyPercent'] = allData['potentialCanopyAcres'].divide(allData['PolyArea_Acres'])

# Population Density
allData['PopDensKm2'] = allData['Population'].divide(allData['PolyArea_M2'].divide(1000**2))

# UHI Calculations
allData['uhiSummer'] = allData['Urban_LSTsummer'].subtract(allData['Rural_LSTsummer'])
allData['uhiWinter'] = allData['Urban_LSTwinter'].subtract(allData['Rural_LSTwinter'])
allData['uhi'] = allData['Urban_LST'].subtract(allData['Rural_LST'])

# UHI Standard Deviation
allData['uhiSummerStd'] = ((allData['Urban_LSTsummerstd']**2).add(allData['Rural_LSTsummerstd']**2))**(0.5)
allData['uhiWinterStd'] = ((allData['Urban_LSTwinterstd']**2).add(allData['Rural_LSTwinterstd']**2))**(0.5)
allData['uhiStd'] = ((allData['Urban_LSTstd']**2).add(allData['Rural_LSTstd']**2))**(0.5)

# Set ET and AC Penetration Numbers
for rate in ['ET_Low','ET_High','AC_Low','AC_High']:
	allData[rate] = 0
for climateZoneStr in et_and_ac_numbers.keys():
	climateZoneNum = int(climateZoneStr)
	allData.loc[allData['Climate_Zone_State'] == climateZoneNum, 'ET_Low'] = et_and_ac_numbers[climateZoneStr]['ET_Low']
	allData.loc[allData['Climate_Zone_State'] == climateZoneNum, 'ET_High'] = et_and_ac_numbers[climateZoneStr]['ET_High']
	allData.loc[allData['Climate_Zone_State'] == climateZoneNum, 'AC_Low'] = et_and_ac_numbers[climateZoneStr]['AC_Low']
	allData.loc[allData['Climate_Zone_State'] == climateZoneNum, 'AC_High'] = et_and_ac_numbers[climateZoneStr]['AC_High']

#------------------------------------------------------------------
#			Get List of Cities to Run
#------------------------------------------------------------------
# Get list of cities to run
valCounts = allData.NAME.value_counts()
allCities = valCounts.keys()

#------------------------------------------------------------------
#			Add Columns to Output DataFrame
#------------------------------------------------------------------
#--------Quartile Variables--------------
quartileVars = ['Income_Quartile', 'group4_UHI_median', 'group4_canopyPercent_median',  'group3_UHI_median', 'group3_canopyPercent_median',
		'group2_UHI_median', 'group2_canopyPercent_median','group1_UHI_median', 'group1_canopyPercent_median',
		'TGTree_Per','TGTree_Acr','Population_Quartile','Ratio_Pop_Inc']
for groupStatsName in quartileVars:
	allData[groupStatsName] = np.nan

#--------Variables From Regression--------------
regressionVars = ['UHI_Modeled','Modeled_MinPotUHI',  'r2', 'regression_num', 'regression_group', 'regression_canopy_slope',
		'SlopeConf95Low', 'SlopeConf95High', 'targetCanopyPercent_regr', 'Modeled_TGPotUHI']
for groupStatsName in regressionVars:
	allData[groupStatsName] = np.nan

#--------Variables From Suitability Stats & Calculation--------------
suitabilityVars = ['UHIGap','rankIncome','rankUHI', 'rankPopDensity', 'rankPopulation', 'Ratio_Ranked_Pop_Inc', 
	'targetCanopyAcres', 'TGUhi_Acre', 'TGUhi_Perc','RatCANTree', 'RatCANUhi', 
	'TGTree_Acre_Lim','TGUhi_Acre_Lim','TGTree_Per_Lim','TGUhi_Per_Lim',
	'TGDiffUHI','MinDiffUHI','TGPotUHI','MinPotUHI','TGDiffUHI_Lim','TGPotUHI_Lim','UGDiffUHI_Lim','UGPotUHI_Lim',
	'A1', 'A1_ranked', 'A1_quartile','A2', 'A2_ranked','A2_quartile', 'mTC_Acres','Pot_kW_Low','Pot_kW_High']
for groupStatsName in suitabilityVars:
	allData[groupStatsName] = np.nan

#------------------------------------------------------------------
#		Loop Through Each City and Calculate City-Specific Stats and Regression
#------------------------------------------------------------------
if not os.path.isdir(tableDir):
	os.mkdir(tableDir)
if not os.path.isdir(figureDir):
	os.mkdir(figureDir)

for city in allCities:
	print(city)
	cityName = city.split(',')[0]\
			  .replace(' ', '')\
	          .replace(')','')\
	          .replace('(','')\
	          .replace('.','')
	groupData = allData[allData.NAME == city].copy()

	#-----------Get Stats By Income Quartile-------- 
	if len(groupData) >= minObs_cityStats:
		quartileStats = urbanTreeLib.calcQuartileStats(groupData, quartileVars)
		groupData.update(quartileStats)
		allData.update(quartileStats)

	#-----------Run Regression--------
	if len(groupData) >= minObs_regression:
		allData = urbanTreeLib.runRegression(allData, groupData, cityName, regressionVars, figureDir)

	#-----------Add Suitability and Income Stats, do any needed masking--------
	if len(groupData) >= minObs_cityStats:
		groupData = allData[allData.NAME == city].copy() # get data again, including the new UHI variables
		groupStats = urbanTreeLib.suitabilityStats(groupData, suitabilityVars) 
		allData.update(groupStats)


#for col in allData.columns: print(col, len(allData[allData[col].isnull()]))

#------------------------------------------------------------------
#			Finalize dataset
#------------------------------------------------------------------
# Rename Certain Variables:
exportData = allData.rename(columns = {'Climate_Zone_State': 'ClimateZone',
									 'Climate_Zone_McPherson': 'ClimZ_McPh',
									 'PolyArea_Acres': 'Area_Acres',
									 'canopyAcres': 'cTC_Acres',
									 'canopyPercent': 'cTC_Percent',
									 'uhiSummer': 'UHI_Current',
									 'group4_UHI_median': 'HiInco_UHI',
									 'group4_canopyPercent_median': 'HiInco_Can',
									 'group1_UHI_median': 'LoInco_UHI',
									 'group1_canopyPercent_median': 'LoInco_Can',
									 'regression_num': 'Regr_num',
									 'r2': 'Regr_r2',
									 'regression_canopy_slope': 'Regr_slope',
									 'NAME': 'City_Name',
									 'Income_Quartile': 'IncomeQuartile',
									 'Population_Quartile': 'PopQuartile'})

# Variables to Export:
columns = sorted(['Regr_num','Regr_r2', 'Regr_slope','SlopeConf95Low', 'SlopeConf95High', 
	'ClimateZone', 'ClimZ_McPh', 'Income', 'IncomeQuartile',
	'Households','PopDensKm2', 'Population','PopQuartile','Ratio_Pop_Inc','Ratio_Ranked_Pop_Inc',
	'Area_Acres', 'cTC_Acres', 'cTC_Percent', 
	'PotAreaAcr', 'HiInco_Can','LoInco_Can','TGTree_Acr','TGTree_Per','RatCANTree','TGUhi_Acre','TGUhi_Perc','RatCANUhi',
	'TGTree_Acre_Lim','TGUhi_Acre_Lim',
	'HiInco_UHI','LoInco_UHI','UHIGap','mTC_Acres',
	'UHI_Current','UHI_Modeled',
	'Modeled_TGPotUHI', 'Modeled_MinPotUHI', 
	'TGDiffUHI','MinDiffUHI','TGPotUHI','MinPotUHI',
	'TGDiffUHI_Lim','TGPotUHI_Lim','UGDiffUHI_Lim','UGPotUHI_Lim',
	'A1','A2','A1_ranked','A2_ranked','A1_quartile','A2_quartile',
	'Pot_kW_Low', 'Pot_kW_High'])
columns.insert(0, 'City_Name')
columns.insert(0, 'geoid')
columns.append('.geo')

# Multiply Percent Variables by 100
exportData[['TGTree_Per','TGUhi_Perc','cTC_Percent','HiInco_Can','LoInco_Can']] = exportData[['TGTree_Per','TGUhi_Perc','cTC_Percent','HiInco_Can','LoInco_Can']].multiply(100)

# Set nans to zero
exportData = exportData.fillna(0)

#------------------------------------------------------------------
#			Export
#------------------------------------------------------------------

exportData = exportData.reindex(columns, axis = 1)

exportData.to_csv(outTable_forGEE, index=False, float_format='%.3f')
exportData.drop(columns='.geo').to_csv(outTable, index=False, float_format='%.2f')















