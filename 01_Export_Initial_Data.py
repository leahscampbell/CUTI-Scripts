import ee, pdb, os
ee.Initialize()
from geeViz import taskManagerLib

#-----------------------------------------------------
#			Options
#-----------------------------------------------------
export_distances = False
export_nlcd = False
export_potential_area = False
export_climate_zones = False
export_income_population = False
export_canopy_cover = False
export_canopy_area = False
export_geos = True
#-----------------------------------------------------
#			Initial Datasets
#-----------------------------------------------------
# Bucket to export to in Cloud Storage
gcpBucket_TCC = 'urban-tree-canopy-cover'
gcpBucket = 'urban-tree'

# Tiger Urban Areas
tiger = ee.FeatureCollection('users/Shree1175/CA_UrbanReforestation/TIGER_CA_Urban_Areas')

# CBGs with UHI/LST values and City Name
# Get these from this script: https://code.earthengine.google.com/5f05c717099f6e6b564afa13b2f9c161, (Gmail from TC Feb. 25 2021)
lst_cbg = ee.FeatureCollection('users/leahscampbell/contour/tnc/urbantree/CalUHI_cb_vf_All_Feb2021')\
	.distinct(['.geo', 'geoid', 'Urban_LSTsummer']) # There are some duplicates\
cbg_tcc = lst_cbg.select(['NAME','geoid','aland','awater','Ar_pixel'])
lst_cbg = lst_cbg.select(['NAME','geoid'])

# Block Group Level - Income & Population - for all CA
incomePop = ee.FeatureCollection('users/tirthankarchakraborty/California_blockgroup_vf')\

# NLCD Land cover. Used for canopy regression and also get valid areas within CBGs
nlcd = ee.Image('USGS/NLCD/NLCD2016').select('landcover').clip(tiger)

# Earth Define Canopy cover
# Leah uploaded to ee from XX PLACE
earthdefine = ee.ImageCollection('users/leahscampbell/contour/tnc/urbantree/EarthDefine').mosaic()\
  .unmask(ee.Image(0),False).updateMask(nlcd.neq(11)).clip(tiger)

# Asset Directory for Canopy Area Assets
canopyAreaDir = 'users/leahscampbell/contour/tnc/urbantree/Canopy_Area_Tables'

# Coastlines
coast = ee.FeatureCollection("users/tirthankar25/coastline")

# Potential Area
urbanSuitability = ee.Image('users/charlotteks/urbn_suitability')

# Clipped Geometry Asset to Save To
geoAsset = 'users/leahscampbell/contour/tnc/urbantree/Clipped_Geometries_CBG'

# Size parameters for filtering clipped geometries (see more info below)
canopyDataMaskMinSize = 15000
canopyDataMask2MinSize = 200000
canopyDataMaskPortion = 0.01
canopyDataMaskRatio = 0.9
#----------------------------------------------------------
#           Initialize List of Cities
#----------------------------------------------------------
# List of cities to loop through
areaList = lst_cbg.aggregate_histogram('NAME').keys().getInfo()
areaNameStrings = []
for name in areaList:
	cleanName = name.split(',')[0]\
              .replace(' ','')\
              .replace(')','')\
              .replace('(','')\
              .replace('.','')
	areaNameStrings.append(cleanName)
areaDict = {areaList[i]: areaNameStrings[i] for i in range(len(areaList))}

