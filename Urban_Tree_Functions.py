#---------------------------------------------------------------
#				Urban_Tree_Functions.py
#---------------------------------------------------------------
# Library of functions to be used in 03_Run_Regression_and_Suitability.py

import os, pdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy import stats
import statsmodels.api as sm

#------------------------------------------------------------------
#			Income Quartile Stats
#------------------------------------------------------------------
def groupIncome(incomeQuartiles, i):
	
	if i <= incomeQuartiles[0]:
		group = 1
	elif i > incomeQuartiles[0] and i <= incomeQuartiles[1]:
		group = 2
	elif i > incomeQuartiles[1] and i <= incomeQuartiles[2]:
		group = 3
	else:
		group = 4

	return group

def calcQuartileStats(data, quartileVars):
	
	# Income Quartiles
	incomeQuartiles = data['Income'].quantile(q=[0.25,0.5,0.75]).to_numpy()
	data['Income_Quartile'] = data['Income'].apply(lambda i: groupIncome(incomeQuartiles, i))

	group4 = data[data['Income_Quartile'] == 4]
	data['group4_UHI_median'] = group4['uhiSummer'].median()
	data['group4_canopyPercent_median'] = group4['canopyPercent'].median()

	group3 = data[data['Income_Quartile'] == 3]
	data['group3_UHI_median'] = group3['uhiSummer'].median()
	data['group3_canopyPercent_median'] = group3['canopyPercent'].median()

	group2 = data[data['Income_Quartile'] == 2]
	data['group2_UHI_median'] = group2['uhiSummer'].median()
	data['group2_canopyPercent_median'] = group2['canopyPercent'].median()

	group1 = data[data['Income_Quartile'] == 1]
	data['group1_UHI_median'] = group1['uhiSummer'].median()
	data['group1_canopyPercent_median'] = group1['canopyPercent'].median()

	data['TGTree_Per'] = data['group4_canopyPercent_median'].subtract(data['canopyPercent'])
	data['treeGap_acresTotal'] = data['group4_canopyPercent_median'].multiply(data['PolyArea_Acres'])
	data['TGTree_Acr'] = data['treeGap_acresTotal'].subtract(data['canopyAcres'])

	# Limited Scenario - Trees Needed
	data['TGTree_Acre_Lim'] = np.where((data['TGTree_Acr'] > data['PotAreaAcr']), data['PotAreaAcr'], data['TGTree_Acr'])
	data['TGUhi_Acre_Lim'] = np.where((data['TGUhi_Acre'] > data['PotAreaAcr']), data['PotAreaAcr'], data['TGUhi_Acre'])

	try:
		data['Population_Quartile'] = pd.qcut(data['Population'], 4, labels = ['1','2','3','4']).astype('str')
	except:
		data['Population_Quartile'] = 0
	data['Ratio_Pop_Inc'] = data['Population'].divide(data['Income'])

	return data[quartileVars]

#------------------------------------------------------------------
#			Regression Functions
#------------------------------------------------------------------
# Create the Regression to be Used in the Following Steps
def calcMultivariateLinearRegression_SM(x, y, varShortNames):
	x = sm.add_constant(x, has_constant='add')
	reg = sm.OLS(y, x).fit()
	print(reg.summary())

	rsquared = reg.rsquared
	m = reg.params.iloc[1:]
	b = reg.params.iloc[0]
	canopySlope = m.iloc[0]
	conf_int = reg.conf_int(alpha=0.05, cols=None)
	SlopeConf95Low = conf_int.loc['canopyPercent',0]
	SlopeConf95High = conf_int.loc['canopyPercent',1]
	#predict = reg.predict(x)

	equation = 'y = '
	for i, var in enumerate(varShortNames):
		equation = equation + f'{m.iloc[i]:.4f}'+'*'+var+' + '
		if i == np.ceil(len(varShortNames)/3) or i == np.ceil(len(varShortNames)*2/3):
			equation = equation +'\n'
	equation = equation + f'{b:.4f}'

	return reg, equation, rsquared, canopySlope, SlopeConf95Low, SlopeConf95High

