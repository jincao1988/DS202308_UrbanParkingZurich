import json
import pandas as pd
import plotly.express as px
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.request import urlopen
from pprint import pprint

from cmcrameri import cm
import numpy as np

################################################### input variables #####################################################################
# coorindates [x,y] indicates the targeted destination
st.title("Parking options in Zurich")


def get_geocode_from_address(address):
    endpoint = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    response = requests.get(endpoint, params=params)
    if response.status_code == 200 and response.json():
        location = response.json()[0]
        return float(location["lat"]), float(location["lon"])
    return None


address = st.text_input(
    "Where are you going? Enter your destination:",
    value="Heinrichstrasse 200, 8005 Zurich",
)
# address = "Heinrichstrasse 200, 8005 Zurich"  # Example address
coordinates = get_geocode_from_address(address)


if coordinates:
    # st.write(f"Latitude: {coordinates[0]}, Longitude: {coordinates[1]}")
    user_input_lat = coordinates[0]
    user_input_lon = coordinates[1]
else:
    st.write("Failed to get coordinates.")

###################################################obtain geo of on-street ############################## SCORING: Tim traffic score ############################


@st.cache_data
def read_data(path):
    return pd.read_csv(path)


file_path = "./data/processed/parking_spots_traffic_scores.csv"

df_park = read_data(file_path)

to_trans = {
    "Blaue Zone": "Blue Zone",
    "Weiss markiert": "White Zone",
    "Nur mit Geh-Behindertenausweis": "Disabled",
    "Nur für Taxi": "Only Taxi",
    "Für Reisecars": "Only Coaches",
    "Für Elektrofahrzeuge": "Only Electric vehicles",
    "Zeitweise Taxi, zeitweise Güterumschlag": "Temporary",
}

rename_dict = {
    "properties.id1": "property_id",
    "properties.parkdauer": "parking_duration",
    "properties.art": "parking_kind",
    "properties.gebuehrenpflichtig": "payed",
    "properties.objectid": "object_id",
    "geometry.coordinates": "coord",
}

df_park = df_park.rename(columns=rename_dict)

df_park = df_park.drop(["type", "geometry.type", "coord", "id", "object_id"], axis=1)
df_park.loc[df_park["payed"] == "nicht gebührenpflichtig", "payed"] = 0
df_park.loc[df_park["payed"] == "gebührenpflichtig", "payed"] = 1
for key in to_trans:
    df_park.loc[df_park["parking_kind"] == key, "parking_kind"] = to_trans[key]


#############################################obtain geo of parking houses - Timothycode##############################################################
geo_url2 = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Oeffentlich_zugaengliche_Parkhaeuser?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=poi_parkhaus_view"

with urlopen(geo_url2) as response:
    geo_data_house = json.load(response)

df = pd.json_normalize(geo_data_house, "features")

df["lon"] = df["geometry.coordinates"].apply(lambda row: row[0])
df["lat"] = df["geometry.coordinates"].apply(lambda row: row[1])

parkinghouse_trace = go.Scattermapbox(
    lat=df["lat"],
    lon=df["lon"],
    mode="markers",
    marker=dict(size=20),
    name="Park houses",
)

#######################################obtain tarifzones Jin code####################################################################################
url = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Gebietseinteilung_Parkierungsgebuehren?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=tarifzonen"
response = requests.get(url)
tarif = response.json()

data = pd.DataFrame(
    {
        "region_id": ["1", "2", "3", "4"],
        "region": [
            "Zürich-West",
            "Innenstadt und Oerlikon",
            "Innenstadt und Oerlikon",
            "suburban district",
        ],
        "value": ["high tarif", "high tarif", "high tarif", "low tarif"],
        "bedienungszeiten": [
            "Montag - Mittwoch, 9:00 - 20:00 Uhr, Donnerstag - Sonntag, 9:00 - 9:00 Uhr",
            "Montag - Samstag, 9:00 - 20:00 Uhr",
            "Montag - Samstag, 9:00 - 20:00 Uhr",
            "Montag - Samstag, 9:00 - 20:00 Uhr",
        ],
    }
)

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
    hover_data=["region", "value", "bedienungszeiten"],
)
tarifzones.update_coloraxes(showscale=False)