#----------------------------------------------------------
#           Calculate and Export Distances
#----------------------------------------------------------
if export_distances:
	print('Export Distances')
	def add_distance(feature):
		centr = feature.geometry().centroid()
		dist_coast = ee.Number(centr.distance(coast, 5))
		urb_centr = ee.Feature(tiger.filter(ee.Filter.eq('NAME10', feature.get('NAME'))).first()).geometry().centroid()
		dist_urb = ee.Number(centr.distance(urb_centr, 5))
		return feature.set({'Dist_coast': dist_coast, 'Dist_urbCenter': dist_urb})

	cityDistances = []
	for cityName in areaList:
		print('Distances:', cityName)

		cityCBGs = lst_cbg.filter(ee.Filter.eq('NAME', cityName))

		distances = cityCBGs.map(add_distance)

		cityDistances.append(distances)

	exportDistances = ee.FeatureCollection(cityDistances).flatten()

	# Set geometries to null so that .geo column doesn't make the file huge.
	exportDistances = exportDistances.map(lambda cbg: cbg.setGeometry(None))

	t = ee.batch.Export.table.toCloudStorage(**{\
        'collection': exportDistances, 
        'description': 'Distances_Table_toStorage', 
        'bucket': gcpBucket, 
        'fileNamePrefix': 'Distances_CBG_Table_All', 
        'fileFormat': 'CSV'})
	t.start()
	# t = ee.batch.Export.table.toAsset(**{\
	#     'collection': exportDistances, 
	#     'description': 'Distances_Table_toAsset', 
	#     'assetId': ''})
	# t.start()

#----------------------------------------------------------
#           Calculate and Export NLCD Percentages
#----------------------------------------------------------
if export_nlcd:
	print('Export NLCD')

	# Add NLCD Classes & Canopy Percent
	nlcdImage = ee.Image(nlcd.eq(21)).rename('NLCD_Dev_OpenSpace_Perc')\
		.addBands(ee.Image(nlcd.eq(22)).rename('NLCD_Dev_LowIntensity_Perc'))\
		.addBands(ee.Image(nlcd.eq(23)).rename('NLCD_Dev_MedIntensity_Perc'))\
		.addBands(ee.Image(nlcd.eq(24)).rename('NLCD_Dev_HighIntensity_Perc'))\
		.addBands(ee.Image(nlcd.lt(21).Or(nlcd.gt(24))).rename('NLCD_Other_Perc'))

	exportNLCD = nlcdImage.reduceRegions(**{\
		'collection': lst_cbg,
		'reducer': ee.Reducer.mean(), 
		'scale': 30, 
		'crs': None, 
		'crsTransform': None, 
		'tileScale': 1})

	# Set geometries to null so that .geo column doesn't make the file huge.
	exportNLCD = exportNLCD.map(lambda cbg: cbg.setGeometry(None))

	t = ee.batch.Export.table.toCloudStorage(**{\
        'collection': exportNLCD, 
        'description': 'NLCD_Percent_Table_toStorage', 
        'bucket': gcpBucket, 
        'fileNamePrefix': 'NLCD_Percent_CBG_Table_All', 
        'fileFormat': 'CSV'})
	t.start()
	# t = ee.batch.Export.table.toAsset(**{\
	#     'collection': exportNLCD, 
	#     'description': 'NLCD_Percent_Table_toAsset', 
	#     'assetId': ''})
	# t.start()


#----------------------------------------------------------
#           Calculate and Export Potential Area
#----------------------------------------------------------
if export_potential_area:
	print('Export Potential Area')

	urbanSuitability = urbanSuitability.rename('PotentialArea_m2')
	urbanSuitability = urbanSuitability.addBands(urbanSuitability.multiply(0.000247105).rename('PotentialArea_Acres'))

	exportPotArea = urbanSuitability.reduceRegions(**{\
		'collection': lst_cbg,
		'reducer': ee.Reducer.sum(), 
		'scale': 30, 
		'crs': None, 
		'crsTransform': None, 
		'tileScale': 1})

	# Set geometries to null so that .geo column doesn't make the file huge.
	exportPotArea = exportPotArea.map(lambda cbg: cbg.setGeometry(None))

	t = ee.batch.Export.table.toCloudStorage(**{\
        'collection': exportPotArea, 
        'description': 'Potential_Area_Table_toStorage', 
        'bucket': gcpBucket, 
        'fileNamePrefix': 'Potential_Area_CBG_Table_All', 
        'fileFormat': 'CSV'})
	t.start()
	# t = ee.batch.Export.table.toAsset(**{\
	#     'collection': exportPotArea, 
	#     'description': 'Potential_Area_Table_toAsset', 
	#     'assetId': ''})
	# t.start()

