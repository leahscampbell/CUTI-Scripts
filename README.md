# CUTI-Scripts
Closing Urban Tree cover Inequity (CUTI) Script Repository
* Scripts used to generate suitability scores and tree canopy cover estimates for CUTI study.
* Contains all methods outlined in Chakraborty, T., T. Biswas, L.S. Campbell, B. Franklin, S. Parker, and M. Tukman, 2022. Feasibility of Afforestation as an Equitable Nature-Based Solution in Urban Areas. Sustainable Cities and Society, 81. https://doi.org/10.1016/j.scs.2022.103826

## Primary POCs
* Primary technical contacts
	* TC Chakraborty - tc.chakraborty@yale.edu
	* Leah Campbell - lcampbell@contourgroupconsulting.com

* Primary manuscript authors
	* TC Chakraborty - tc.chakraborty@yale.edu
	* Tanushree Biswas - tanushree.biswas@tnc.org

## Dependencies
* earthengine-api (Javascript API)
* Python 3
* earthengine-api (Python package)
* geeViz (Python package)

## Using
* Ensure you have Python 3 installed
  * <https://www.python.org/downloads/>
  
* Ensure the Google Earth Engine api is installed and up-to-date
  * `pip install earthengine-api --upgrade`
  * `conda update -c conda-forge earthengine-api`

* Ensure geeViz is installed and up-to-date
  * `pip install geeViz --upgrade`

* Running scripts
  * The two GEE js scripts are run first to generate the urban and rural reference polygons, calculate land surface temperature from Landsat satellite observations, and finally calculate the surface urban heat island intensity. 
  * Each consequent python script is then intended to run sequentially to reproduce the methods used in Chakraborty et al 2021 (forthcoming)
  
## Final data
The city and CBG-level suitability summaries (Suitability_Summaries_City_v10_limit.csv and Suitability_Table_CBG_v10_limit.csv), as well as the intermediate variables calculated in the study (CBG_Table_v10.csv), are in the Data tables directory. 
  

