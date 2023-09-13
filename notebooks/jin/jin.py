# plot different parking tarif zones
import json
import pandas as pd
import plotly.express as px


# Getting the coordinates of the parking 

with open("./ParkingPrice/data/dav.tarifzonen.json") as tarif:
    tarif = json.load(tarif)

tarif["features"][0]

tarif['geometry.coordinates'][0][0][0]

# for i in range(4):
#     tarif['geometry.coordinates'][i][]
#     lat=lat.append()

data = pd.DataFrame({
    'region_id': ['1', '2', '3','4'],
    'value': [1, 0, 0,0],
})
data


fig = px.choropleth_mapbox(
    data,
    geojson=tarif,  # GeoJSON with region boundaries and properties
    locations="region_id",  # Identifier in your data
    featureidkey="properties.objectid",  # Identifier in GeoJSON matching your data
        color="value",  # Data values for coloring the regions
    color_continuous_scale="Viridis",  # Choose a color scale
    mapbox_style="carto-positron",
    center={"lat": 47, "lon": 8.33},
    zoom=2
)
fig.show()