#----------------------------------------------------------
#           Calculate and Export Climate Zones
#----------------------------------------------------------
if export_climate_zones:
	print('Export Climate Zones')

	def getClimateZoneImage(climateZone, inName, outName):
		keys = climateZone.aggregate_histogram('OBJECTID').keys()
		keyNums = keys.map(lambda id: ee.Number.parse(id))
		zones = keyNums.map(lambda id: ee.Feature(climateZone.filter(ee.Filter.eq('OBJECTID',id)).first()).get(inName))
		crosswalk = ee.Dictionary.fromLists(keys, zones);
		print('crosswalk', crosswalk.getInfo())

		czImage = climateZone.reduceToImage(**{\
			'properties': ['OBJECTID'], 
			'reducer': ee.Reducer.first()}).rename(outName)

		return czImage

	# California Building Climate Zones
	caBuilding = ee.FeatureCollection('users/leahscampbell/contour/tnc/urbantree/Building_Climate_Zones')
	caBuilding = caBuilding.map(lambda zone: zone.set('BZone', ee.Number.parse(zone.get('BZone'))))
	caBuildingImage = caBuilding.reduceToImage(**{\
		'properties': ['BZone'], 
		'reducer': ee.Reducer.first()}).rename('Climate_Zone_State')

	# McPherson Building Climate Zones
	mcPherson = ee.FeatureCollection('users/leahscampbell/contour/tnc/urbantree/Climate_Zones_McPherson')
	mcPhersonImage = getClimateZoneImage(mcPherson, 'Climate_Zo', 'Climate_Zone_McPherson')

	# DOE Building Climate Zones
	CA_State_Boundary = ee.FeatureCollection("TIGER/2018/States").filter(ee.Filter.eq('NAME', 'California'))
	DOE = ee.FeatureCollection('users/tirthankarchakraborty/Climate_Zones_DOE_Building_America_Program').filterBounds(CA_State_Boundary)
	DOEImage = getClimateZoneImage(DOE, 'BA_Climate', 'Climate_Zone_DOE')

	# McPherson Building Climate Zones
	ecoregions = ee.FeatureCollection("projects/igde-work/igde-data/ecoregion_biome_ca_2020")
	ecoregionsImage = getClimateZoneImage(ecoregions, 'region_nam', 'Climate_Zone_Ecoregion')

	# Aggregate to one image, reduce and export
	zoneImage = caBuildingImage.addBands(mcPhersonImage).addBands(DOEImage).addBands(ecoregionsImage)
	exportClimateZones = zoneImage.reduceRegions(**{\
		'collection': lst_cbg,
		'reducer': ee.Reducer.mode(), 
		'scale': 30, 
		'crs': None, 
		'crsTransform': None, 
		'tileScale': 1})

	# Set geometries to null so that .geo column doesn't make the file huge.
	exportClimateZones = exportClimateZones.map(lambda cbg: cbg.setGeometry(None))

	t = ee.batch.Export.table.toCloudStorage(**{\
        'collection': exportClimateZones, 
        'description': 'Climate_Zones_Table_toStorage', 
        'bucket': gcpBucket, 
        'fileNamePrefix': 'Climate_Zones_CBG_Table_All', 
        'fileFormat': 'CSV'})
	t.start()
	# t = ee.batch.Export.table.toAsset(**{\
	#     'collection': exportClimateZones, 
	#     'description': 'Climate_Zones_Table_toAsset', 
	#     'assetId': ''})
	# t.start()

