#---------------------------------------------------------------
#				04_City_Summaries.py
#---------------------------------------------------------------
# Create summaries using variables from the regression_and_suitability_table
import os, pdb
import pandas as pd 
import numpy as np 
import math


inDataDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v8_Input_Data'
tigerGeo = os.path.join(inDataDir, 'Tiger_Geo.csv')

tableDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v10_Output_Tables'
filename = os.path.join(tableDir, 'Suitability_Table_CBG_v10_limit.csv')
savefile = os.path.join(tableDir, 'Suitability_Summaries_City_v10_limit.csv')
savefile_forGEE = os.path.join(tableDir, 'Suitability_Summaries_City_v10_limit_forGEE.csv')

#---------------------------------------------------
#				Prep Data Table
#---------------------------------------------------
tiger = pd.read_csv(tigerGeo)

table = pd.read_csv(filename)

#---------------------------------------------------
#				Create Summary Table
#---------------------------------------------------
groups = table['City_Name'].value_counts()
groups.index.name = 'City_Name'
outTable = pd.DataFrame(columns = ['n', 
	'AcresNeeded_to_HighIncomeUHI', 'AcresNeeded_to_HighIncomeCanopyPercent', 'PercentNeeded_to_HighIncomeCanopyPercent',
	'AcresNeeded_to_HighIncomeUHI_Lim', 'AcresNeeded_to_HighIncomeCanopyPercent_Lim',
	'HiInco_CanAcres', 'HiInco_CanopyPercent', 'LoInco_CanAcres', 'LoInco_CanopyPercent',
	'HiLo_TreeGap_Perc', 'HiLo_TreeGap_Acres', 
	'Potential_Acres','Total_Area_Acres', 
	'Potential_Acres_vs_AcresNeeded_to_HighIncomeUHI','Potential_Acres_vs_AcresNeeded_to_HighIncomeCanopyPercent', 
	'Total_CanopyAcres', 'Total_CanopyPercent', 
	'Current_Avg_UHI', 'Current_Std_UHI',
	'Modeled_Avg_UHI', 'Modeled_Std_UHI',
	'MinPot_Avg_UHI', 'MinPot_Std_UHI',
	'TGPot_Avg_UHI', 'TGPot_Std_UHI',
	'MinDiff_Avg_UHI', 'MinDiff_Std_UHI',
	'TGDiff_Avg_UHI', 'TGDiff_Std_UHI',
	'UGPot_Avg_UHI_Lim', 'UGPot_Std_UHI_Lim',
	'TGPot_Avg_UHI_Lim', 'TGPot_Std_UHI_Lim',
	'UGDiff_Avg_UHI_Lim', 'UGDiff_Std_UHI_Lim',
	'TGDiff_Avg_UHI_Lim', 'TGDiff_Std_UHI_Lim',
	'HiInco_UHI', 'LoInco_UHI', 'HiLo_UHIGap',
	'Regr_r2', 'Regr_slope','SlopeConf95Low', 'SlopeConf95High',
	'Income_Quartile_1_MaxVal','Income_Quartile_2_MaxVal','Income_Quartile_3_MaxVal',
	'Income_Quartile_1_Population', 'Income_Quartile_2_Population', 'Income_Quartile_3_Population', 'Income_Quartile_4_Population','Total_Population',
	'Pot_kW_Low', 'Pot_kW_High'], 
	index = groups.index)