# Plot the Linear Regression for Each Group
def plotMultivariateLinearRegression_SM(reg, x, y, equation, plot_xvar, title, ylabel, xlabel, savedir, saveName, xlim = None, ylim = None, arcsinTransform = False):
	
	if len(y) >= 30:
		predictLen = 30
	else:
		predictLen = len(y)
	# Calculate median values of each of the non-plot_xvars
	predictTable = x.loc[0:predictLen-1, :].copy()
	if arcsinTransform == True:
		predictTable[plot_xvar] = np.linspace(0, np.pi/2, predictLen)
	else:
		predictTable[plot_xvar] = np.linspace(0, 1, predictLen)
	for var in x.columns:
		if var != plot_xvar:
			predictTable[var] = x[var].median()
	predictTable = sm.add_constant(predictTable, has_constant='add')
	predict = reg.predict(predictTable)
	rsquared = reg.rsquared
		
	# Calculate xlabels
	if arcsinTransform == True:
		percentTicks = [0, 0.1, 0.2, 0.4, 0.6, 0.8]
		tickLocs = [np.arcsin(np.sqrt(i)) for i in percentTicks]
		tickLabels = [int(i*100) for i in percentTicks]
	else:
		tickLocs = np.arange(0, 1, 0.2)
		tickLabels = [int(i*100) for i in tickLocs]

	fig = plt.figure(figsize=(7,4),frameon=True,facecolor='w')
	ax = fig.add_axes([0.1, 0.14, 0.72, 0.76])
	sc = ax.scatter(x[plot_xvar], y, c = x['Income'], vmax = 100000, s = 1)
	ax.plot(predictTable[plot_xvar], predict, color='k')
	ax.axhline(y=0, linestyle = '--', color='k')
	#ax.axhline(y=group4_UHI_median, linestyle = ':', color = 'r')
	#ax.axhline(y=group3_UHI_median, linestyle = ':', color = 'r')
	ax.text(0.99, 0.97, equation, transform=ax.transAxes, 
				fontsize = 8, color = 'k', verticalalignment='top', horizontalalignment = 'right')
	ax.text(0.99, 0.86, '$r^2$ = '+f'{rsquared:.2f}', transform=ax.transAxes, 
			fontsize = 10, color = 'k', verticalalignment='top', horizontalalignment = 'right')
	ax.text(0.99, 0.8, 'n = '+str(len(x)), transform=ax.transAxes, 
			fontsize = 10, color = 'k', verticalalignment='top', horizontalalignment = 'right')
	ax.set_title(title)
	if xlim != None:
		ax.set_xlim(xlim[0], xlim[1])
	if ylim != None:
		ax.set_ylim(ylim[0], ylim[1])
	ax.set_ylabel(ylabel)
	ax.set_xlabel(xlabel)
	ax.set_xticks(tickLocs)
	ax.set_xticklabels(tickLabels)

	cbax = fig.add_axes([0.85, 0.14, 0.03, 0.76]) 
	cb = plt.colorbar(sc, cax = cbax, orientation = 'vertical')
	cb.ax.tick_params(labelsize=10)
	cb.set_label('Income', rotation = 270, labelpad = 15, fontsize = 10)

	fig.savefig(os.path.join(savedir, saveName))
	plt.close()

