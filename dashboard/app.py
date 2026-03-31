# Create a Streamlit dashboard to visualize the crime data

#-----------------------------------------------------

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

#-----------------------------------------------------
# Dashbord Configuration
st.set_page_config(
    layout="wide")

st.title("Austin Crime Dashboard")
st.markdown("Explore crime patterns across different APD sectors in Austin, TX from January 1, 2022 to March 7, 2026")

#-----------------------------------------------------

# Load Data
@st.cache_data # Cache the data loading function for better performance
def load_data():
    df = pd.read_csv("data/austin_crime_preprocessed.csv",
                     parse_dates=["occurred_date_time", "report_date_time"])
    return df

df = load_data()

#-----------------------------------------------------
# in terminal ran: streamlit run dashboard/app.py to run the dashboard and test live app
#-----------------------------------------------------

# Add sidebar filters
st.sidebar.header("Filter Options")

selected_sector = st.sidebar.selectbox(
    "Select APD Sector",
    ["All"] + sorted(df["sector_name_clean"].unique().tolist())
)

# how to apply filter selected
if selected_sector == "All":
    filtered_df = df
else:
    filtered_df = df[df["sector_name_clean"] == selected_sector]

#-----------------------------------------------------

# Add KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Crimes", f"{len(filtered_df):,}")
col4.metric("Most Common Crime", 
            filtered_df["highest_offense_description"].mode()[0])
col2.metric("Unique Crime Types",
            filtered_df["highest_offense_description"].nunique())
col3.metric("Average Reporting Delay (hrs)",
            round(((filtered_df["report_date_time"] - filtered_df["occurred_date_time"]).dt.total_seconds() / 86400).mean(), 2))

st.markdown("---")

#-----------------------------------------------------

# Add Interactive Visualizations via Plotly

import plotly.express as px
#-----------------------------------------------------

## Sector Comparison Map

st.header("Crime by Sector (Map)")

# Load GeoJSON for APD sectors
@st.cache_data
def load_geojson():
    import json
    with open("data/apd_sectors.geojson") as f:
        return json.load(f)

geojson = load_geojson()

# Aggregate crime counts by sector
sector_counts = df["sector_name_clean"].value_counts().to_dict()

# Add crime counts to GeoJSON properties
for feature in geojson["features"]:
    sector = feature["properties"]["sector_name_clean"]
    feature ["properties"]["crime_count"] = sector_counts.get(sector, 0)

# create style function and highlight selected sectors
def style_function(feature):
    sector = feature["properties"]["sector_name_clean"]
    if selected_sector != "All" and sector == selected_sector:
        return {
            "fillColor": "red",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.7
        }
    return {
        "fillColor": "blue",
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.5
    }

# create interactive map via folium
map = folium.Map(
    location=[30.2672, -97.7431], 
    zoom_start=11,
    tiles="cartodbpositron" #"cartodbpositron" is a light, clean basemap that works well for overlaying data
)

# add GeoJson layer with crime counts and tooltips
folium.GeoJson(
    geojson,
    style_function = style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["sector_name_clean", "crime_count"],
            aliases=["Sector:", "Total Crimes"],
            localize=True
        )
    ).add_to(map)


# Display map in Streamlit
st_folium(map, width=1050, height=600)

st.markdown("---")
#-----------------------------------------------------

st.header("Time Analysis")

col1, col2 = st.columns(2)

## Crime by Hour
hourly = filtered_df.groupby("hour").size().reset_index(name="count")

fig_hourly = px.line(
    hourly,
    x="hour",
    y="count",
    title="Crime by Hour"
)

fig_hourly.update_layout(template = "plotly_white")


## Crime by Weekday
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

weekday = (
    filtered_df["weekday"].value_counts().reindex(weekday_order).reset_index())

weekday.columns = ["weekday", "count"]

fig_weekday = px.bar(
    weekday,
    x="weekday",
    y="count",
    title="Crime by Weekday"
)

fig_weekday.update_layout(template = "plotly_white")

with col1:
    st.plotly_chart(fig_hourly, use_container_width = True, key="hourly")
    
with col2:
    st.plotly_chart(fig_weekday, use_container_width = True, key="weekday")
    
st.markdown("---")

#-----------------------------------------------------

## Top 10 Crime Offense Types

st.header("Crime Distribution")
col1, col2 = st.columns(2)

# top crimes
top_crimes = (    
    filtered_df["highest_offense_description"]
    .value_counts()
    .head(10)
    .reset_index()
)

top_crimes.columns = ["offense", "count"]

fig_top = px.bar(
    top_crimes,
    x="count",
    y="offense",
    orientation='h',
    title="Top 10 Crime Offense Types"
)

fig_top.update_layout(template="plotly_white", yaxis={"categoryorder":"total ascending"})

# crime by sector
sector_counts = df["sector_name_clean"].value_counts().reset_index()
sector_counts.columns = ["sector", "count"]

fig_sector = px.bar(
    sector_counts,
    x="sector",
    y="count",
    title="Crime by Sector"
)

fig_sector.update_layout(template="plotly_white")

with col1:
    st.plotly_chart(fig_top, use_container_width = True, key="top_crimes")

with col2:
    st.plotly_chart(fig_sector, use_container_width = True, key="sector")

st.markdown("---")
#-----------------------------------------------------

# Display data table
st.header("Crime Data Table")
st.dataframe(filtered_df.sample(1000), use_container_width=True)
#-----------------------------------------------------