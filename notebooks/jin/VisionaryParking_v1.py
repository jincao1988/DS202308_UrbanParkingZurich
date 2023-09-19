import json
import pandas as pd
import plotly.express as px
import streamlit as st
import requests

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.request import urlopen
#from googletrans import Translator, constants
from pprint import pprint
################################################### input variables #####################################################################
#coorindates [x,y] indicates the targeted destination

user_input_lat = st.number_input("Enter the latitude of your destination:", value=47.373878, step=0.001)
user_input_lon = st.number_input("Enter the lontitude of your destination:", value=8.545094, step=0.001)

user_input_lat
user_input_lon


###################################################obtain geo of on-street parking - Antonio code#####################################################################
#translator = Translator()
geo_url = 'https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Oeffentlich_zugaengliche_Strassenparkplaetze_OGD?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=view_pp_ogd'

with urlopen(geo_url) as response:
    geo_data = json.load(response)

to_trans = {'Blaue Zone': 'Blue Zone',
            'Weiss markiert': 'White Zone',
            'Nur mit Geh-Behindertenausweis': 'Disabled',
            'Nur für Taxi': 'Only Taxi',
            'Für Reisecars': 'Only Coaches',
            'Für Elektrofahrzeuge': 'Only Electric vehicles',
            'Zeitweise Taxi, zeitweise Güterumschlag': 'Temporary'}

df_park = pd.json_normalize(geo_data['features'])

rename_dict = { 'properties.id1' : 'property_id', 
                'properties.parkdauer' : 'parking_duration', 
                'properties.art' : 'parking_kind',
                'properties.gebuehrenpflichtig': 'payed', 
                'properties.objectid' : 'object_id',
                'geometry.coordinates': 'coord'}

df_park = df_park.rename(columns=rename_dict)

df_park[['lon', 'lat']] = pd.DataFrame(df_park.coord.to_list())
df_park = df_park.drop(['type', 'geometry.type', 'coord', 'id', 'object_id'], axis=1)
df_park.loc[df_park['needtopay'] == 'nicht gebührenpflichtig', 'payed'] = 0
df_park.loc[df_park['needtopay'] == 'gebührenpflichtig', 'payed'] = 1
for key in to_trans:
    df_park.loc[df_park['parking_kind'] == key, 'parking_kind'] = to_trans[key]

# df_park # display the table of on-street parking data

# map_fig = px.scatter_mapbox(df_park, lat='lat', lon='lon', color='parking_kind')
# map_fig.update_layout(
#     mapbox_style="open-street-map",
#     mapbox_zoom=13, 
#     mapbox_center = {"lat": 47.373878, "lon": 8.545094},
#     height=1000,
#     width=1000)

# st.plotly_chart(map_fig)

#############################################obtain geo of parking houses - Timothycode##############################################################
geo_url2 = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Oeffentlich_zugaengliche_Parkhaeuser?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=poi_parkhaus_view"

with urlopen(geo_url2) as response:
    geo_data_house = json.load(response)

df = pd.json_normalize(geo_data_house, "features")

df["lon"] = df["geometry.coordinates"].apply(lambda row: row[0])
df["lat"] = df["geometry.coordinates"].apply(lambda row: row[1])

parkinghouse_trace=go.Scattermapbox(
    lat = df["lat"],
    lon = df["lon"],
    mode = "markers",
    marker=dict(size=20),
    name='Park house'
    )

#######################################obtain tarifzones Jin code####################################################################################
url = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Gebietseinteilung_Parkierungsgebuehren?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=tarifzonen"
response=requests.get(url)
tarif=response.json()

data = pd.DataFrame({
    'region_id': ['1', '2', '3','4'],
    'region':['Zürich-West','Innenstadt und Oerlikon','Innenstadt und Oerlikon','suburban district'],
    'value': ['high tarif', 'high tarif', 'high tarif','low tarif'],
    'bedienungszeiten': ['Montag - Mittwoch, 9:00 - 20:00 Uhr, Donnerstag - Sonntag, 9:00 - 9:00 Uhr','Montag - Samstag, 9:00 - 20:00 Uhr','Montag - Samstag, 9:00 - 20:00 Uhr',
                         'Montag - Samstag, 9:00 - 20:00 Uhr']
})

################################################## Plotting ##########################################################################
####################################plot base map with choropleth############################################################
tarifzones = px.choropleth_mapbox(
    data,
    geojson=tarif,  # GeoJSON with region boundaries and properties
    locations="region_id",  # Identifier in your data
    featureidkey="properties.objectid",  # Identifier in GeoJSON matching your data
        color="value",  # Data values for coloring the regions
    color_continuous_scale="turbo",  # Choose a color scale
    mapbox_style="open-street-map",
    center={"lat": user_input_lat, "lon": user_input_lon},
    zoom=18,
    height=1000,
    width=1000,
    opacity=0.4,
    hover_data=['region', 'value','bedienungszeiten']
)
tarifzones.update_coloraxes(showscale=False)

####################################plot added trace of on-street parking and parking houses ############################################################
#add radio to select show parking_kind in same marker but diff color,  or same color but different marker.

# show_plot = st.radio(
#     label='Choose display option of a parking spot ', options=['color', 'marker'])

# if show_plot == 'color':
# for pk in df_park['parking_kind'].unique():
#     map_fig_onstreet = go.Scattermapbox(   
#         lat=df_park[df_park['parking_kind']==pk]['lat'], 
#         lon=df_park[df_park['parking_kind']==pk]['lon'], 
#         mode='markers',
#         name=pk,
#         marker=dict(size=10),
#         #hoverinfo='all',
#         #hoverinfo=
#     )


map_fig_onstreet = go.Scattermapbox(   
    lat=df_park['lat'], 
    lon=df_park['lon'], 
    mode='markers',
    name='parking_kind',
    marker=dict(size=10),
        #hoverinfo='all',
        #hoverinfo=
)
tarifzones.add_trace(map_fig_onstreet)
# else:#this part does not yet work.
#     for pk in df_park['parking_kind'].unique():
#         map_fig_onstreet = go.Scattermapbox(   
#             lat=df_park[df_park['parking_kind']==pk]['lat'], 
#             lon=df_park[df_park['parking_kind']==pk]['lon'], 
#             mode='markers',
#             marker=dict(size=10,symbol=pk),
#             name=pk,
#             )
#         tarifzones.add_trace(map_fig_onstreet)

tarifzones.add_trace(parkinghouse_trace)

destination_trace = go.Scattermapbox(
    lat=[user_input_lat], 
    lon=[user_input_lon], 
    mode='markers', 
    name='Destination',
    marker=dict(size=40),
    hovertemplate="Travel destination"+"<extra></extra>"
    )
tarifzones.add_trace(destination_trace)

st.plotly_chart(tarifzones)


################################### display data #######################################################
if st.checkbox('Show on-street parking data below'):
    sentence=f"On-street data sheet contains {df_park.shape[0]} rows and {df_park.shape[1]} columns data."
    st.write(sentence)
    df_park
    

if st.checkbox('Show parking house data below'):
    sentence=f"On-street data sheet contains {df.shape[0]} rows and {df.shape[1]} columns data."
    st.write(sentence)
    df

if st.checkbox('Show parking tarif zones data below'):
    sentence=f"On-street data sheet contains {data.shape[0]} rows and {data.shape[1]} columns data."
    st.write(sentence)
    data