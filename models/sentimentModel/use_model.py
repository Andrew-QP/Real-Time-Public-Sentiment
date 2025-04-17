"""
This utility file allows using a pre-trained sentiment-enhanced stock prediction model without retraining.
"""
import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from config import config
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler

def convert_to_numeric(value):
    """Convert string values like '1.3K' to numeric values (1300)"""
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return 0.0
        
    # Remove any commas
    value = value.replace(',', '')
    
    # Check for K, M, B suffixes
    if 'K' in value or 'k' in value:
        return float(value.replace('K', '').replace('k', '')) * 1000
    elif 'M' in value or 'm' in value:
        return float(value.replace('M', '').replace('m', '')) * 1000000
    elif 'B' in value or 'b' in value:
        return float(value.replace('B', '').replace('b', '')) * 1000000000
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

def list_available_models(directory=None):
    """
    List all available trained models in the versions directory
    
    Args:
        directory (str, optional): Directory to search. 
                                If None, uses default versions directory
    
    Returns:
        list: List of model file paths
    """
    if directory is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(script_dir, "saved_versions")
    
    if not os.path.exists(directory):
        print(f"Versions directory {directory} not found.")
        return []
    
    model_files = [f for f in os.listdir(directory) if f.endswith('.h5')]
    model_files.sort(reverse=True)  # Sort newest first
    
    if not model_files:
        print("No trained models found in the versions directory.")
        return []
    
    print("Available trained models:")
    for i, model_file in enumerate(model_files):
        print(f"{i+1}. {model_file}")
    
    return [os.path.join(directory, f) for f in model_files]

