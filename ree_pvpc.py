#!/usr/bin/env python2.7

import datetime
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
import sys
import time
import urllib2

tz = pytz.timezone("Europe/Madrid")
url = 'http://www.esios.ree.es/Solicitar?fileName=PVPC_CURV_DD_{0}&fileType=txt&idioma=es'

def get_data_for_day(dt):
    ref_time = time.mktime(dt.timetuple())
    day_str = dt.strftime("%Y%m%d")
    day_url = url.format(day_str)
    response_string = urllib2.urlopen(day_url)
    response = json.load(response_string)
    pvpc = response['PVPC']
    # PVPC is an array of dictionaries where every dictionary is:
    # {"Dia":"13/11/2015","Hora":"00-01",
    # "GEN":"126,08","NOC":"75,81","VHC":"79,94",
    # "COFGEN":"0,000075326953000000","COFNOC":"0,000158674625000000",
    # "COFVHC":"0,000134974129000000","PMHGEN":"66,35","PMHNOC":"63,98",
    # "PMHVHC":"66,63","SAHGEN":"6,14","SAHNOC":"5,92","SAHVHC":"6,17",
    # "FOMGEN":"0,03","FOMNOC":"0,03","FOMVHC":"0,03","FOSGEN":"0,13",
    # "FOSNOC":"0,12","FOSVHC":"0,13","INTGEN":"2,46","INTNOC":"2,37",
    # "INTVHC":"2,47","PCAPGEN":"6,94","PCAPNOC":"1,16","PCAPVHC":"1,64",
    # "TEUGEN":"44,03","TEUNOC":"2,22","TEUVHC":"2,88"}
    
    # Looking here: http://tarifaluzhora.es/ it seems that GEN is the main
    # electricity price, and it comes in thousandth of an euro.
        
    # It will send 25 hours at CEST to CET transition day.
    times = []
    values = []
    
    keys = [ 'GEN' ]
    # for every hour data in pvpc
    for res in pvpc:
        # TODO: check day value
        hour_offset = int( res['Hora'].split('-')[0] ) * 3600
        for k in keys:
            v = float( res[k].replace(',','.') ) # replace commas by dots
            dt = datetime.datetime.fromtimestamp( ref_time + hour_offset )
            dt = tz.localize( dt )
            times.append( dt )
            values.append( v * 0.001 )
    return pd.Series( data=np.array(values), index=np.array(times), name="GEN" )

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(days=n)

def generate_series(start_str, stop_str):
    start = tz.localize( datetime.datetime.strptime(start_str, "%Y%m%d") )
    stop = tz.localize( datetime.datetime.strptime(stop_str, "%Y%m%d") )
    dt = start
    ts_list = [ get_data_for_day(dt) for dt in daterange(start,stop + datetime.timedelta(days=1)) ]
    ts = pd.Series([],index=[],name="GEN").append( ts_list )
    return ts

if __name__ == "__main__":
    ts = generate_series(sys.argv[1], sys.argv[2])
    print ts.to_csv(None, header=True, index_label="datetime")
