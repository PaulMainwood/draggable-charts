import numpy as np
import pandas as pd
from pathlib import Path

def load_price_data(tokenizer_dir = '/opt/data/tokenizers/20250603-192806/tokenizer'):
    # Define the base directory
    tokenizer_dir = Path(tokenizer_dir)
    priceperiod_df = pd.read_csv(tokenizer_dir / 'priceperiod_counts.csv')
    priceperiod_dict = dict(zip(priceperiod_df['key'], priceperiod_df['value']))
    period_prices = np.load(tokenizer_dir / 'period_prices.npy')
    stockcode_df = pd.read_csv(tokenizer_dir / 'stockcode_counts.csv')
    sku_shares_df = pd.read_csv(tokenizer_dir / 'sku_shares.pandas_df')
    
    # Create mapping from stockcode to name, ensuring we only map the columns that exist in sku_shares
    stockcode_to_name = dict(zip(sku_shares_df['StockCode'], sku_shares_df['Name']))
    
    # Validate that the number of elements matches
    if len(priceperiod_dict) != len(period_prices):
        raise ValueError(
            f"Number of elements in priceperiod_dict ({len(priceperiod_dict)}) "
            f"does not match number of rows in period_prices ({len(period_prices)})"
        )
    
    # Validate that stockcode_counts and sku_shares have the same number of rows as period_prices columns
    if len(stockcode_df) != period_prices.shape[1]:
        raise ValueError(
            f"Number of rows in stockcode_counts ({len(stockcode_df)}) "
            f"does not match number of columns in period_prices ({period_prices.shape[1]})"
        )
    
    if len(sku_shares_df) + 1 != period_prices.shape[1]:
        raise ValueError(
            f"Number of rows in sku_shares ({len(sku_shares_df)}) "
            f"does not match number of columns in period_prices ({period_prices.shape[1]})"
        )
    
    return priceperiod_dict, period_prices, stockcode_df, sku_shares_df, stockcode_to_name

def create_price_periods_df(priceperiod_dict, period_prices, stockcode_df):
    # Create a list to store the data for each row
    rows = []
    
    # Get the stockcode keys in order
    stockcode_keys = stockcode_df['key'].tolist()
    print(f"Type of stockcode_keys: {type(stockcode_keys)}")
    print(f"Type of first element: {type(stockcode_keys[0])}")
    
    # Process each row in period_prices
    for i, (key, value) in enumerate(priceperiod_dict.items()):
        # Split the key into format and period, handling 'UNK' case
        if key == 'UNK':
            format_type = 'UNK'
            period = 0
        else:
            format_type, period = key.split('|')
        
        # Create a row dictionary with the basic columns
        row_dict = {
            'Format': format_type,
            'Price_period': int(period)
        }
        
        # Add the price data for each stockcode
        for j, stockcode in enumerate(stockcode_keys):
            row_dict[stockcode] = period_prices[i, j]
        
        rows.append(row_dict)
    
    # Create the DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure columns are in the correct order
    column_order = ['Format', 'Price_period'] + stockcode_keys
    df = df[column_order]
    
    # Sort by Format and Price_period
    df = df.sort_values(['Format', 'Price_period'])
    
    return df

def convert_df_back_to_period_prices(edited_df, priceperiod_dict, stockcode_df):
    """
    Convert an edited price periods DataFrame back to the original period_prices.npy format.
    
    Args:
        edited_df: DataFrame with edited price data (sorted by Format and Price_period)
        priceperiod_dict: Original dictionary mapping keys to values from priceperiod_counts.csv
        stockcode_df: DataFrame with stockcode information from stockcode_counts.csv
    
    Returns:
        numpy.ndarray: period_prices array in the original order
    """
    # Get the stockcode keys in order
    stockcode_keys = stockcode_df['key'].tolist()
    
    # Create a mapping from (Format, Price_period) to row index in the edited DataFrame
    # This allows us to look up the edited values by the original key structure
    format_period_to_row = {}
    for idx, row in edited_df.iterrows():
        format_type = row['Format']
        period = row['Price_period']
        
        # Handle 'UNK' case
        if format_type == 'UNK':
            key = 'UNK'
        else:
            key = f"{format_type}|{period}"
        
        format_period_to_row[key] = idx
    
    # Initialize the output array with the same shape as the original
    num_rows = len(priceperiod_dict)
    num_cols = len(stockcode_keys)
    period_prices = np.zeros((num_rows, num_cols))
    
    # Fill the array in the original order
    for i, (key, value) in enumerate(priceperiod_dict.items()):
        # Get the corresponding row from the edited DataFrame
        if key in format_period_to_row:
            edited_row_idx = format_period_to_row[key]
            edited_row = edited_df.iloc[edited_row_idx]
            
            # Extract the price values for each stockcode
            for j, stockcode in enumerate(stockcode_keys):
                period_prices[i, j] = edited_row[stockcode]
        else:
            raise ValueError(f"Key '{key}' not found in edited DataFrame")
    
    return period_prices

def save_updated_period_prices(edited_df, priceperiod_dict, stockcode_df, output_path):
    """
    Save an edited price periods DataFrame back to period_prices.npy format.
    
    Args:
        edited_df: DataFrame with edited price data (sorted by Format and Price_period)
        priceperiod_dict: Original dictionary mapping keys to values from priceperiod_counts.csv
        stockcode_df: DataFrame with stockcode information from stockcode_counts.csv
        output_path: Path where to save the new period_prices.npy file
    """
    # Convert the edited DataFrame back to the original format
    updated_period_prices = convert_df_back_to_period_prices(edited_df, priceperiod_dict, stockcode_df)
    
    # Save to the specified path
    output_path = Path(output_path)
    np.save(output_path, updated_period_prices)
    
    print(f"Updated period_prices saved to: {output_path}")
    print(f"Array shape: {updated_period_prices.shape}")

if __name__ == "__main__":
    priceperiod_dict, period_prices, stockcode_df, sku_shares_df, stockcode_to_name = load_price_data()
    price_periods_df = create_price_periods_df(priceperiod_dict, period_prices, stockcode_df)
    print("\nPrice Periods DataFrame:")
    print(price_periods_df.head())
    print("\nStockcode to Name mapping (first 5 items):")
    print(dict(list(stockcode_to_name.items())[:5])) 