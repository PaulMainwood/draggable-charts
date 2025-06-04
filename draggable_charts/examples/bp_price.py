import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

from draggable_charts import line_chart
from utils.load import load_price_data, create_price_periods_df

st.set_page_config(layout="centered")

st.header("Pricing")

# Load the data using our new functions
priceperiod_dict, period_prices, stockcode_df, sku_shares_df, stockcode_to_name = load_price_data()
price_periods_df = create_price_periods_df(priceperiod_dict, period_prices, stockcode_df)

# Get unique formats for the dropdown
formats = sorted(price_periods_df['Format'].unique().tolist())

# Create dropdowns for format and product selection
selected_format = st.selectbox(
    "Select a format",
    options=formats
)

# Filter the stockcode_to_name dict to only include names (values)
product_names = sorted(list(stockcode_to_name.values()))

selected_product = st.selectbox(
    "Select a product",
    options=product_names
)

# Get the stockcode for the selected product name
selected_stockcode = [k for k, v in stockcode_to_name.items() if v == selected_product][0]

# Filter the dataframe by selected format
filtered_df = price_periods_df[price_periods_df['Format'] == selected_format]

# Get the selected column data
selected_data = filtered_df[selected_stockcode].values

# Create the initial data with the selected column
initial_data = pd.DataFrame({
    "new_price": selected_data,
    "original_price": selected_data.copy(),  # Make a copy for the original price
})

# Create dates for the x-axis
start_date = datetime(2023, 1, 3)
dates = [start_date + timedelta(weeks=i) for i in range(len(initial_data))]
initial_data["index"] = dates

initial_data = initial_data.set_index("index")
initial_data.index = initial_data.index.astype(str)

plot_options = {
    "title": f"Pricing plot for {selected_product} ({selected_format})", 
    "colors": ['#ff0909', '#d3d3d3'],
    "x_label": "Week",
    "y_label": "Price",
    "x_grid": True,
    "y_grid": True,
    'legend_position': 'top',
    'legend_align': 'center',
    'tension': 0.4,
    'fill_gaps': False,
    'fixed_lines': ["original_price"],
    'labels': {"new_price": "New price", "original_price": "Original price"},
    "point_radius": [3, 3],
    "border_dash": [(0, 0), (5, 5)],
    "x_type": "date",
    "x_format": "%d/%m",
    "y_format": "$.2f",
    "y_min": 0, 
}

new_data = line_chart(data=initial_data, options=plot_options, key="Price chart")
new_data
