# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 12:37:18 2020

@author: ewand
"""

import base64
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import time
from PIL import Image
import jellyfish
import datetime

image = Image.open('AfricaPolis_cropped.jpg')

#st.image(image, caption='', use_column_width=True)
#st.sidebar.image(image, caption='', use_column_width=True)


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
    iter_time = time.time()
    for pt in points.geometry:
      j = int(np.ceil(i*prog_scale))
      progress_bar.progress(j)
      r.append(containment_checker(pt))
      if i % 50 == 1:
        elapsed_num = time.time()-start
        elapsed_sec = time.gmtime(elapsed_num)
        elapsed = time.strftime("%M:%S", elapsed_sec)
        it_per_s = round(50/(time.time()-iter_time),ndigits=1)
        remaining_sec = time.gmtime((n_data - i)/it_per_s)
        remaining = time.strftime("%M:%S", remaining_sec)
        iter_time = time.time()
      status_text.text(f'Progress: {i}/{n_data}, Time: {elapsed},\nit/s: {it_per_s}, Remaining: {remaining}')
      i+=1
    #r = points.geometry.progress_apply(containment_checker)
    return np.any(r, axis=1)


@st.cache
def download_africapolis():
  africapolis_url = 'http://www.africapolis.org/download/Africapolis_2015_shp.zip'
  africapolis = gpd.read_file(africapolis_url)
  return africapolis

@st.cache
def process_africapolis(africapolis):
  polys = africapolis.geometry #This is a series of polygons
  containment_checker = polys.geometry.buffer(0).contains
  return containment_checker

def check_valid_country(string, valid_list):
  sim_metrics = [jellyfish.levenshtein_distance(string, valid_country) for valid_country in valid_list]
  valid_list_sorted = [x for _, x in sorted(zip(sim_metrics,valid_list), key=lambda pair: pair[0])]
  if string not in [_ for _ in valid_list]:
    valid_string = st.sidebar.selectbox(f'*{string.upper()}* does not appear in the AfricaPolis dataset. Please select the corresponding country name.', ['Please Select One', 'My country is missing!']+list(valid_list_sorted))
  else:
    valid_string = string
  return valid_string

def download_link(object_to_download, download_filename, download_link_text):
  if isinstance(object_to_download,pd.DataFrame):
      object_to_download = object_to_download.to_csv(index=False)

  # some strings <-> bytes conversions necessary here
  b64 = base64.b64encode(object_to_download.encode()).decode()
  return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


"""
# Urban Africa Labelling

This web application will label entries in a dataset as urban or rural based on latitude and longitude using the AfricaPolis dataset. 

Once the AfricaPolis data has been loaded, you will be prompted to select your dataset (csv or xlsx) using the file explorer. Processing will then happen automatically. You will then be prompted to download the processed data, simply click the link to start the download.

Please note that there are some gaps in the AfricaPolis database, for example Madagascar not being covered. If this is a concern, check which countries are covered in the Country Data link at https://www.africapolis.org/data 
"""


africapolis = download_africapolis()
long_name = 'longitude'
lat_name = 'latitude'
isurban=None

st.sidebar.markdown('### Provide input when prompted:')

data_file = st.sidebar.file_uploader('Select your data file:', type=['csv', 'xlsx'])


if data_file is not None:
  data = pd.read_csv(data_file)
  st.write(data.head(5))
  filter_countries = st.sidebar.selectbox("Does your dataset have a 'Country' attribute?", ['Please Select One', 'Yes', 'No'])
  if filter_countries != 'Please Select One':
    filter_countries = (filter_countries == 'Yes')
    
    filtering_done = False
    if filter_countries:
      if 'country' not in data.columns:
        country_col = st.sidebar.selectbox('Please enter the name of the Country column.', ['Please Select One']+list(data.columns))
      else:
        country_col = 'country'
      
      if country_col != 'Please Select One':
          
        countries = [country.upper() for country in np.unique(data[country_col])]
        
        countries_url = 'http://www.africapolis.org/download/Africapolis_country.xlsx'
        countries_data = pd.read_excel(countries_url, skiprows=15)
        iso_lookup = dict(zip([string.upper() for string in countries_data.Country], countries_data.ISO))
        
        valid_countries = list()
        for country in countries:
          valid_country = check_valid_country(country.upper(), iso_lookup.keys())
          if valid_country == 'My country is missing!':
            continue
          else:
            valid_countries.append(valid_country)
        if 'Please Select One' not in valid_countries:
          iso_list = [iso_lookup[country] for country in valid_countries]
          bools = [iso in iso_list for iso in africapolis.ISO]
          africapolis = africapolis[bools]
          filtering_done = True
    else: 
      filtering_done = True
        
    if filtering_done:
      containment_checker = process_africapolis(africapolis)
      
      if long_name not in data.columns or lat_name not in data.columns:
        long_name = st.sidebar.selectbox('Please select the name of the Longitude column in your data', ['Please Select One']+list(data.columns))
        lat_name = st.sidebar.selectbox('Please select the name of the Latitude column in your data', ['Please Select One']+list(data.columns))
      if long_name != 'Please Select One' and lat_name != 'Please Select One':
        st.write('Processing data now, this may take some time...')
        isurban = containment_tests(data=data, 
                                    checker = containment_checker,
                                    long_name=long_name,
                                    lat_name=lat_name)
        
        if isurban is not None:
          #st.balloons()
          st.success('Processing complete.')
          data['is_urban'] = isurban                
          
          data_download = download_link(data, f'urban-africa-downloads-{str(datetime.datetime.now())}.csv', 'Click to Download Data')
          
          st.markdown(data_download, unsafe_allow_html=True)
