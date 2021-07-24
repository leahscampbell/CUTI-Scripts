#---------------------------------------------------------------
#				02_Aggregate_Data_Table.py
#---------------------------------------------------------------

import os
import pandas as pd 
import pdb

# Root paths
inDataDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v9_Input_Data'
outTableDir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v9_Output_Tables'

# Output Tables
outTable = os.path.join(outTableDir, 'CBG_Table_v9.csv')
outTable_forGEE = os.path.join(outTableDir, 'CBG_Table_v9_forGEE.csv')

# Data Tables
lstDissTable = os.path.join(inDataDir, 'CalUHI_diss_vf_All.csv') # Rural LSTs
lstCBGTable = os.path.join(inDataDir, 'CalUHI_cb_vf_All.csv') # Urban LSTs
canopyTableDir = os.path.join(inDataDir, 'Canopy_Percent_Tables') # Canopy Percentages
distanceTable = os.path.join(inDataDir, 'Distances_CBG_Table_All.csv')# Distance from Coast and Centroid of City
nlcdTable = os.path.join(inDataDir, 'NLCD_Percent_CBG_Table_All.csv')
incPopTable = os.path.join(inDataDir, 'Income_Population_CBG_Table_All.csv')
potentialAreaTable = os.path.join(inDataDir, 'Potential_Area_CBG_Table_All.csv')
climateZoneTable = os.path.join(inDataDir, 'Climate_Zones_CBG_Table_All.csv')
clippedGeometryDir = os.path.join(inDataDir, 'Clipped_Geometries')

#---------------------------------------------------------------
#				Read in Tables
#---------------------------------------------------------------
print('UHI Tables')
lstDiss = pd.read_csv(lstDissTable)
lstCBG = pd.read_csv(lstCBGTable)
print(lstCBG['NAME'].nunique(), ' Cities')

print('Canopy Percent')
canopyPercent = pd.concat([pd.read_csv(os.path.join(canopyTableDir, file)) for file in os.listdir(canopyTableDir)])
print(canopyPercent['NAME'].nunique(), ' Cities')

print('Distances')
distance = pd.read_csv(distanceTable)
print(distance['NAME'].nunique(), ' Cities')

print('NLCD')
nlcd = pd.read_csv(nlcdTable)
print(nlcd ['NAME'].nunique(), ' Cities')

print('Potential Area')
potArea = pd.read_csv(potentialAreaTable)
print(potArea['NAME'].nunique(), ' Cities')

print('Income & Population')
incPop = pd.read_csv(incPopTable)
print('No City Names in Dataset')

print('Climate Zones')
climateZones = pd.read_csv(climateZoneTable)
print(climateZones['NAME'].nunique(), ' Cities')

print('Clipped Geometries')
clippedGeometries = pd.concat([pd.read_csv(os.path.join(clippedGeometryDir, file)) for file in os.listdir(clippedGeometryDir)])
#print(clippedGeometries['NAME'].nunique(), ' Cities')

#---------------------------------------------------------------
#				Prep Data and Merge As We Go
#---------------------------------------------------------------

# Prep CBG LST table
lstCBG = lstCBG.loc[:,~lstCBG.columns.str.startswith('b')].drop(columns=['system:index','.geo']).drop_duplicates()
lstCBG = lstCBG[lstCBG.Urban_LST.notnull()] # Drop any CBGs with no Urban LST data
lstCBG = lstCBG.fillna(0) 

# Prep Rural LST table
lstDiss = lstDiss.loc[:,lstDiss.columns.str.contains('Rural.*|NAME10')].rename(columns={'NAME10':'NAME'})
lstDiss = lstDiss[lstDiss.Rural_LST.notnull()] # Drop any CBGs with no Rural LST data

# Merge Urban and Rural tables to create main data table
data = lstCBG.merge(lstDiss, how='inner', on='NAME', copy=False).drop(columns = ['countyfp','funcstat','geoid_data','intptlat','intptlon','mtfcc','namelsad','statefp','tractce'])
print('Create Table with LST Data: ', len(data))

# Add Canopy Percent to main data table
canopyPercent = canopyPercent.drop(columns=['system:index']).drop_duplicates()[canopyPercent.Canopy_Percent.notnull()].rename(columns = {'Canopy_Percent': 'canopyPercent'})
data = canopyPercent[['canopyPercent','geoid']].merge(data, how='inner', on='geoid', copy=False)
print('Add Canopy Percent: ', len(data))

# Add Distances to main data table
distance = distance.drop(columns=['system:index']).drop_duplicates()[distance.Dist_coast.notnull()]
data = distance[['Dist_coast','Dist_urbCenter','geoid']].merge(data, how='inner', on='geoid', copy=False)
print('Add Distances: ', len(data))

# Add NLCD
nlcd = nlcd.drop(columns=['system:index']).drop_duplicates()[nlcd.NLCD_Dev_HighIntensity_Perc.notnull()]
data = data.merge(nlcd.loc[:,nlcd.columns.str.contains('geoid|NLCD.*')], how='inner', on='geoid', copy=False, sort=True)
print('Add NLCD: ', len(data))

# Add Potential Area ** and add .geo column here!! **
potArea = potArea.drop(columns=['system:index']).drop_duplicates()[potArea.PotentialArea_Acres.notnull()]\
	.rename(columns={'PotentialArea_Acres':'PotAreaAcr'})
data = data.merge(potArea[['PotAreaAcr', 'geoid']], how='inner', on='geoid', copy=False, sort=True)
print('Add Potential Area: ', len(data))

# Add Climate Zone
climateZones = climateZones.fillna(0).astype({'Climate_Zone_State': 'int', 'Climate_Zone_DOE': 'int', 'Climate_Zone_Ecoregion': 'int', 'Climate_Zone_McPherson': 'int'})
data = data.merge(climateZones[['Climate_Zone_State', 'Climate_Zone_DOE', 'Climate_Zone_Ecoregion', 'Climate_Zone_McPherson', 'geoid']], how='inner', on='geoid', copy=False)
print('Add Climate Zones: ', len(data))

# Add Income & Population
incPop = incPop[['geoid','Population','Income','Households']].drop_duplicates()
data = data.merge(incPop, how='inner', on='geoid', copy=False, sort=True)
print('Add Income & Population: ', len(data))

data = data[data.Income.notnull()]
print('Drop Blocks with No Income Data: ', len(data))

# Drop Block Groups with Population = 0
data = data[data['Population'] != 0]
print('Drop Blocks with No Population: ', len(data))

# Clipped Geometries
#geos = clippedGeometries.drop(columns =['system:index','NAME'])
data = data.merge(clippedGeometries[['geoid','PolyArea_Acres','.geo']], how='inner', on='geoid', copy=False, sort=True)
print('Add Clipped Geometries and Drop CBGs that Dont Meet Size Requirements: ', len(data))
print('Cities: ', data['NAME'].nunique())
print(data.columns)

#---------------------------------------------------------------
#				Save Geometries
#---------------------------------------------------------------
if not os.path.isdir(outTableDir):
	os.mkdir(outTableDir)

data.fillna(0).to_csv(outTable_forGEE, index = False)
data.drop(columns = ['.geo']).to_csv(outTable, index = False)























