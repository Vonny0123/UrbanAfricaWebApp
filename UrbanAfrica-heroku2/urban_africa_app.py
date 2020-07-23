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
from io import BytesIO
image = Image.open('AfricaPolis_cropped.jpg')

st.image(image, caption='', use_column_width=True)

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
        elapsed_num = time.time()-start
        elapsed_sec = time.gmtime(elapsed_num)
        elapsed = time.strftime("%M:%S", elapsed_sec)
        it_per_s = round(i/elapsed_num,ndigits=3)
        remaining_sec = time.gmtime((n_data - i)/it_per_s)
        remaining = time.strftime("%M:%S", remaining_sec)
      status_text.text(f'Progress: {i}/{n_data}, Time: {elapsed},\nit/s: {it_per_s}, Remaining: {remaining}')
      i+=1
    #r = points.geometry.progress_apply(containment_checker)
    return np.any(r, axis=1)


@st.cache
def download_africapolis():
  africapolis_url = 'http://www.africapolis.org/download/Africapolis_2015_shp.zip'
  africapolis = gpd.read_file(africapolis_url)
  polys = africapolis.geometry #This is a series of polygons
  containment_checker = polys.geometry.buffer(0).contains
  return containment_checker

"""
# Urban Labeller

This web application will label entries in a dataset as urban or rural based on latitude and longitude using the Africapolis dataset. 
Once the Africapolis data has been loaded, you will be prompted to select your dataset (csv or xlsx) using the file explorer. Processing will then happen automatically. You will then be prompted to download the processed data, right-click the link and select save-as to save the data in your desired location. 
"""


containment_checker = download_africapolis()
long_name = 'longitude'
lat_name = 'latitude'
isurban=None

data_file = st.file_uploader('Select your data file:', type=['csv', 'xlsx'])
#africapolis_file = st.file_uploader('Select your Africapolis file:', type=['shp'])

if data_file is not None:
  data = pd.read_csv(data_file)
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
      #csv = data.to_csv(index=False)
            
      def download_link(object_to_download, download_filename, download_link_text):
        """
        Generates a link to download the given object_to_download.
    
        object_to_download (str, pd.DataFrame):  The object to be downloaded.
        download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
        download_link_text (str): Text to display for download link.
    
        Examples:
        download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
        download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')
    
        """
        if isinstance(object_to_download,pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)
    
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'
        
      data_download = download_link(data, 'processed_data.csv', 'Click to download data')
      
      st.markdown(data_download, unsafe_allow_html=True)
