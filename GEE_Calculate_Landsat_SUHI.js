//######################################################################################################## 
//#                                                                                                    #\\
//#                      Calculating surface urban heat islands using Landsat data                     #\\
//#                                                                                                    #\\
//########################################################################################################
// date: 2021-7-24 (updated: 2021-7-24)
// authors: TC Chakraborty | tc.chakraborty@yale.edu | https://tc25.github.io/

//Load in urban areas with seeded index column
var Cities=ee.FeatureCollection('users/tirthankarchakraborty/TIGER_CA_Urban_Areas_seeded')

//Load in census block groups in California
var Group=ee.FeatureCollection('users/Shree1175/CA_UrbanReforestation/CaCensusBlockGroup2015')

//Subset census block groups overlapping with cities
var Blocks=Group.filterBounds(Cities.union())

//Export result to assets (only export the first time)
Export.table.toAsset({
collection: Blocks, assetId: 'Ca_AllCities_BlockGroup'
});

//Load in urban census block groups in California
var Blocks = ee.FeatureCollection("users/tirthankarchakraborty/Ca_AllCities_BlockGroup");

//Function for adding city metadata to block groups
function addMeta(feature){
  var select=ee.Feature(Cities.filterBounds(feature.geometry()).first())
  return feature.set({'NAME':select.get('NAME10')})
}

//Map function over census block group feature collection
var Blocks_Meta=Blocks.map(addMeta)

//Export result to assets (only export the first time)
Export.table.toAsset({
collection: Blocks_Meta, assetId: 'Ca_AllCities_BlockGroup_Meta'
});
 
//Load in urban areas with seeded index column
var cities=ee.FeatureCollection('users/tirthankarchakraborty/TIGER_CA_Urban_Areas_seeded')

//Load in urban census block groups with metadata in California
var table=ee.FeatureCollection('users/tirthankarchakraborty/Ca_AllCities_BlockGroup_Meta')

//Remove urban clusters that are not completely within the state.
var acs = ee.FeatureCollection(table)
var ca_cities = ee.FeatureCollection(cities).filterMetadata('NAME10','not_contains','AZ').filterMetadata('NAME10','not_contains','NV')

var acs_outline = ee.Image().byte().paint({featureCollection:acs, color: 1, width: 1});
var cities_outline = ee.Image().byte().paint({featureCollection:ca_cities, color: 2, width: 1});

//Load in modules to compute land Surface temperature (LST) from Landsat using the statistical mono-window algorithm 
//(Modified from https://doi.org/10.3390/rs12091471) 
var LandsatLSTsummer = require('users/tirthankarchakraborty/TC25:modules/Landsat_LST_Summer.js')
var LandsatLSTwinter = require('users/tirthankarchakraborty/TC25:modules/Landsat_LST_Winter.js')
var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js')

// select region of interest, date range, and landsat satellite
var geometry = ca_cities.geometry().bounds();
var satellite = 'L5';
var date_start = '2007-01-01';
var date_end = '2012-01-01';
var use_ndvi = true;

// get landsat collection with added variables: NDVI, FVC, TPW, EM, LST
var LandsatColl = LandsatLST.collection(satellite, date_start, date_end, geometry, use_ndvi)
var LandsatCollwinter = LandsatLSTwinter.collection(satellite, date_start, date_end, geometry, use_ndvi)
var LandsatCollsummer = LandsatLSTsummer.collection(satellite, date_start, date_end, geometry, use_ndvi)

// create mean LST images for each case
var exImagesummer = LandsatCollsummer.mean();
var exImagewinter = LandsatCollwinter.mean();
var exImage = LandsatColl.mean();

//Export result to assets (only export the first time)
Export.image.toAsset({image:exImage, assetId:'Landsat_LST_Cal_v4', region:ca_cities.geometry().bounds(), scale:30, maxPixels:9999999999999})
Export.image.toAsset({image:exImagewinter, assetId:'Landsat_LST_Cal_v4_Winter', region:ca_cities.geometry().bounds(), scale:30, maxPixels:9999999999999})
Export.image.toAsset({image:exImagesummer, assetId:'Landsat_LST_Cal_v4_Summer', region:ca_cities.geometry().bounds(), scale:30, maxPixels:9999999999999})

//Load in the processed Landsat images
var exImagesummer=ee.Image('users/tirthankarchakraborty/Landsat_LST_Cal_v4_Summer')
var exImagewinter=ee.Image('users/tirthankarchakraborty/Landsat_LST_Cal_v4_Winter')
var exImage=ee.Image('users/tirthankarchakraborty/Landsat_LST_Cal_v4')

