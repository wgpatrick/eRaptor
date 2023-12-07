# example/st_app.py

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

import pandas as pd
import random
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

# app title
st.title("NBA Raptor Data from Neil Paine")

st.header("Filter Player Data!", divider="rainbow")

# Define filter dataframe code
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter data on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

# Get all values from the worksheet
url = 'https://docs.google.com/spreadsheets/d/1CsPkNuDvHunzTiNeqSq_QC9Nr2f4Ioco2wUggJ9VQsI/edit#gid=1113356622'
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet=url, skiprows=0, index_col=0,header=1)

#Create the filtered dataframe
df = filter_dataframe(data)
st.dataframe(df)

#Create Scatter Plot
st.header("Create 2x2 Plot", divider="rainbow")
circle_color = st.selectbox("Select Circle Color", df.columns,index=11)
fig = px.scatter(df, x='eRO',y='eRD',hover_name='Player', color=circle_color,
                 title="Offensive eRaptor vs Defensive eRaptor for Both Playoffs and Regular Season")
st.plotly_chart(fig, theme="streamlit", use_container_width=True)

#Player Comparison

st.header("Player Comparison", divider="rainbow")

player_1 = st.selectbox("Select Player 1",df['Player'].unique(),
                        help="Select a player! It's set to a random player to start.")
player_2 = st.selectbox("Select Player 2",df['Player'].unique(),
                        help="Select a player! It's set to a random player to start.")

player_data_1 = df[df['Player']==player_1]
player_data_1_RS = player_data_1[player_data_1['Type']=='RS']
player_data_1_PO = player_data_1[player_data_1['Type']=='PO']

player_data_2 = df[df['Player']==player_2]
player_data_2_RS = player_data_2[player_data_2['Type']=='RS']
player_data_2_PO = player_data_2[player_data_2['Type']=='PO']

comparison_data_RS = [player_data_1_RS, player_data_2_RS]
players_data_RS = pd.concat(comparison_data_RS)
comparison_data_PO = [player_data_1_PO, player_data_2_PO]
players_data_PO = pd.concat(comparison_data_PO)


fig2=px.line(players_data_RS,x='Age',y='eRT',hover_name='Year', color='Player',
             title="Regular Season eRaptor (eRT) by Age")
st.plotly_chart(fig2,theme="streamlit",use_container_width=True)
fig3=px.line(players_data_PO,x='Age',y='eRT',hover_name='Year', color='Player',
             title="Playoffs Raptor (eRT) by Age")
st.plotly_chart(fig3,theme="streamlit",use_container_width=True)
