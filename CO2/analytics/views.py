from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from .models import Measure
import pandas as pd
import numpy as np
import scipy

pd.options.plotting.backend = 'matplotlib'

def season(indices): #returns the season of a date
	ind=pd.to_datetime(indices)
	d=ind.date()
	year=d.year
	d1=datetime.date(year-1,12,21)
	d2=datetime.date(year,3,21)
	d3=datetime.date(year,6,21)
	d4=datetime.date(year,9,21)
	d5=datetime.date(year,12,21)
	if d>= d1 and d < d2:
		return "winter "+str(year)
	if d>= d2 and d < d3:
		return "spring "+str(year)
	if d>= d3 and d < d4:
		return "summer "+str(year)
	if d>= d4 and d < d5:
		return "fall "+str(year)
	if d>= d5 :
		return "winter "+str(year+1)
def week_or_weekend(indices):
	ind=pd.to_datetime(indices)
	d=ind.date()
	weekno=d.weekday()
	if weekno<5:
		return "week"
	else:
		return "weekend"

def index(request):

	real_data=[]
	interpolate_data=[]
	#Data collecting from database
	for m in Measure.objects.order_by('-measure_date'):
		real_data.append(m.measure_rate)
		interpolate_data.append(m.measure_rate)
		interpolate_data.append(np.nan)
	#Construction of time indices
	time_index_real = pd.date_range(start='2017-01-01', end='2019-01-01',freq='0.5H')[:-1]
	time_index_interpolate=pd.date_range(start='2017-01-01', end='2019-01-01',freq='0.25H')[:-1]
	#Construction of time series
	time_serie_real=pd.Series(real_data, index=time_index_real)
	time_serie_interpolate=pd.Series(interpolate_data, index=time_index_interpolate)
	time_serie_interpolate=time_serie_interpolate.interpolate(method='polynomial', order=2)

	#fig=time_serie_real.plot(grid=True)
	#time_serie_interpolate.plot(grid=True,ylim=(0,10000))
	#plt.show()

	#Seasons meadians
	real_medians=time_serie_real.groupby(by=season).median()
	real_medians=real_medians.to_dict()
	interpolate_medians=time_serie_interpolate.groupby(by=season).median()
	interpolate_medians=interpolate_medians.to_dict()
	#weekday and weekend means
	real_means=time_serie_real.groupby(by=week_or_weekend).mean()
	real_means=real_means.to_dict()
	interpolate_means=time_serie_interpolate.groupby(by=week_or_weekend).mean()
	interpolate_means=interpolate_means.to_dict()

	#Limiting the precision of the values of the means
	for key,value in real_means.items():
		real_means[key]="%.2f" % value
	for key,value in interpolate_means.items():
		interpolate_means[key]="%.2f" % value
	
	#Calculating consumption from CSV
	cols = ["Consommation (MW)", "Taux de CO2 (g/kWh)"]
	file_data = pd.read_csv("analytics/eco2mix-national-cons-def.csv",encoding="utf-8",usecols=cols,sep=';')
	file_data[cols] = file_data[cols].replace(np.NaN, 0) #replacing Nan by zeros
	production_CO2=file_data[cols].product(axis=1).sum(axis=0)/1000 #the 1/1000 coefficient is due units conversion

	#Constructing the context for the template
	context = {
	#'real_data': real_data[:10],
	#'interpolate_data':interpolate_data[:20],
	'real_medians':real_medians,
	'real_means':real_means,
	'interpolate_medians':interpolate_medians,
	'interpolate_means':interpolate_means,
	'production_CO2':production_CO2
	}
	#Loading the template 
	template = loader.get_template('analytics/index.html')

	return HttpResponse(template.render(context,request))