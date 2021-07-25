//######################################################################################################## 
//#                                                                                                    #\\
//#              Generating standardized urban buffers for urban heat island calculations              #\\
//#                                                                                                    #\\
//########################################################################################################
// date: 2021-7-24 (updated: 2021-7-24)
// authors: TC Chakraborty | tc.chakraborty@yale.edu | https://tc25.github.io/

//Load in urban feature collection
var urb =ee.FeatureCollection('users/Shree1175/CA_UrbanReforestation/TIGER_CA_Urban_Areas')

//Add random seeded column for indexing
var urb=urb.randomColumn('Index_column', 5)

//Function for calculating area of features
function are_calc(feature){
  var ar=ee.Number(feature.area())
  return feature.set({"Area":ar})
}

//Map function over urban feature collection
var urb=urb.map(are_calc)

//Export result to assets (only export the first time)
Export.table.toAsset({collection:urb, assetId: 'TIGER_CA_Urban_Areas_seeded'})

//Define sequence of buffer widths to be tested
var Buff_widths=ee.List.sequence(30, 30000, 30)

//Function to generate standardized buffers (~comparable to area of urban cluster)
function Optimize(feature){
function buff(bufflength){
 var Buffed_polygon= ee.Feature(feature.buffer(ee.Number(bufflength))).set({'Buffer_width':ee.Number(bufflength)})
  var Area=ee.Number((Buffed_polygon.geometry().difference(feature.geometry())).area())
  return ee.Feature(Buffed_polygon.geometry().difference(feature.geometry())).set({"Buffer_diff":ee.Number(Area.subtract(ee.Number(feature.get('Area')))).abs(),"Buffer_area":Area, 'Buffer_width':Buffed_polygon.get('Buffer_width')})
}

var Buffed=ee.FeatureCollection(Buff_widths.map(buff))
var Sorted_bybuffer=Buffed.sort({property:"Buffer_diff"})
var First_feature=ee.Feature(Sorted_bybuffer.first())
return First_feature.set({'Index_column':feature.get('Index_column'),'Urban_Area':feature.get('Area'),'Buffer_width':First_feature.get('Buffer_width')})

}
//Map function over urban feature collection
var Optimum=urb.map(Optimize)

//Export result to assets
Export.table.toAsset({collection:Optimum, assetId: 'TIGER_CA_Urban_Areas_buffer'})