#----------------------------------------------------------
#           Export Income, Population, and Households
#----------------------------------------------------------
if export_income_population:
	print('Export Income & Population')

	props = ['ALAND','AWATER','GEOID','House_Unit','Income','Pop']
	props_rename = ['aland','awater','geoid','Households','Income','Population']
	incomePop = incomePop.select(props, props_rename)

	# For some reason, doing this step made it drop the "Income" property...no idea why.
	#incomePop = incomePop.map(lambda cbg: cbg.setGeometry(None))

	t = ee.batch.Export.table.toCloudStorage(**{\
        'collection': incomePop, 
        'description': 'Income_Population_Table_toStorage', 
        'bucket': gcpBucket, 
        'fileNamePrefix': 'Income_Population_CBG_Table_All', 
        'fileFormat': 'CSV'})
	t.start()

#----------------------------------------------------------
#           Calculate and Export Tree Canopy Cover
#----------------------------------------------------------
# These are exported by city because they take a while...and it fails if you do too many CBGs at once.

if export_canopy_cover:
	print('Export Canopy Cover')

	# Pixel area, for use in canopy area calculation
	Im_Area=ee.Image.pixelArea().updateMask(nlcd.neq(11)).clip(tiger)

	for cityName in areaList:
		print('Canopy Cover:', cityName)
		cityPolys = cbg_tcc.filter(ee.Filter.eq('NAME', cityName))
		omit = ['060819901000', '060419901000'] # These are large CBGs that are completely water in the bay area - were making it crash.
		cityPolys = cityPolys.filter(ee.Filter.inList('geoid', omit).Not())

		if cityPolys.size().getInfo() > 0:
			cityPolys = cityPolys.map(lambda poly: poly.set('mean', -99999))

			# Add Canopy Percentage
			canopyPercent = earthdefine.reduceRegions(**{\
				'collection': cityPolys,
	            'reducer': ee.Reducer.mean(), 
	            'scale': 1, 
	            'crs': None, 
	            'crsTransform': None, 
	            'tileScale': 8})
			props = canopyPercent.first().propertyNames()
			canopyPercent = canopyPercent.select(props, props.replace('mean','Canopy_Percent'))#.replace('sum','CanopyData_Area_1m'))

			# Set geometries to null so that .geo column doesn't make the file huge.
			canopyPercent = canopyPercent.map(lambda cbg: cbg.setGeometry(None))

			# Export
			outStr = areaDict[cityName]
			t = ee.batch.Export.table.toCloudStorage(**{\
	            'collection': canopyPercent, 
	            'description': 'Canopy_Percent_'+outStr+'_Table_toStorage', 
	            'bucket': gcpBucket_TCC, 
	            'fileNamePrefix': 'Canopy_Percent_CBG_Table_'+outStr, 
	            'fileFormat': 'CSV'})
			t.start()
			# t = ee.batch.Export.table.toAsset(**{\
			#     'collection': canopyPercent, 
			#     'description': 'Canopy_Percent_'+outStr+'_Table_toAsset', 
			#     'assetId': 'users/leahscampbell/contour/tnc/urbantree/canopyPercent_Tables/Canopy_Percent_'+outStr+'_Table'})
			# t.start()

# #To batch download files from bucket:
# localdir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v9_Input_Data/Canopy_Percent_Tables'
# command = 'gsutil -m cp -r gs://'+gcpBucket_TCC+'/Canopy_Percent* "'+localdir+'/."'
# command = 'gsutil -m cp -r gs://urban-tree-canopy-cover/Canopy_Percent* "'+localdir+'/."'
# os.system(command)


# To check for failed tasks:
# tasks = ee.data.getTaskList()[0:211]
# status = [task['state'] for task in tasks]
# name = [task['description'] for task in tasks]
# for i, state in enumerate(status):
#   if state == 'FAILED':
#     print('FAILED: '+name[i])

#----------------------------------------------------------
#           Calculate and Export Canopy Data Areas
#----------------------------------------------------------
# These are exported by city because they take a while...and it fails if you do too many CBGs at once.

# In order to export Clipped Geometries, this must be exported to Asset.
# The 1m Area and 30m Area are used for this - to find very small areas within CBGs that should be eliminated.
# This is kind of a hack, but we are limited by the way GEE deals with pixels along a polygon boundary that intersects pixels.

