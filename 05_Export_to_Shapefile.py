#---------------------------------------------------------------
#				05_Export_to_Shapefile.py
#---------------------------------------------------------------
# ** This must be done AFTER uploading the CSV tables to GEE (which is done manually). 
# This just exports from asset to shapefile. **

import ee, pdb
ee.Initialize()
from geeViz import taskManagerLib

cbgName = 'Suitability_Table_CBG_v10'
cityName = 'Suitability_Summaries_byCity_v10'
suitabilityTableCBG_Asset = 'users/leahscampbell/contour/tnc/urbantree/'+cbgName
suitabilityTableCity_Asset = 'users/leahscampbell/contour/tnc/urbantree/'+cityName

#----------------------------------------------
# CBG Table: Rename needed variables and export to shapefile
#-----------------------------------------------
assetTable = ee.FeatureCollection(suitabilityTableCBG_Asset)
origPropNames = ee.List(sorted([\
	'Income', 
	'A1', 
	'A2', 
	'HiInco_Can', 
	'TGUhi_Acre', 
	'Regr_r2', 
	'Area_Acres', 
	'mTC_Acres', 
	'A2_quartile', 
	'Pot_kW_High', 
	'A1_ranked', 
	'Ratio_Pop_Inc', 
	'ClimZ_McPh', 
	'City_Name', 
	'PotAreaAcr', 
	'Pot_kW_Low', 
	'RatCANUhi', 
	'UHI_Modeled', 
	'cTC_Percent', 
	'LoInco_UHI', 
	'UHI_Current', 
	'UHIGap', 
	'MinPotUHI', 
	'IncomeQuartile', 
	'cTC_Acres', 
	'LoInco_Can', 
	'MinDiffUHI', 
	'RatCANTree', 
	'Population', 
	'PopDensKm2', 
	'ClimateZone', 
	'Regr_slope', 
	'A2_ranked', 
	'Households', 
	'TGPotUHI', 
	'Regr_num', 
	'PopQuartile', 
	'TGUhi_Perc', 
	'TGTree_Acr', 
	'geoid', 
	'A1_quartile', 
	'TGDiffUHI', 
	'HiInco_UHI', 
	'TGTree_Per',
  ]))
  
newPropNames = origPropNames.replace('Ratio_Pop_Inc','RatioPopInc')
assetTable = assetTable.select(origPropNames, newPropNames)

print('Exporting CBG Table')
t = ee.batch.Export.table.toDrive(**{\
    'collection': assetTable, 
    'description': 'Suitability_Table_toDrive_shp', 
    'folder': 'Canopy_Regression_Tables', 
    'fileNamePrefix': cbgName, 
    'fileFormat': 'SHP',
    'selectors': newPropNames.getInfo()})
t.start()

#----------------------------------------------
# City Table: Rename needed variables and export to shapefile
#-----------------------------------------------
citySummaries = ee.FeatureCollection(suitabilityTableCity_Asset)
print(citySummaries.first().propertyNames().getInfo())
allNames = citySummaries.first().propertyNames().getInfo()
# --------Set negative Diff_UHI to 0 and Update Potential_UHI with that number---------
def updateVals(city):
  diff_UHI = city.getNumber('MinDiff_Avg_UHI')
  current_UHI = city.getNumber('Current_Avg_UHI')
  pot_UHI = city.getNumber('MinPot_Avg_UHI')
  newDiffUHI = ee.Number(ee.Algorithms.If(\
    ee.Number(diff_UHI).lt(0),
    0,
    diff_UHI))
  newPotUHI = ee.Number(ee.Algorithms.If(\
    ee.Number(diff_UHI).lt(0),
    current_UHI,
    pot_UHI))
  
  city = city.set('MinPot_Avg_UHI', newPotUHI).set('MinDiff_Avg_UHI', newDiffUHI)
  
  diff_UHI = city.getNumber('TGDiff_Avg_UHI')
  pot_UHI = city.getNumber('TGPot_Avg_UHI')
  newDiffUHI = ee.Number(ee.Algorithms.If(\
    ee.Number(diff_UHI).lt(0),
    0,
    diff_UHI))
  newPotUHI = ee.Number(ee.Algorithms.If(\
    ee.Number(diff_UHI).lt(0),
    current_UHI,
    pot_UHI))
  
  city = city.set('TGPot_Avg_UHI', newPotUHI).set('TGDiff_Avg_UHI', newDiffUHI)
  return city
citySummaries = citySummaries.map(lambda city: updateVals(city))

# ----------- Rename -----------------
shapefileNames = {\
  'City_Name': 'City_Name', 
  'n': 'n', 
  'AcresNeeded_to_HighIncomeUHI': 'UHIGapAcres',
  'AcresNeeded_to_HighIncomeCanopyPercent': 'TreeGapAcres', 
  'Potential_Acres': 'PotAcres',
  'Total_Area_Acres': 'TotAreaAcres', 
  'Total_CanopyPercent': 'CanopyPercent', 
  'Total_Population': 'TotPopulation',
  'Current_Avg_UHI': 'CurrentUHI',
  'Modeled_Avg_UHI': 'ModeledUHI', 
  'MinPot_Avg_UHI':'MinPotUHI',
  'TGPot_Avg_UHI': 'TGPotUHI',
  'MinDiff_Avg_UHI': 'MinDiffUHI',
  'TGDiff_Avg_UHI': 'TGDiffUHI',
  'Current_Std_UHI': 'StdCurrentUHI',
  'Modeled_Std_UHI': 'StdModeledUHI', 
  'MinPot_Std_UHI':'StdMinPotUHI',
  'TGPot_Std_UHI': 'StdTGPotUHI',
  'MinDiff_Std_UHI': 'StdMinDiffUHI',
  'TGDiff_Std_UHI': 'StdTGDiffUHI',
  'SlopeConf95Low': 'SlpCon95Low',
  'SlopeConf95High': 'SlpCon95High',
  'Pot_kW_Low': 'Pot_kW_Low',
  'Pot_kW_High': 'Pot_kW_High',
  'LoInco_CanopyPercent': 'LoInco_Can', 
  'HiLo_UHIGap': 'HiLoUHIGap', 
  'Regr_r2': 'Regr_r2', 
  'HiLo_TreeGap_Perc': 'HiLoTreeGap', 
  'HiInco_CanopyPercent': 'HiInco_Can', 
  'Regr_slope': 'Regr_slope', 
  'Total_CanopyAcres': 'TotCanAcres', 
  'HiInco_UHI': 'HiInco_UHI', 
  'LoInco_UHI': 'LoInco_UHI'}
origPropertyNames = list(shapefileNames.keys())
newPropertyNames = [shapefileNames[key] for key in origPropertyNames]

citySummaries = citySummaries.select(origPropertyNames, newPropertyNames)

# -----------Export-----------------
print('Exporting City Table')

t = ee.batch.Export.table.toDrive(**{\
    'collection': citySummaries, 
    'description': 'Suitability_Summaries_toDrive_shp', 
    'folder': 'UrbanTree_Suitability_Summaries', 
    'fileNamePrefix': cityName, 
    'fileFormat': 'SHP'})
t.start()

taskManagerLib.trackTasks()


