for group in groups.index:
	
	groupTable = table[table['City_Name'] == group].copy()

	groupTable.loc[groupTable['TGUhi_Acre'].lt(0), 'TGUhi_Acre'] = 0
	groupTable.loc[groupTable['TGTree_Acr'].lt(0), 'TGTree_Acr'] = 0
	groupTable.loc[groupTable['TGUhi_Acre_Lim'].lt(0), 'TGUhi_Acre_Lim'] = 0
	groupTable.loc[groupTable['TGTree_Acre_Lim'].lt(0), 'TGTree_Acre_Lim'] = 0
	groupTable.loc[groupTable['Pot_kW_Low'].lt(0), 'Pot_kW_Low'] = 0
	groupTable.loc[groupTable['Pot_kW_High'].lt(0), 'Pot_kW_High'] = 0
	# Mask out CBGs with more tree canopy than high income canopy to start with - this is done in 03_Run_Regression_and_Suitability.py
	#groupTable.loc[(groupTable['cTC_Percent'] - groupTable['HiInco_Can']).gt(0), 'TGDiffUHI'] = 0
	#groupTable.loc[(groupTable['cTC_Percent'] - groupTable['HiInco_Can']).gt(0), 'TGPotUHI'] = groupTable[(groupTable['cTC_Percent'] - groupTable['HiInco_Can']).gt(0), 'UHI_Current']
	
	outTable.loc[group, 'Potential_Acres'] = groupTable['PotAreaAcr'].sum()
	outTable.loc[group, 'Total_Area_Acres'] = groupTable['Area_Acres'].sum()
	outTable.loc[group, 'AcresNeeded_to_HighIncomeUHI'] = groupTable['TGUhi_Acre'].sum()
	outTable.loc[group, 'AcresNeeded_to_HighIncomeCanopyPercent'] = groupTable['TGTree_Acr'].sum()
	outTable.loc[group, 'AcresNeeded_to_HighIncomeUHI_Lim'] = groupTable['TGUhi_Acre_Lim'].sum()
	outTable.loc[group, 'AcresNeeded_to_HighIncomeCanopyPercent_Lim'] = groupTable['TGTree_Acre_Lim'].sum()
	outTable.loc[group, 'PercentNeeded_to_HighIncomeCanopyPercent'] = outTable.loc[group, 'AcresNeeded_to_HighIncomeCanopyPercent'] / outTable.loc[group, 'Total_Area_Acres'] * 100	
	outTable.loc[group, 'Potential_Acres_vs_AcresNeeded_to_HighIncomeUHI'] = np.min([outTable.loc[group, 'AcresNeeded_to_HighIncomeUHI'], outTable.loc[group, 'Potential_Acres']])
	outTable.loc[group, 'Potential_Acres_vs_AcresNeeded_to_HighIncomeCanopyPercent'] = np.min([outTable.loc[group, 'AcresNeeded_to_HighIncomeCanopyPercent'], outTable.loc[group, 'Potential_Acres']])
	outTable.loc[group, 'Total_CanopyAcres'] = groupTable['cTC_Acres'].sum()
	outTable.loc[group, 'Total_CanopyPercent'] = outTable.loc[group, 'Total_CanopyAcres'] / outTable.loc[group, 'Total_Area_Acres'] * 100

	# High and Low Income Canopy Cover
	groupTable['HiInco_CanAcres'] = groupTable['HiInco_Can'].divide(100).multiply(groupTable['Area_Acres'])
	outTable.loc[group, 'HiInco_CanAcres'] = groupTable['HiInco_CanAcres'].sum()
	outTable.loc[group, 'HiInco_CanopyPercent'] = groupTable['HiInco_Can'].iloc[0]
	groupTable['LoInco_CanAcres'] = groupTable['LoInco_Can'].divide(100).multiply(groupTable['Area_Acres'])
	outTable.loc[group, 'LoInco_CanAcres'] = groupTable['LoInco_CanAcres'].sum()
	outTable.loc[group, 'LoInco_CanopyPercent'] = groupTable['LoInco_Can'].iloc[0]#= outTable.loc[group, 'LoInco_CanAcres'] / outTable.loc[group, 'Total_Area_Acres'] * 100

	# Tree Gap - Between High and Low Income and the average of all the individual Tree Gaps.
	outTable.loc[group, 'HiLo_TreeGap_Perc'] = outTable.loc[group, 'HiInco_CanopyPercent'] - outTable.loc[group, 'LoInco_CanopyPercent']
	outTable.loc[group, 'HiLo_TreeGap_Acres'] = outTable.loc[group, 'HiInco_CanAcres'] - outTable.loc[group, 'LoInco_CanAcres']

	# Weighted UHI Averages:
	outTable.loc[group, 'Modeled_Avg_UHI'] = np.average(groupTable['UHI_Modeled'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'Current_Avg_UHI'] = np.average(groupTable['UHI_Current'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'MinPot_Avg_UHI'] = np.average(groupTable['MinPotUHI'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'TGPot_Avg_UHI'] = np.average(groupTable['TGPotUHI'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'MinDiff_Avg_UHI'] = np.average(groupTable['MinDiffUHI'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'TGDiff_Avg_UHI'] = np.average(groupTable['TGDiffUHI'], weights = groupTable['Area_Acres'])

	# Limited Scenario Weighted UHI Averages
	outTable.loc[group, 'UGPot_Avg_UHI_Lim'] = np.average(groupTable['UGPotUHI_Lim'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'TGPot_Avg_UHI_Lim'] = np.average(groupTable['TGPotUHI_Lim'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'UGDiff_Avg_UHI_Lim'] = np.average(groupTable['UGDiffUHI_Lim'], weights = groupTable['Area_Acres'])
	outTable.loc[group, 'TGDiff_Avg_UHI_Lim'] = np.average(groupTable['TGDiffUHI_Lim'], weights = groupTable['Area_Acres'])
	#outTable.loc[group, 'Potential_Avg_UHI'] = np.average(groupTable['MinPotUHI'], weights = groupTable['Area_Acres'])
	# groupTable['Modeled_Minus_Potential_UHI'] = groupTable['UHI_Modeled'].subtract(groupTable['MinPotUHI'])
	# outTable.loc[group, 'Modeled_Minus_Potential_UHI'] = np.average(groupTable['Modeled_Minus_Potential_UHI'], weights = groupTable['Area_Acres'])
	
	# Weighted UHI Standard Deviation
	# From https://stackoverflow.com/questions/2413522/weighted-standard-deviation-in-numpy:
	outTable.loc[group, 'Modeled_Std_UHI'] = math.sqrt(np.average((groupTable['UHI_Modeled']-outTable.loc[group, 'Modeled_Avg_UHI'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'Current_Std_UHI'] = math.sqrt(np.average((groupTable['UHI_Current']-outTable.loc[group, 'Current_Avg_UHI'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'MinPot_Std_UHI'] = math.sqrt(np.average((groupTable['MinPotUHI']-outTable.loc[group, 'MinPot_Avg_UHI'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'TGPot_Std_UHI'] = math.sqrt(np.average((groupTable['TGPotUHI']-outTable.loc[group, 'TGPot_Avg_UHI'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'MinDiff_Std_UHI'] = math.sqrt(np.average((groupTable['MinDiffUHI']-outTable.loc[group, 'MinDiff_Avg_UHI'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'TGDiff_Std_UHI'] = math.sqrt(np.average((groupTable['TGDiffUHI']-outTable.loc[group, 'TGDiff_Avg_UHI'])**2, weights = groupTable['Area_Acres']))

	# Limited Scenario - Weighted UHI Standard Deviation
	outTable.loc[group, 'UGPot_Std_UHI_Lim'] = math.sqrt(np.average((groupTable['UGPotUHI_Lim']-outTable.loc[group, 'UGPot_Avg_UHI_Lim'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'TGPot_Std_UHI_Lim'] = math.sqrt(np.average((groupTable['TGPotUHI_Lim']-outTable.loc[group, 'TGPot_Avg_UHI_Lim'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'UGDiff_Std_UHI_Lim'] = math.sqrt(np.average((groupTable['UGDiffUHI_Lim']-outTable.loc[group, 'UGDiff_Avg_UHI_Lim'])**2, weights = groupTable['Area_Acres']))
	outTable.loc[group, 'TGDiff_Std_UHI_Lim'] = math.sqrt(np.average((groupTable['TGDiffUHI_Lim']-outTable.loc[group, 'TGDiff_Avg_UHI_Lim'])**2, weights = groupTable['Area_Acres']))

	# High and Low Income UHI
	outTable.loc[group, 'HiInco_UHI'] = groupTable['HiInco_UHI'].iloc[0]
	outTable.loc[group, 'LoInco_UHI'] = groupTable['LoInco_UHI'].iloc[0]
	outTable.loc[group, 'HiLo_UHIGap'] = outTable.loc[group, 'LoInco_UHI'] - outTable.loc[group, 'HiInco_UHI']

	outTable.loc[group, 'n'] = groups.loc[group]
	outTable.loc[group, 'Total_Population'] = groupTable['Population'].sum()

	# Income quartiles. Recalculate since smaller cities were lumped with Climate Zones for regression calculations
	incomeQuartiles = groupTable['Income'].quantile(q=[0.25,0.5,0.75]).to_numpy()
	outTable.loc[group, 'Income_Quartile_1_MaxVal'] = incomeQuartiles[0]
	outTable.loc[group, 'Income_Quartile_2_MaxVal'] = incomeQuartiles[1]
	outTable.loc[group, 'Income_Quartile_3_MaxVal'] = incomeQuartiles[2]
	outTable.loc[group, 'Income_Quartile_1_Population'] = groupTable[groupTable['IncomeQuartile'] == 1]['Population'].sum()
	outTable.loc[group, 'Income_Quartile_2_Population'] = groupTable[groupTable['IncomeQuartile'] == 2]['Population'].sum()
	outTable.loc[group, 'Income_Quartile_3_Population'] = groupTable[groupTable['IncomeQuartile'] == 3]['Population'].sum()
	outTable.loc[group, 'Income_Quartile_4_Population'] = groupTable[groupTable['IncomeQuartile'] == 4]['Population'].sum()

	# Regression Stats
	outTable.loc[group, 'Regr_r2'] = groupTable['Regr_r2'].iloc[0]	
	outTable.loc[group, 'Regr_slope'] = groupTable['Regr_slope'].iloc[0]
	outTable.loc[group, 'SlopeConf95Low'] = groupTable['SlopeConf95Low'].iloc[0]
	outTable.loc[group, 'SlopeConf95High'] = groupTable['SlopeConf95High'].iloc[0]
	
	# Calculate energy savings
	outTable.loc[group, 'Pot_kW_Low'] = groupTable['Pot_kW_Low'].sum()
	outTable.loc[group, 'Pot_kW_High'] = groupTable['Pot_kW_High'].sum()


outTable.to_csv(savefile)

tiger = tiger[['NAME10','.geo']].rename(columns = {'NAME10': 'City_Name'})
outTable = outTable.merge(tiger, how='inner', on='City_Name', copy=False)
outTable.to_csv(savefile_forGEE, index=False)