from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpRequest
import datetime
#import time 
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from .models import Measure,Image
import pandas as pd
import numpy as np
from .settings import MEDIA_ROOT, MEDIA_URL

pd.options.plotting.backend = 'matplotlib'
MIN_DATE="2017-01-01"
MAX_DATE="2019-01-01"
INTERPOLATE_IMG='interpolate.png'
REAL_IMG='real.png'
DIFF_IMG='diff.png'


def main(request):
    imgs = Image.objects.all()
    return render_to_response('index.html', {'images': imgs, 'media_root': MEDIA_ROOT, 'media_url': MEDIA_URL})

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
def week_or_weekend(indices): #return if a date is a weekday or weekend 
	ind=pd.to_datetime(indices)
	d=ind.date()
	week_no=d.weekday()
	#print(week_no)
	if week_no<5:
		return "weekday"
	else:
		return "weekend"
def time_series():
	real_data=[]
	interpolate_data=[]
	for idx,m in enumerate(Measure.objects.order_by('-measure_date')): #Collecting data from database
		real_data.append(m.measure_rate)
		if idx%2==0:
			interpolate_data.append(m.measure_rate)
		else:
			interpolate_data.append(np.NaN)
	#Construction of time indices
	time_index_real = pd.date_range(start='2017-01-01', end='2019-01-01',freq='0.5H')[:-1]
	time_index_interpolate=pd.date_range(start='2017-01-01', end='2019-01-01',freq='0.5H')[:-1]
	#Construction of time series
	time_serie_real=pd.Series(real_data, index=time_index_real)
	time_serie_interpolate=pd.Series(interpolate_data, index=time_index_interpolate)
	time_serie_interpolate=time_serie_interpolate.interpolate()
	for key,value in time_serie_interpolate.items():
		time_serie_interpolate[key]="%.2f" % value
	return [time_serie_real,time_serie_interpolate]

def index(request):
	#Construction of time series
	time_serie_real,time_serie_interpolate=time_series()
	GET_isset=False
	#Generating the plots
	if request.method=="GET" and len(request.GET)>0:
		GET_isset=True
		start_plot=request.GET['start']
		end_plot=request.GET['end']
		start_plot=datetime.datetime.strptime(start_plot, "%Y-%m-%d")
		end_plot=datetime.datetime.strptime(end_plot, "%Y-%m-%d")
		plot_index=pd.date_range(start=start_plot, end=end_plot,freq='0.5H')[:-1]
		real_plot=time_serie_real[plot_index]
		interpolate_plot=time_serie_interpolate[plot_index]
		diff_plot=real_plot.subtract(interpolate_plot)
		real_fig = plt.figure()
		real_plot.plot(kind='line',ylim=(0,100),figsize=(8,2),grid=True)
		real_fig.savefig(MEDIA_URL+'images/'+REAL_IMG)
		interpolate_fig=plt.figure()
		interpolate_plot.plot(kind='line',ylim=(0,100),figsize=(8,2),grid=True)
		interpolate_fig.savefig(MEDIA_URL+'images/'+INTERPOLATE_IMG)
		diff_fig = plt.figure()
		diff_plot.plot(kind='line',ylim=(-50,50),figsize=(8,2),grid=True)
		diff_fig.savefig(MEDIA_URL+'images/'+DIFF_IMG)
	else:
		start_plot="2017-01-01"
		end_plot="2019-01-01"

	start_get=start_plot
	end_get=end_plot
	
	#construction of seasons medians series
	seasons_order = ["winter 2017", "spring 2017","summer 2017", 
			"fall 2017","winter 2018", "spring 2018",
			"summer 2018", "fall 2018", "winter 2019"]

	real_medians=time_serie_real.groupby(by=season).median()
	interpolate_medians=time_serie_interpolate.groupby(by=season).median()

	
	real_medians.index = pd.CategoricalIndex(real_medians.index, categories=seasons_order, ordered=True)
	real_medians = real_medians.sort_index()
	interpolate_medians.index = pd.CategoricalIndex(interpolate_medians.index, categories=seasons_order, ordered=True)
	interpolate_medians = interpolate_medians.sort_index()
	
	real_medians=real_medians.to_dict()
	interpolate_medians=interpolate_medians.to_dict()
	
	#weekday and weekend means
	real_means=time_serie_real.groupby(by=week_or_weekend).mean()
	real_means=real_means.to_dict()
	print(real_means)
	interpolate_means=time_serie_interpolate.groupby(by=week_or_weekend).mean()
	interpolate_means=interpolate_means.to_dict()

	#Limiting the precision of the values of the means
	for key,value in interpolate_medians.items():
		interpolate_medians[key]="%.2f" % value
	for key,value in real_means.items():
		real_means[key]="%.2f" % value
	for key,value in interpolate_means.items():
		interpolate_means[key]="%.2f" % value
	
	#Calculating consumption from CSV
	cols = ["Consommation (MW)", "Taux de CO2 (g/kWh)"]
	file_data = pd.read_csv("analytics/eco2mix-national-cons-def.csv",encoding="utf-8",usecols=cols,sep=';')
	file_data[cols] = file_data[cols].replace(np.NaN, 0) #replacing Nan by zeros
	production_CO2=file_data[cols].product(axis=1).sum(axis=0)/1000 #the 1/1000 coefficient is due units conversion

	imgs = Image.objects.all()


	#Constructing the context for the template
	context = {
	'real_medians':real_medians,
	'real_means':real_means,
	'interpolate_medians':interpolate_medians,
	'interpolate_means':interpolate_means,
	'production_CO2':production_CO2,
	'min_date': MIN_DATE,
	'max_date': MAX_DATE,
	'start_value':start_get,
	'end_value':end_get,
	'images': imgs, 
	'media_root': MEDIA_ROOT, 
	'media_url': MEDIA_URL
	}
	if GET_isset:
		context['url_interpolate_img']=MEDIA_URL+'images/'+INTERPOLATE_IMG
		context['url_real_img']=MEDIA_URL+'images/'+REAL_IMG
		context['url_diff_img']=MEDIA_URL+'images/'+DIFF_IMG
	#Loading the template 
	template = loader.get_template('analytics/index.html')
	return HttpResponse(template.render(context,request))