# Using the Regression, Calculate Variables of Interest
def predictUHIVals(data, variables, reg, arcsinTransform = False):
	
	# LinReg line with actual Canopy Percent
	predictTable = data[variables].copy()
	predictTable = sm.add_constant(predictTable, has_constant = 'add')
	predict_current = reg.predict(predictTable)	

	# Potential UHI if use all available space (MPUA)
	variables[0] = 'potentialCanopyPercent' # replace regular canopy percent in table with potential canopy percent
	predictTable = data[variables].copy()
	predictTable = sm.add_constant(predictTable, has_constant = 'add')
	predict = reg.predict(predictTable)	

	# Potential UHI if close the tree gap (TREEGAP)
	variables[0] = 'group4_canopyPercent_median' # replace regular canopy percent in table with group 4 canopy percent
	predictTable = data[variables].copy()
	predictTable = sm.add_constant(predictTable, has_constant = 'add')
	predict_treegap = reg.predict(predictTable)

	# Canopy Needed for UHIGAP scenario
	target_intercept = data['uhiSummer'].subtract(data['canopyPercent'].multiply(reg.params.iloc[1])) # b = y - mx
	# calculate target canopy percent if UHI is higher than target, otherwise set to current value.
	targetCanopyPercent_regr = np.where(data['uhiSummer'] >= data['group4_UHI_median'], (data['group4_UHI_median'].copy().subtract(target_intercept)).divide(reg.params.iloc[1]), data['canopyPercent'])

	out = pd.DataFrame(data = {'Old UHI': data['uhiSummer'].copy(), 
								'UHI_Modeled': predict_current, # Modeled UHI Along Regression Line
								'Modeled_MinPotUHI': predict, # Modeled Potential UHI if use all available space
								'Modeled_TGPotUHI': predict_treegap, # Modeled TreeGap Closed UHI
								'Old Canopy Percent': data['canopyPercent'].copy(), 
								'Pot. Canopy Percent': data['potentialCanopyPercent'].copy(), 
								'targetCanopyPercent_regr': targetCanopyPercent_regr, # Canopy Needed to Achieve Group 4 UHI 
								'geoid': data['geoid'].copy()})	
	#print(out)
	
	return out

# Wrapper to Run Regression, Plot it, and Predict Values
def runRegression(allData, data, groupString, regressionVars, savedir):	

	#-----------No Transform - MultiVariate--------------------
	variables = ['canopyPercent', 'Dist_coast', 'Dist_urbCenter', 'PopDensKm2', 'Income',
	   'NLCD_Dev_HighIntensity_Perc', 'NLCD_Dev_MedIntensity_Perc',
       'NLCD_Dev_LowIntensity_Perc', 'NLCD_Dev_OpenSpace_Perc',
       'NLCD_Other_Perc']
	shortNames = ['Can','DistCo', 'DistUrb','Pop','Inc','NLCDHigh','NLCDMed','NLCDLow','NLCDOpen','NLCDOther']

	regrName = 'multivar'
	saveName = regrName+'_'+groupString

	copy = data.copy().reset_index(drop = True)

	x = copy[variables]
	y = copy['uhiSummer']

	reg, equation, rsquared, canopySlope, SlopeConf95Low, SlopeConf95High = calcMultivariateLinearRegression_SM(x, y, shortNames)
	plotMultivariateLinearRegression_SM(reg, x, y, equation, 'canopyPercent', groupString+':\nMultiVariate Linear Regression', 'UHI (C)', 'Percent Canopy Cover', savedir, saveName+'.png', xlim = [0, 1.0], ylim = [-6, 15], arcsinTransform = False )

	# Predict values for each scenario (TREEGAP, UHIGAP, MPUA)
	predict = predictUHIVals(data, variables, reg, False)

	#predict['equation_'+regrName] = equation
	predict['r2'] = rsquared
	predict['regression_num'] = int(len(y))
	predict['regression_group'] = groupString
	predict['regression_canopy_slope'] = canopySlope
	predict['SlopeConf95Low'] = SlopeConf95Low
	predict['SlopeConf95High'] = SlopeConf95High

	allData.update(predict[regressionVars]) 
	
	return allData