####################################plot added trace of on-street parking and parking houses ############################################################
# add radio to select show parking_kind in same marker but diff color,  or same color but different marker.

# show_plot = st.radio(
#     label='Choose display option of a parking spot ', options=['color', 'marker'])

# if show_plot == 'color':
# parking_colors= df_park['parking_kind'].unique()


def mpl_to_plotly(cmap, pl_entries=11, rdigits=2, reverse=False):
    # cmap - colormap
    # pl_entries - int = number of Plotly colorscale entries
    # rdigits - int -=number of digits for rounding scale values
    scale = np.linspace(0, 1, pl_entries)
    colors = (cmap(scale)[:, :3] * 255).astype(np.uint8)
    if reverse:
        colors = colors[::-1]
    pl_colorscale = [
        [round(s, rdigits), f"rgb{tuple(color)}"] for s, color in zip(scale, colors)
    ]
    pl_colorscale = [f"rgb{tuple(color)}" for color in colors]
    return pl_colorscale


def produe_marker_colors(values, color_scale=100):
    svalues = (values - min(values)) / (max(values) - min(values)) * (color_scale - 1)
    rdigits = int(np.log10(color_scale))
    cmap = mpl_to_plotly(cm.roma, pl_entries=color_scale, rdigits=rdigits, reverse=True)
    cindeces = [int(value) for value in svalues]
    return [cmap[ci] for ci in cindeces], cmap


# df_park["score"] = df_park["anzfahrzeuge"] / df_park["anzfahrzeuge"].sum()

parking_markers, cmap = produe_marker_colors(df_park["anzfahrzeuge"])

map_fig_onstreet = go.Scattermapbox(
    lat=df_park["lat"],
    lon=df_park["lon"],
    text=df_park.apply(
        lambda row: f"{row['parking_kind']} - {row['parking_duration']} minutes allowed",
        axis=1,
    ),
    mode="markers",
    name="On-street parking",
    marker=dict(
        size=10,
        # symbol='square',-> this just does not work.
        color=parking_markers,
        colorscale=cmap,
        showscale=True,
        cmin=0,
        cmax=1,
    ),
)

tarifzones.add_trace(map_fig_onstreet)


# map_fig_onstreet.update_layout(
#     mapbox_style="open-street-map",
#     mapbox_center={"lat": user_input_lat, "lon": user_input_lon},
#     mapbox_zoom=18,
# )


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

destination_trace = go.Scattermapbox(
    lat=[user_input_lat],
    lon=[user_input_lon],
    mode="markers",
    name="Destination",
    marker=dict(size=40),
    hovertemplate="Travel destination" + "<extra></extra>",
)
tarifzones.add_trace(destination_trace)


st.subheader("Display parking choices near to my destination")

if st.checkbox("Show parking houses in map"):
    tarifzones.add_trace(parkinghouse_trace)

st.plotly_chart(tarifzones)


################################### display data #######################################################
st.title("Data zone")

if st.checkbox("Show on-street parking data below"):
    sentence = f"On-street data sheet contains {df_park.shape[0]} rows and {df_park.shape[1]} columns data."
    st.write(sentence)
    df_park


if st.checkbox("Show parking house data below"):
    sentence = f"On-street data sheet contains {df.shape[0]} rows and {df.shape[1]} columns data."
    st.write(sentence)
    df

if st.checkbox("Show parking tarif zones data below"):
    sentence = f"On-street data sheet contains {data.shape[0]} rows and {data.shape[1]} columns data."
    st.write(sentence)
    data


# ################################### add destination circle############################################
# circle_center = (user_input_lat, user_input_lon)
# circle_radius = user_input_r
# m = folium.Map(location=circle_center, zoom_start=12)

# folium.Circle(
#     location=circle_center,
#     radius=circle_radius,
#     color='blue',  # Circle border color
#     fill=True,
#     fill_color='blue',  # Circle fill color
#     fill_opacity=0.3,  # Opacity of the circle fill
#     popup='My Circle'  # Popup text when clicking on the circle
# ).add_to(m)


#################################### input of places #################################
