# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 12:37:18 2020

@author: ewand
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import cloudpickle
import time


def containment_tests(data, checker, long_name='longitude', lat_name='latitude'):
  data = pd.DataFrame(data)
  points = gpd.GeoDataFrame(data.loc[:,[long_name,lat_name]], geometry=gpd.points_from_xy(data.loc[:,long_name], data.loc[:,lat_name])) #create a series of point objects representing location of events
    
  if points is not None:
    r = []
    i=1
    n_data = len(data)
    prog_scale = 100/len(data)
    progress_bar = st.progress(0)
    status_text = st.empty()
    start = time.time()
    for pt in points.geometry:
      j = int(np.ceil(i*prog_scale))
      progress_bar.progress(j)
      r.append(containment_checker(pt))
      if i % 10 == 1:
        elapsed = round(time.time()-start,ndigits=3)
        it_per_s = round(i/elapsed,ndigits=3)
        remaining = round((n_data - i)/it_per_s, ndigits=3)
      status_text.text(f'Progress: {i}/{n_data}, Time: {elapsed}s,\nit/s: {it_per_s}, Remaining: {remaining}s')
      i+=1
    #r = points.geometry.progress_apply(containment_checker)
    return np.any(r, axis=1)


#@st.cache
#def download_africapolis():
#  africapolis_url = 'http://www.africapolis.org/download/Africapolis_2015_shp.zip'
#  africapolis = gpd.read_file(africapolis_url)
#  polys = africapolis.geometry #This is a series of polygons
#  containment_checker = polys.geometry.buffer(0).contains
#  return containment_checker

st.write(os.listdir())

@st.chache
def load_africapolis():
  i = 0
  for filename in os.listdir('africapolis'):
    if i == 0:
      africapolis = gpd.read_file(os.path.join('africapolis', filename))
    else:
      africapolis = africapolis.append(gpd.read_file(os.path.join('africapolis', filename)))
    i+=1
  polys = africapolis.geometry #This is a series of polygons
  containment_checker = polys.geometry.buffer(0).contains
  return containment_checker

containment_checker = download_africapolis()
long_name = 'longitude'
lat_name = 'latitude'
isurban=None

data_file = st.file_uploader('Select your data file:', type=['csv', 'xlsx'])
#africapolis_file = st.file_uploader('Select your Africapolis file:', type=['shp'])

if data_file is not None:
  data = pd.read_csv(data_file).iloc[:100,:]
  if long_name not in data.columns or lat_name not in data.columns:
    long_name = st.selectbox('Please select the name of the Longitude column in your data', ['Please Select One']+list(data.columns))
    lat_name = st.selectbox('Please select the name of the Latitude column in your data', ['Please Select One']+list(data.columns))
  if long_name != 'Please Select One' and lat_name != 'Please Select One':
    st.write('Processing data now, this may take some time...')
    isurban = containment_tests(data=data, 
                                checker = containment_checker,
                                long_name=long_name,
                                lat_name=lat_name)
    
    if isurban is not None:
      st.write('Processing complete.')
      data['is_urban'] = isurban
      #data.to_csv(data_dir_, index=False)
      
