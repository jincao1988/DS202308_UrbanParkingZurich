# plot different parking tarif zones
import json
import pandas as pd
import plotly.express as px
import streamlit as st
import requests


#Getting the coordinates of the parking 
url = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Gebietseinteilung_Parkierungsgebuehren?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=tarifzonen"
response=requests.get(url)
tarif=response.json()
# file_path="./data/dav_tarifzonen.json"

# with open(file_path,'r') as tarif:
#     tarif = json.load(tarif)


data = pd.DataFrame({
    'region_id': ['1', '2', '3','4'],
    'value': [1, 1, 1,0],
})
data


fig = px.choropleth_mapbox(
    data,
    geojson=tarif,  # GeoJSON with region boundaries and properties
    locations="region_id",  # Identifier in your data
    featureidkey="properties.objectid",  # Identifier in GeoJSON matching your data
        color="value",  # Data values for coloring the regions
    color_continuous_scale="turbo",  # Choose a color scale
    mapbox_style="open-street-map",
    center={"lat": 47.373878, "lon": 8.545094},
    zoom=15,
    height=1000,
    width=1000,
    opacity=0.4
)

st.plotly_chart(fig)

