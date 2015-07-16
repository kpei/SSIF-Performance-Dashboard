from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.template import RequestContext, loader
from data.models import *
import datetime as dt
import json
import pandas as pd
import numpy as np

#since epoch milliseconds
def unix_time(dte):
    epoch = dt.datetime.utcfromtimestamp(0)
    delta = dte - epoch
    return delta.total_seconds() * 1000.0

def index(request):
    # Calculate Portfolio Statistics
    rf = 0.0 #LOL RATES
    r_p = Portfolio().getReturns()
    r = r_p['return']
    er = np.mean(r)*252*100 # Mean Annualized Return from daily
    sigma = (np.std(r)*np.sqrt(252))*100 # Annualized Standard Deviation
    sharpe = (er-rf)/sigma

    # Benchmark Calculations
    # ASSUMPTION: Benchmark is hardcoded as 65% US SPX, 35% CN TSX
    w = [0.65, 0.35]
    benchmark = Asset.objects.filter(industry__exact = 'Index')
    # get returns according to available portfolio dates
    rmat = pd.merge(pd.DataFrame(benchmark[0].getReturns()), pd.DataFrame(benchmark[1].getReturns()), on='date')
    rmat = pd.merge(pd.DataFrame(r_p), rmat, on='date')
    rmat = rmat.iloc[:,1:] # Remove Date column
    r_b = np.dot(rmat.iloc[:, 1:], w) # Calculate Benchmark
    r = rmat.iloc[:, 0]
    beta = np.cov(r,r_b)[0,1]/np.var(r_b) # Beta
    alpha = (np.mean(r) - np.mean(r_b)*beta)*100*252

    # Template and output
    template = loader.get_template('dashboard/index.html')
    context = RequestContext(request, {
        'portfolioStartDate': dt.datetime.strftime(Portfolio.objects.all().order_by('date')[0].date, '%B %d, %Y'),
        'avgRet': round(er, 2),
        'vola': round(sigma, 2),
        'sharpe': round(sharpe,2),
        'alpha': round(alpha, 2),
        'beta': round(beta,2)
    })

    return HttpResponse(template.render(context))

def portfoliojson(request):
    # Template and output
    p = list(Portfolio.objects.all().order_by('date').values('date', 'value', 'cash'))
    # Adhere to ISO8601
    e = []
    for i,dp in enumerate(p):
        e.append([ unix_time(dp['date']), round(dp['value']+dp['cash'])])

    return JsonResponse(e, safe=False)