if export_canopy_area:
	print('Export Canopy Area')

	# Pixel area, for use in canopy area calculation
	Im_Area=ee.Image.pixelArea().updateMask(nlcd.neq(11)).clip(tiger)

	for cityName in areaList:
		print('Canopy Area:', cityName)
		cityPolys = cbg_tcc.filter(ee.Filter.eq('NAME', cityName))
		omit = ['060819901000', '060419901000'] # These are large CBGs that are completely water in the bay area - were making it crash.
		cityPolys = cityPolys.filter(ee.Filter.inList('geoid', omit).Not())

		if cityPolys.size().getInfo() > 0:
			cityPolys = cityPolys.map(lambda poly: poly.set('sum', -9999))

			outStr = areaDict[cityName]

			# Add Area Covered by Earth Define Data (1 meter scale)
			canopyArea = Im_Area.reduceRegions(**{\
				'collection': cityPolys,
	            'reducer': ee.Reducer.sum(), 
	            'scale': 1, 
	            'crs': None, 
	            'crsTransform': None,  
	            'tileScale': 4})
			props = canopyArea.first().propertyNames()
			canopyArea = canopyArea.select(props, props.replace('sum','CanopyData_Area_1m').replace('Ar_pixel','CanopyData_Area_30m'))

			# Export
			t = ee.batch.Export.table.toAsset(**{\
			    'collection': canopyArea, 
			    'description': 'Canopy_Area_'+outStr+'_Table_toAsset', 
			    'assetId': canopyAreaDir+'/Canopy_Area_'+outStr})
			t.start()

# To check for failed tasks:
# tasks = ee.data.getTaskList()[0:211]
# status = [task['state'] for task in tasks]
# name = [task['description'] for task in tasks]
# for i, state in enumerate(status):
#   if state == 'FAILED':
#     print('FAILED: '+name[i])
#----------------------------------------------------------
#           Create Clipped Geometries and Save
#----------------------------------------------------------
# Use this workflow to clip geometries to Tiger Boundary and filter by size
# The 1m and 30m canopy area estimates must be exported to asset using 01_Export_Initial_Data.py before doing this step.

# Mask CBGs with not enough Earth Define data or that are adjacent to areas with Earth Define data
# Min size = 15000 m2 (smallest full CBG is just over this area)
# Must be min size 200000 m2 OR have (Canopy_portion_of_CBG > 0.01 and canopy_area_1m_vs_30m > 0.9)
# Canopy_portion_of_CBG = (canopy data area (1m scale))/(Full CBG area)
# Canopy_Area_1m_vs_30m = (canopy data area (1m scale))/(canopy data area (30m scale)) - if this is at the edge of polygon, this ratio will be low

def setClippedGeometry(CBG):
	geo = CBG.geometry()
	newGeo = geo.intersection(tigerBoundary)
	CBG = CBG.setGeometry(newGeo)\
		.set('Data_Area_Acres',newGeo.area(5).multiply(0.000247105))\
		.set('GeoType',newGeo.type())
	return CBG