def get_latest_data(limit=None):
    """
    Get the most recent data for prediction
    
    Args:
        limit (int, optional): Number of rows to retrieve. If None, gets all data for the latest day.
        
    Returns:
        pd.DataFrame: DataFrame with the latest data
    """
    # Connect to database
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, config["db_path"]))
    print(f"Loading database from: {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    # First try simply getting the most recent data
    financial_features = ", ".join(config["use_financial_features"])
    sentiment_features = ", ".join(config["use_sentiment_features"])
    engagement_features = ", ".join(config["use_engagement_features"])
    
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    
    # Simple query to get the most recent data
    query = f"""
        SELECT createdDate, 
               {financial_features}, 
               {sentiment_features}, 
               {engagement_features}
        FROM tweets 
        WHERE {config["target_column"]} IS NOT NULL
        ORDER BY createdDate DESC
        {limit_clause}
    """
    
    df = pd.read_sql_query(query, conn)
    
    if len(df) == 0:
        print("No data found in database.")
        conn.close()
        return pd.DataFrame()
    
    # Convert time column to datetime
    df['createdDate'] = pd.to_datetime(df['createdDate'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    
    # Sort by created date (ascending)
    df = df.sort_values('createdDate')
    
    # Convert engagement features from strings to numeric values
    for feature in config["use_engagement_features"]:
        df[feature] = df[feature].apply(convert_to_numeric)
    
    print(f"Successfully loaded {len(df)} rows of data for {df['createdDate'].dt.date.iloc[0] if len(df) > 0 else 'unknown date'}")
    
    conn.close()
    return df

def predict_next_10_minutes(model_path=None, sequence_data=None):
    """
    Make predictions for the next 10 minutes using a pre-trained model
    
    Args:
        model_path (str): Path to the saved model. If None, uses latest model.
        sequence_data (np.ndarray, optional): Custom input sequence
                                            If None, uses latest data
    
    Returns:
        float: Predicted price
    """
    # List available models if no model path provided
    if model_path is None:
        models = list_available_models()
        if not models:
            print("No trained models found. Please train a model first.")
            return None
        model_path = models[0]  # Use the latest model
    
    # Load the model
    model = load_model(model_path)
    print(f"Successfully loaded model from {model_path}")
    
    # If no custom data provided, load the latest data
    if sequence_data is None:
        # Get the latest data
        df = get_latest_data(limit=config["sequence_length"])
        
        # Prepare features
        all_features = (
            config["use_financial_features"] + 
            config["use_sentiment_features"] + 
            config["use_engagement_features"]
        )
        
        # Apply feature weights
        weighted_df = df.copy()
        for feature in config["use_financial_features"]:
            weighted_df[feature] = weighted_df[feature] * config["financial_weight"]
        
        for feature in config["use_sentiment_features"]:
            weighted_df[feature] = weighted_df[feature] * config["sentiment_weight"]
        
        for feature in config["use_engagement_features"]:
            weighted_df[feature] = weighted_df[feature] * config["engagement_weight"]
        
        # Prepare sequence data
        sequence_length = config["sequence_length"]
        if len(df) < sequence_length:
            print(f"Warning: Only {len(df)} samples available, {sequence_length} required. Padding with first record.")
            # Pad with the first available record
            first_data = weighted_df[all_features].iloc[0].values
            padding = np.tile(first_data, (sequence_length - len(df), 1))
            sequence_data = np.vstack((padding, weighted_df[all_features].values))
        else:
            sequence_data = weighted_df[all_features].values[-sequence_length:]
        
        # Reshape for model input (batch_size, sequence_length, features)
        sequence_data = np.expand_dims(sequence_data, axis=0)
    
    # Create scalers
    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()
    
    # For simplicity, fit scalers on the available data
    # In a more refined version, you'd save and load the scalers with the model
    feature_data_flat = sequence_data.reshape(-1, sequence_data.shape[-1])
    feature_scaler.fit(feature_data_flat)
    
    # Scale input sequence
    sequence_data_scaled = feature_scaler.transform(feature_data_flat)
    sequence_data_scaled = sequence_data_scaled.reshape(1, config["sequence_length"], len(all_features))
    
    # Fit target scaler on the target column values from the data
    target_values = df[config["target_column"]].values.reshape(-1, 1)
    target_scaler.fit(target_values)
    
    # Make prediction
    prediction_scaled = model.predict(sequence_data_scaled, verbose=0)[0][0]
    
    # Convert prediction back to original scale
    prediction = target_scaler.inverse_transform([[prediction_scaled]])[0][0]
    
    # Get the latest actual price for comparison
    latest_price = df[config["target_column"]].iloc[-1]
    
    print(f"\nCurrent {config['target_column']}: ${latest_price:.2f}")
    print(f"Predicted {config['target_column']} (10 minutes ahead): ${prediction:.2f}")
    print(f"Predicted change: ${prediction - latest_price:.2f} ({((prediction - latest_price) / latest_price) * 100:.2f}%)")
    
    return prediction

def visualize_prediction(model_path, interval=10):
    """
    Visualize predictions vs actual values for a full day
    
    Args:
        model_path (str): Path to the model file
        interval (int): Time interval between points to plot (in minutes)
    """
    # Load the model
    model = load_model(model_path)
    
    # Extract timestamp from the model filename
    model_filename = os.path.basename(model_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load full day of data
    df = get_latest_data(limit=1000)  # Get a large amount of data
    
    if len(df) == 0:
        print("No data available for visualization.")
        return
    
    if len(df) < config["sequence_length"]:
        print(f"Not enough data points for prediction. Need at least {config['sequence_length']} points.")
        return
        
    # Prepare features
    all_features = (
        config["use_financial_features"] + 
        config["use_sentiment_features"] + 
        config["use_engagement_features"]
    )
    
    # Apply feature weights
    weighted_df = df.copy()
    for feature in config["use_financial_features"]:
        weighted_df[feature] = weighted_df[feature] * config["financial_weight"]
    
    for feature in config["use_sentiment_features"]:
        weighted_df[feature] = weighted_df[feature] * config["sentiment_weight"]
    
    for feature in config["use_engagement_features"]:
        weighted_df[feature] = weighted_df[feature] * config["engagement_weight"]
    
    # Create scalers - train on the ENTIRE dataset for consistency
    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()
    
    # Fit feature scaler on all feature data
    all_feature_data = weighted_df[all_features].values
    feature_scaler.fit(all_feature_data)
    
    # Fit target scaler on all target data
    target_values = df[config["target_column"]].values.reshape(-1, 1)
    target_scaler.fit(target_values)
    
    # Make predictions for each point in the series
    predictions = []
    actual_values = []
    timestamps = []
    
    sequence_length = config["sequence_length"]
    
    # Skip the first sequence_length points since we need that many points to make the first prediction
    for i in range(sequence_length, len(df)):
        # Get the sequence
        sequence = weighted_df[all_features].iloc[(i-sequence_length):i].values
        
        # Scale the sequence using the consistent scalers
        sequence_flat = sequence.reshape(-1, len(all_features))
        sequence_scaled = feature_scaler.transform(sequence_flat)
        sequence_scaled = sequence_scaled.reshape(1, sequence_length, len(all_features))
        
        # Make prediction
        prediction_scaled = model.predict(sequence_scaled, verbose=0)[0][0]
        prediction = target_scaler.inverse_transform([[prediction_scaled]])[0][0]
        
        # Get the actual value (use the i+1 index to match the 10-minute prediction horizon)
        actual_idx = min(i+1, len(df)-1)  # Avoid index out of bounds
        
        predictions.append(prediction)
        actual_values.append(df[config["target_column"]].iloc[actual_idx])
        timestamps.append(df['createdDate'].iloc[i])
    
    # If we don't have enough points, just use all points
    if len(timestamps) <= 10:
        interval_indices = list(range(len(timestamps)))
        interval_timestamps = timestamps
    else:
        # Filter data to show points at specified intervals (about 20 points for readability)
        interval_indices = list(range(0, len(timestamps), max(1, len(timestamps) // 20)))
        
        # Make sure the last point is included
        if len(timestamps) - 1 not in interval_indices:
            interval_indices.append(len(timestamps) - 1)
            
        interval_timestamps = [timestamps[i] for i in interval_indices]
    
    # Calculate metrics for displayed data
    mse = np.mean((np.array(actual_values) - np.array(predictions))**2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(np.array(actual_values) - np.array(predictions)))
    r2 = 1 - (np.sum((np.array(actual_values) - np.array(predictions))**2) / 
              np.sum((np.array(actual_values) - np.mean(np.array(actual_values)))**2))
    
    print(f"\nVisualization Metrics:")
    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"R²: {r2:.4f}")
    
    # Setup visualization
    plt.figure(figsize=(14, 7), facecolor='black')
    plt.style.use('dark_background')
    
    # Get values at interval points
    interval_actual = [actual_values[i] for i in interval_indices]
    interval_predictions = [predictions[i] for i in interval_indices]
    
    # Format timestamps for display
    display_timestamps = [ts.strftime('%H:%M') for ts in interval_timestamps]
    
    # Plot with different colors and styles for clear distinction
    plt.plot(range(len(interval_actual)), interval_actual, 
             color='#2E86C1', linewidth=2.5, label='Close Price')
    
    plt.plot(range(len(interval_predictions)), interval_predictions, 
             color='#E74C3C', linewidth=2, linestyle='--', 
             label='Close Price Predicted with Sentiment & Finance Data')
    
    # Calculate y-axis limits with some padding
    all_values = interval_actual + interval_predictions
    y_min = min(all_values) * 0.995
    y_max = max(all_values) * 1.005
    plt.ylim(y_min, y_max)
    
    # Set x-axis ticks and labels (show about 10-15 ticks for readability)
    tick_indices = list(range(0, len(interval_timestamps), max(1, len(interval_timestamps) // 12)))
    if len(interval_timestamps) - 1 not in tick_indices:
        tick_indices.append(len(interval_timestamps) - 1)
    tick_labels = [display_timestamps[i] for i in tick_indices]
    plt.xticks(tick_indices, tick_labels, rotation=45)
    
    # Add labels and title
    day_str = df['createdDate'].dt.strftime('%Y-%m-%d').iloc[0]
    plt.title(f"Real-Time Stock Price ({day_str})", fontsize=16)
    plt.xlabel('Time (CT)', fontsize=12)
    plt.ylabel('Stock Price (USD)', fontsize=12)
    
    # Add metrics to the plot
    metrics_text = f"RMSE: {rmse:.4f}  MAE: {mae:.4f}  R²: {r2:.4f}"
    plt.annotate(metrics_text, xy=(0.5, 0.02), xycoords='figure fraction', 
                 ha='center', va='bottom', color='white', fontsize=10)
    
    # Add grid and legend
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    plt.tight_layout()
    
    # Save the visualization
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    save_path = os.path.join(results_dir, f"price_predictions_{timestamp}.png")
    plt.savefig(save_path)
    print(f"Visualization saved to {save_path}")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    # List available models
    models = list_available_models()
    
    if models:
        # Let user select a model
        selection = input("Enter the number of the model to use (or press Enter for the latest): ")
        if selection.strip() and selection.isdigit() and 1 <= int(selection) <= len(models):
            model_path = models[int(selection) - 1]
        else:
            # Use latest model
            model_path = models[0]
        
        model_filename = os.path.basename(model_path)
        print(f"Using model: {model_filename}")
        
        # Generate visualization with 10-minute intervals for full day
        visualize_prediction(model_path, interval=10)
    else:
        print("No models available. Please train a model first.")