//Select the LST band
var LST=exImage.select('LST')
var LSTwinter=exImagewinter.select('LST')
var LSTsummer=exImagesummer.select('LST')

//Select the NLCD land cover data
var landcover=ee.Image('USGS/NLCD/NLCD2016').select('landcover');
var urban=landcover

//Create pixel area image for non-open water pixels
var Im_Area=ee.Image.pixelArea().clip(ca_cities).updateMask(urban.neq(11));

//Select urban pixels in image
var urbanurban=urban.updateMask(urban.eq(23).or(urban.eq(24)))

//Select background reference pixels in image
var urbannonurban=urban.updateMask(urban.eq(41).or(urban.eq(42)).or(urban.eq(43))
.or(urban.eq(51)).or(urban.eq(52)).or(urban.eq(71)).or(urban.eq(72)).or(urban.eq(73))
.or(urban.eq(74)).or(urban.eq(81)).or(urban.eq(82)))

//Create pixel area image for non-water and water-adjacent pixels
var LSTurban=urban.updateMask(urban.neq(11).or(urban.eq(90)).or(urban.eq(95)))

//Load in urban buffer feature collection
var Cities_buff=ee.FeatureCollection('users/tirthankarchakraborty/TIGER_CA_Urban_Areas_buffer')

//Load in Digital Elevation Model (DEM_) and select values corresponding to the urban pixels
var DEM=(ee.Image('USGS/GMTED2010'));
var DEM_urban=DEM.updateMask(urbanurban);

//Function to calculate median elevation of urban pixels within each cluster
var Ar = function(feature) { 
  var ref_urb=ee.Feature(ca_cities.filterMetadata('Index_column','equals',feature.get('Index_column')).first());
  var Ar_dat = ee.Number(DEM_urban.reduceRegion({reducer:ee.Reducer.median(), geometry: ref_urb.geometry(), scale: 30, maxPixels: 10000000000000}).get('be75'))
  return feature.set({'City_DEM': Ar_dat});
};

//Map function over urban cluster feature collection
var Cities_buff=Cities_buff.map(Ar);

//Reduce feature collection of median urban DEM to an image
var DEM_urban_median=Cities_buff.filter(ee.Filter.neq('City_DEM', null)).reduceToImage({properties: ['City_DEM'], reducer: ee.Reducer.first()});

//Find all pixels that deviate from the median by more than 50 meters
var DEM_diff=(DEM.subtract(DEM_urban_median)).abs()
var urbannonurban2=DEM_diff.lte(50);

//Select LST pixels corresponding to urban land cover within the clusters
var dayurbanLST=LST.updateMask(urbanurban).clip(ca_cities);

//Select LST pixels corresponding to reference land cover (non vegetation, water body or >50 m elevation differential) within the clusters
var dayruralLST=LST.updateMask(urbannonurban).updateMask(urbannonurban2);
var AllLST=LST.updateMask(LSTurban)

//Above steps for summer and winter LST
var dayurbanLSTsummer=LSTsummer.updateMask(urbanurban).clip(ca_cities);
var dayruralLSTsummer=LSTsummer.updateMask(urbannonurban).updateMask(urbannonurban2);
var AllLSTsummer=LSTsummer.updateMask(LSTurban)
var dayurbanLSTwinter=LSTwinter.updateMask(urbanurban).clip(ca_cities);
var dayruralLSTwinter=LSTwinter.updateMask(urbannonurban).updateMask(urbannonurban2);
var AllLSTwinter=LSTwinter.updateMask(LSTurban)

//Function to calculate urban and rural LST corresponding to each cluster for the different cases
  var regions_urb= function(feature){
    
    var ref_rural=ee.Feature(Cities_buff.filterMetadata('Index_column','equals',feature.get('Index_column')).first());

      var drLST=dayruralLST.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
        var duLST=dayurbanLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLST=AllLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
     
       var drLSTsummer=dayruralLSTsummer.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
        var duLSTsummer=dayurbanLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLSTsummer=AllLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
    
      var drLSTwinter=dayruralLSTwinter.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
        var duLSTwinter=dayurbanLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLSTwinter=AllLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
    
     
           var drLSTstd=dayruralLST.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
        var duLSTstd=dayurbanLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTstd=AllLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
     
       var drLSTsummerstd=dayruralLSTsummer.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
        var duLSTsummerstd=dayurbanLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTsummerstd=AllLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
    
      var drLSTwinterstd=dayruralLSTwinter.reduceRegion({geometry: ref_rural.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
        var duLSTwinterstd=dayurbanLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTwinterstd=AllLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})

    return feature.set({'Urban_LST':duLST.get('LST'),'Rural_LST':drLST.get('LST'),'All_LST':dLST.get('LST'),
      'Urban_LSTsummer':duLSTsummer.get('LST'),'Rural_LSTsummer':drLSTsummer.get('LST'),'All_LSTsummer':dLSTsummer.get('LST'),
      'Urban_LSTwinter':duLSTwinter.get('LST'),'Rural_LSTwinter':drLSTwinter.get('LST'),'All_LSTwinter':dLSTwinter.get('LST'),
      'Urban_LSTstd':duLSTstd.get('LST'),'Rural_LSTstd':drLSTstd.get('LST'),'All_LSTstd':dLSTstd.get('LST'),
      'Urban_LSTsummerstd':duLSTsummerstd.get('LST'),'Rural_LSTsummerstd':drLSTsummerstd.get('LST'),'All_LSTsummerstd':dLSTsummerstd.get('LST'),
      'Urban_LSTwinterstd':duLSTwinterstd.get('LST'),'Rural_LSTwinterstd':drLSTwinterstd.get('LST'),'All_LSTwinterstd':dLSTwinterstd.get('LST')   })
    
  }

