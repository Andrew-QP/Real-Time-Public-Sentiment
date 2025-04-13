"""
This utility file allows using a pre-trained model without retraining.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from data_loader import DataLoader
from config import config
from datetime import datetime


def predict_next_10_minutes(model_path, sequence_data=None):
    """
    Make predictions for the next 10 minutes using a pre-trained model
    
    Args:
        model_path (str): Path to the saved model
        sequence_data (np.ndarray, optional): Custom input sequence
                                            If None, uses latest data
    
    Returns:
        float: Predicted price
    """
    # Load the model directly using Keras (no need for the StockPriceLSTM class)
    model = load_model(model_path)
    print(f"Successfully loaded model from {model_path}")
    
    # If no custom data provided, load the latest data
    if sequence_data is None:
        # Initialize DataLoader
        data_loader = DataLoader(config)
        
        # Get the latest data
        df = data_loader.load_stock_data()
        
        # Prepare a single sequence from the latest data
        features = config["use_features"]
        sequence_length = config["sequence_length"]
        
        # Get the last sequence_length rows
        latest_data = df[features].iloc[-sequence_length:].values
        
        # Reshape for model input (batch_size, sequence_length, features)
        sequence_data = np.expand_dims(latest_data, axis=0)
        
        # Scale the data using the same scaler settings
        train_data = df[features].iloc[:int(len(df)*0.75)].values
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaler.fit(train_data)
        
        # Apply scaling
        sequence_data_reshaped = sequence_data.reshape(-1, len(features))
        sequence_data_scaled = scaler.transform(sequence_data_reshaped)
        sequence_data = sequence_data_scaled.reshape(1, sequence_length, len(features))
    
    # Make prediction
    prediction = model.predict(sequence_data)[0][0]
    
    # If we have a scaler defined, inverse transform
    if 'scaler' in locals():
        # Create dummy array for inverse transformation
        dummy = np.zeros((1, len(features)))
        target_idx = features.index(config["target_column"])
        dummy[0, target_idx] = prediction
        inverse_dummy = scaler.inverse_transform(dummy)
        prediction = inverse_dummy[0, target_idx]
    
    print(f"Predicted {config['target_column']} for 10 minutes from now: ${prediction:.2f}")
    return prediction

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
    
    if not model_files:
        print("No trained models found in the versions directory.")
        return []
    
    print("Available trained models:")
    for i, model_file in enumerate(model_files):
        print(f"{i+1}. {model_file}")
    
    return [os.path.join(directory, f) for f in model_files]

def visualize_prediction(model_path, num_samples=36):
    """
    Visualize predictions vs actual values for the most recent data
    
    Args:
        model_path (str): Path to the model file
        num_samples (int): Number of samples to visualize
    """
    # Extract timestamp from the model filename
    model_filename = os.path.basename(model_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Try to extract timestamp from filename
    import re
    timestamp_match = re.search(r'(\d{8}_\d{6})', model_filename)
    if timestamp_match:
        timestamp = timestamp_match.group(1)
    
    # Load the model
    model = load_model(model_path)
    
    # Load data
    data_loader = DataLoader(config)
    df = data_loader.load_stock_data()
    
    # Prepare sequences
    features = config["use_features"]
    sequence_length = config["sequence_length"]
    
    # Get the most recent data for visualization
    recent_data = df[features].iloc[-num_samples:].values
    
    # Get timestamps for x-axis
    recent_timestamps = df.index[-num_samples:].strftime('%m-%d %H:%M')
    
    # Create a single sequence from the entire recent data
    full_sequence = recent_data[-sequence_length:]
    
    # Reshape for model input (batch_size, sequence_length, features)
    sequence_data = np.expand_dims(full_sequence, axis=0)
    
    # Scale the data using the same scaler settings
    train_data = df[features].iloc[:int(len(df)*0.75)].values
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    scaler.fit(train_data)
    
    # Apply scaling
    sequence_data_reshaped = sequence_data.reshape(-1, len(features))
    sequence_data_scaled = scaler.transform(sequence_data_reshaped)
    sequence_data = sequence_data_scaled.reshape(1, sequence_length, len(features))
    
    # Make prediction for 10 minutes into the future
    prediction = model.predict(sequence_data)[0][0]
    
    # Inverse transform prediction
    dummy = np.zeros((1, len(features)))
    target_idx = features.index(config["target_column"])
    dummy[0, target_idx] = prediction
    prediction_value = scaler.inverse_transform(dummy)[0, target_idx]
    
    # Create visualization
    plt.figure(figsize=(14, 7))
    
    # Plot actual prices
    plt.plot(recent_timestamps, recent_data[:, target_idx], 
             label='Historical Prices', marker='o', color='blue', linewidth=2)
    
    # Add the prediction as a separate point
    future_label = 'Predicted (10 min ahead): ${:.2f}'.format(prediction_value)
    plt.scatter([len(recent_timestamps)], [prediction_value], 
                label=future_label, marker='*', s=200, color='red')
    
    # Add a vertical line to mark where history ends and prediction begins
    plt.axvline(x=len(recent_timestamps)-1, color='gray', linestyle='--', 
                alpha=0.7, label='Now')
    
    # Connect the last actual point to the prediction with a dotted line
    plt.plot([len(recent_timestamps)-1, len(recent_timestamps)], 
             [recent_data[-1, target_idx], prediction_value], 
             'r--', alpha=0.7)
    
    # Set title and labels
    plt.title('Tesla Stock Price Prediction (10 Minutes Ahead)', fontsize=16)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Close Price ($)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Improve x-axis labels
    plt.xticks(range(len(recent_timestamps)), recent_timestamps, rotation=45)
    
    # Add a text annotation for the prediction
    plt.annotate(f'${prediction_value:.2f}', 
                xy=(len(recent_timestamps), prediction_value),
                xytext=(5, 0), textcoords='offset points',
                fontsize=12, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    plt.legend(loc='best')
    
    # Save plot to results directory with matching timestamp
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "results")
    
    # Create results directory if it doesn't exist
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Create plot filename with timestamp matching model
    plot_path = os.path.join(results_dir, f'prediction_visualization_{timestamp}.png')
    plt.savefig(plot_path)
    print(f"Visualization saved to {plot_path}")
    plt.show()

if __name__ == "__main__":
    # List available models
    models = list_available_models()
    
    if models:
        # Let user select a model
        selection = input("Enter the number of the model to use (or press Enter for the latest): ")
        if selection.strip():
            model_path = models[int(selection)-1]
        else:
            # Use the latest model (sort by timestamp in filename)
            model_path = sorted(models, reverse=True)[0]
        
        # Make a prediction
        predict_next_10_minutes(model_path)
        
        # Ask if user wants to visualize predictions
        visualize = input("Would you like to visualize predictions vs actual values? (y/n): ")
        if visualize.lower() == 'y':
            visualize_prediction(model_path)
    else:
        print("No models available. Please train a model first.")