#------------------------------------------------------------------
#			Suitability
#------------------------------------------------------------------
def suitabilityStats(data, suitabilityVars):	
	uhiMask = data['uhiSummer'].le(0)
	uhi = data['uhiSummer'].mask(uhiMask)
	data['rankUHI'] = uhi.apply(lambda score: stats.percentileofscore(uhi.dropna(), score, kind='rank')).fillna(0)

	data['rankPopDensity'] = data['PopDensKm2'].apply(lambda score: stats.percentileofscore(data['PopDensKm2'].dropna(), score, kind='rank'))
	data['rankPopulation'] = data['Population'].apply(lambda score: stats.percentileofscore(data['Population'].dropna(), score, kind='rank'))
	data['rankIncome'] = data['Income'].multiply(-1).apply(lambda score: stats.percentileofscore(data['Income'].multiply(-1).dropna(), score, kind='rank'))
	data['Ratio_Ranked_Pop_Inc'] = data['rankPopulation'].divide(data['rankIncome'])


	data['TGDiffUHI'] = data['UHI_Modeled'].subtract(data['Modeled_TGPotUHI'])
	data['MinDiffUHI'] = data['UHI_Modeled'].subtract(data['Modeled_MinPotUHI'])
	# Mask out values where UHI increases 
	data.loc[data['TGDiffUHI'].lt(0), 'TGDiffUHI'] = 0
	data.loc[data['MinDiffUHI'].lt(0), 'MinDiffUHI'] = 0

	# dUHI2 = UHI difference needed to reach high income UHI 
	data['UHIGap'] = data['uhiSummer'].subtract(data['group4_UHI_median'])

	# If there is not enough potential area to meet TG or UG goal, set to MPUA ("Limited" scenario)
	data['TGDiffUHI_Lim'] = np.where((data['TGDiffUHI'] > data['MinDiffUHI']), data['MinDiffUHI'], data['TGDiffUHI'])
	data['UGDiffUHI_Lim'] = np.where((data['UHIGap'] > data['MinDiffUHI']), data['MinDiffUHI'], data['UHIGap'])

	# Set Diff to zero if there is no tree gap
	data['TGDiffUHI_Lim'] = np.where((data['TGTree_Acr'] < 0), 0, data['TGDiffUHI_Lim'])
	data['UGDiffUHI_Lim'] = np.where((data['TGUhi_Acre'] < 0), 0, data['UGDiffUHI_Lim'])

	# Theoretical Scenario - Potential UHI
	data['TGPotUHI'] = data['uhiSummer'].subtract(data['TGDiffUHI'])
	data['MinPotUHI'] = data['uhiSummer'].subtract(data['MinDiffUHI'])
	
	# Limited Scenario - Potential UHI
	data['TGPotUHI_Lim'] = data['uhiSummer'].subtract(data['TGDiffUHI_Lim'])
	data['UGPotUHI_Lim'] = data['uhiSummer'].subtract(data['UGDiffUHI_Lim'])

	# For UHIGap scenario, if Current UHI is less than HiIncome UHI, set to current UHI
	data['UGPotUHI_Lim'] = np.where((data['uhiSummer'] < data['group4_UHI_median']), data['uhiSummer'], data['UGPotUHI_Lim'])
	data['UGDiffUHI_Lim'] = np.where((data['uhiSummer'] < data['group4_UHI_median']), 0, data['UGDiffUHI_Lim'])

	# Get UHIGAP scenario stats
	data['targetCanopyAcres'] = data['targetCanopyPercent_regr'].multiply(data['PolyArea_Acres'])
	data['TGUhi_Acre'] = data['targetCanopyAcres'].subtract(data['canopyAcres'])
	data['TGUhi_Perc'] = data['TGUhi_Acre'].divide(data['PolyArea_Acres'])
	
	# Limited Scenario - Trees Needed
	data['TGTree_Acre_Lim'] = np.where((data['TGTree_Acr'] > data['PotAreaAcr']), data['PotAreaAcr'], data['TGTree_Acr'])
	data['TGUhi_Acre_Lim'] = np.where((data['TGUhi_Acre'] > data['PotAreaAcr']), data['PotAreaAcr'], data['TGUhi_Acre'])
	data['TGTree_Per_Lim'] = np.where((data['TGTree_Acr'] > data['PotAreaAcr']), data['PotAreaAcr']/data['PolyArea_Acres'], data['TGTree_Per_Lim'])
	data['TGUhi_Per_Lim'] = np.where((data['TGUhi_Acre'] > data['PotAreaAcr']), data['PotAreaAcr']/data['PolyArea_Acres'], data['TGUhi_Per_Lim'])

	# Set Trees Needed to zero if negative
	data['TGTree_Acre_Lim'] = np.where((data['TGTree_Acr'] < 0), 0, data['TGTree_Acre_Lim'])
	data['TGUhi_Acre_Lim'] = np.where((data['TGUhi_Acre'] < 0), 0, data['TGUhi_Acre_Lim'])
	data['TGTree_Per_Lim'] = np.where((data['TGTree_Acr'] < 0), 0, data['TGTree_Per_Lim'])
	data['TGUhi_Per_Lim'] = np.where((data['TGUhi_Acre'] < 0), 0, data['TGUhi_Per_Lim'])

	#data[['canopyAcres','PolyArea_Acres','canopyPercent','group4_canopyPercent_median','TGTree_Acr','PotAreaAcr','TGTree_Per','TGTree_Per_Lim']][data['PotAreaAcr'].lt(data['TGTree_Acr'])]
	# Max Potential Tree Canopy Acres
	data['mTC_Acres'] = data['canopyAcres'].add(data['PotAreaAcr'])

	# RatioCANTree = ratio TGTree_Acres/Potential Area
	data['RatCANTree'] = data['TGTree_Acr'].divide(data['PotAreaAcr']).mask(data['TGTree_Per'].le(0)).mask(data['PotAreaAcr'].eq(0))

	# RatioCANUhi = ratio TGUhi_Acre/Potential Area
	data['RatCANUhi'] = data['TGUhi_Acre'].divide(data['PotAreaAcr']).mask(data['TGUhi_Perc'].le(0)).mask(data['PotAreaAcr'].eq(0))

	# Suitability Variables
	# A1 = UHIGap * TreeGap * Population / Income, TreeGap > 0
	data['A1'] = data['UHIGap'].multiply(data['TGTree_Per'].multiply(100)).multiply(data['PopDensKm2']).divide(data['Income'])\
		.mask(data['TGTree_Per'].le(0)).mask(data['UHIGap'].le(0)) #Mask out any TG or UHI Gap less than or equal to zero.

	# A2 = A1 / ratioCANTree
	data['A1'] = data['A1'].divide(data['RatCANTree'])

	# A4 = Potential UHI Change * TreeGapUHI * Population / Income, TreeGapUHI > 0
	data['A2'] = data['MinDiffUHI'].multiply(data['TGUhi_Perc'].multiply(100)).multiply(data['PopDensKm2']).divide(data['Income'])\
		.mask(data['TGUhi_Perc'].le(0)).mask(data['MinDiffUHI'].le(0)); #Mask out any TGUHI less than or equal to zero.

	# A5 = A4 / ratioCANUhi
	data['A2'] = data['A2'].divide(data['RatCANUhi'])

	# Suitability Ranking
	data['A1_ranked'] = data['A1'].apply(lambda score: stats.percentileofscore(data['A1'].dropna(), score, kind='rank'))
	data['A2_ranked'] = data['A2'].apply(lambda score: stats.percentileofscore(data['A2'].dropna(), score, kind='rank'))	
	try:
		data['A1_quartile'] = pd.qcut(data['A1'], 4, labels = ['1','2','3','4']).astype('str')
	except:
		data['A1_quartile'] = 0
	try:
		data['A2_quartile'] = pd.qcut(data['A2'], 4, labels = ['1','2','3','4']).astype('str')
	except:
		data['A2_quartile'] = 0
	data = data.fillna(0)
	data[['A1_quartile','A2_quartile']] = data[['A1_quartile','A2_quartile']].astype('int')

	# Calculate Potential Energy Savings
	#kW savings = AC Penetration rate (%) * Number of Households per CBG * ET Sensitivity (kW/C) * UHI Reduction (C)
	data['Pot_kW_Low'] = data['AC_Low'].divide(100).multiply(data['Households']).multiply(data['ET_Low']).multiply(data['MinDiffUHI'])
	data['Pot_kW_High'] = data['AC_High'].divide(100).multiply(data['Households']).multiply(data['ET_High']).multiply(data['MinDiffUHI'])

	return data[suitabilityVars]