//Function to calculate urban and rural LST corresponding to each census block group for the different cases
  var regions_cbg= function(feature){
 var duLST=dayurbanLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLST=AllLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
  var duLSTsummer=dayurbanLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLSTsummer=AllLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
  var duLSTwinter=dayurbanLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
       var dLSTwinter=AllLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.mean(),  scale: 30, maxPixels:9999999999999999})
 
  var duLSTstd=dayurbanLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTstd=AllLST.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
  var duLSTsummerstd=dayurbanLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTsummerstd=AllLSTsummer.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
  var duLSTwinterstd=dayurbanLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
       var dLSTwinterstd=AllLSTwinter.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.stdDev(),  scale: 30, maxPixels:9999999999999999})
            var Ar_pixel=Im_Area.reduceRegion({geometry: feature.geometry(),  reducer: ee.Reducer.sum(),  scale: 30, maxPixels:9999999999999999})
    
 
    return feature.set({'Urban_LST':duLST.get('LST'),'All_LST':dLST.get('LST'),
      'Urban_LSTsummer':duLSTsummer.get('LST'),'All_LSTsummer':dLSTsummer.get('LST'),
      'Urban_LSTwinter':duLSTwinter.get('LST'),'All_LSTwinter':dLSTwinter.get('LST'),
      'Urban_LSTstd':duLSTstd.get('LST'),'All_LSTstd':dLSTstd.get('LST'),
      'Urban_LSTsummerstd':duLSTsummerstd.get('LST'),'All_LSTsummerstd':dLSTsummerstd.get('LST'),
      'Urban_LSTwinterstd':duLSTwinterstd.get('LST'),'All_LSTwinterstd':dLSTwinterstd.get('LST'),
      'Ar_pixel':Ar_pixel.get('area')
    })
    
  }

//Remove urban clusters that are not completely within the state.
acs=acs.filterMetadata('NAME','not_contains','AZ').filterMetadata('NAME','not_contains','NV')

//Map functions for the corresponding feature collections
var urb_diss_UHI=ca_cities.map(regions_urb)
var urb_cbg_UHI=acs.map(regions_cbg)

//Export result to assets (only export the first time)
Export.table.toAsset({
collection: urb_diss_UHI, assetId: 'CalUHI_diss_vf_All'
});

Export.table.toDrive({
collection: urb_diss_UHI, folder: 'CalUHI_Tanu', description: 'CalUHI_diss_vf_All',  fileFormat: 'GeoJSON'
});

//Export results with and without geometry to drive
var urb_diss_UHI=urb_diss_UHI.select({propertySelectors:ee.Feature(urb_diss_UHI.first()).propertyNames(),retainGeometry:false})

Export.table.toDrive({
collection: urb_diss_UHI, folder: 'CalUHI_Tanu', description: 'CalUHI_diss_vf_All',  fileFormat: 'CSV'
});

Export.table.toAsset({
collection: urb_cbg_UHI, assetId: 'CalUHI_cb_vf_All'
});

Export.table.toDrive({
collection: urb_cbg_UHI, folder: 'CalUHI_Tanu', description: 'CalUHI_cb_vf_All',  fileFormat: 'GeoJSON'
});

var urb_cbg_UHI=urb_cbg_UHI.select({propertySelectors:ee.Feature(urb_cbg_UHI.first()).propertyNames(),retainGeometry:false})

Export.table.toDrive({
collection: urb_cbg_UHI, folder: 'CalUHI_Tanu', description: 'CalUHI_cb_vf_All',  fileFormat: 'CSV'
});