if export_geos:

	print('Export Clipped Geometries to Asset')

	outTable = []
	allCBGs = []
	canopyAreaAssets = ee.data.listAssets({'parent': 'projects/earthengine-legacy/assets/'+canopyAreaDir})['assets'][95:]
	# canopyAreaAssets = [{'id': 'users/leahscampbell/contour/tnc/urbantree/Canopy_Area_Tables/Canopy_Area_Sacramento'},
 #                        {'id': 'users/leahscampbell/contour/tnc/urbantree/Canopy_Area_Tables/Canopy_Area_LosAngeles--LongBeach--Anaheim'}]
	for cityAsset in canopyAreaAssets:

		#-------------------Read Data and Get Area Parameters----------------------
		#cityName = cityAsset['id'].split('/')[6].split('_')[2]
		cityCBGs = ee.FeatureCollection(cityAsset['id'])
		cityName = ee.Feature(cityCBGs.first()).get('NAME').getInfo()
		print(cityName)
		#print('Original Size', cityCBGs.size().getInfo())
		allCBGs.append(cityCBGs)
		tigerBoundary = ee.Feature(tiger.filter(ee.Filter.eq('NAME10', cityName)).first()).geometry()

		cityCBGs = cityCBGs.map(lambda cbg: ee.Feature(cbg).set('Portion_of_CBG',ee.Feature(cbg).getNumber('CanopyData_Area_1m').divide(ee.Feature(cbg).getNumber('aland')))\
		          .set('1m_vs_30m', ee.Feature(cbg).getNumber('CanopyData_Area_1m').divide(ee.Feature(cbg).getNumber('CanopyData_Area_30m')))\
		          .set('PolyArea_Acres', ee.Feature(cbg).getNumber('CanopyData_Area_1m').multiply(0.000247105)))

		#------------------------Apply Filters---------------------------------
		# Min size = 15000 m2 (smallest full CBG is just over this area)
		cityCBGs = cityCBGs.filter(ee.Filter.gt('PolyArea_Acres', canopyDataMaskMinSize*0.000247105))
		#print('Filter by size of Polygon', cityCBGs.size().getInfo())

		# Must be min size 200000 m2 OR have (Canopy_portion_of_CBG > 0.01 and canopy_area_1m_vs_30m > 0.9)
		cityCBGs = cityCBGs.filter(\
			ee.Filter.Or(ee.Filter.gt('PolyArea_Acres', canopyDataMask2MinSize*0.000247105), 
		    ee.Filter.And(ee.Filter.gt('Portion_of_CBG', canopyDataMaskPortion), ee.Filter.gt('1m_vs_30m',canopyDataMaskRatio))))
		#print('Second Filter', cityCBGs.size().getInfo())

		#------------------------Clip Geometries---------------------------------
		cityCBGs = cityCBGs.map(lambda CBG: setClippedGeometry(CBG))

		cityCBGs = cityCBGs.filter(ee.Filter.Or(ee.Filter.eq('GeoType','Polygon'), ee.Filter.eq('GeoType','MultiPolygon')))

		cityCBGs = cityCBGs.select(['geoid','aland','awater','PolyArea_Acres'])
		#print('Filtered Size', cityCBGs.size().getInfo())

		outStr = areaDict[cityName]
		t = ee.batch.Export.table.toCloudStorage(**{\
	        'collection': cityCBGs, 
	        'description': 'Clipped_Geometries_'+outStr+'_toStorage', 
	        'bucket': gcpBucket, 
	        'fileNamePrefix': 'Clipped_Geometries_CBG_Table_'+outStr, 
	        'fileFormat': 'CSV'})
		t.start()
		# t = ee.batch.Export.table.toAsset(**{\
		#     'collection': cityCBGs, 
		#     'description': 'Clipped_Geos_'+outStr+'_Table_toAsset', 
		#     'assetId': 'users/leahscampbell/contour/tnc/urbantree/Clipped_Geometries/Clipped_Geos_'+outStr})
		# t.start()
	# 	outTable.append(cityCBGs)

	# outTable = ee.FeatureCollection(outTable).flatten()
	# allCBGs = ee.FeatureCollection(allCBGs).flatten()
	# print(outTable.size().getInfo())
	# pdb.set_trace()


# To check for failed tasks:
# tasks = ee.data.getTaskList()[0:203]#len(canopyAreaAssets)]#
# status = [task['state'] for task in tasks]
# name = [task['description'] for task in tasks]
# for i, state in enumerate(status):
#   if state == 'FAILED':
#     print('FAILED: '+name[i])

# #To batch download files from bucket:
gcpBucket = 'urban-tree'
localdir = r'/Volumes/Seagate Backup Plus Drive/contour/tnc/urbantree/data/v8_Input_Data/Clipped_Geometries'
command = 'gsutil -m cp -r gs://urban-tree/Clipped_Geometries* "'+localdir+'/."'
os.system(command)


taskManagerLib.trackTasks()




















