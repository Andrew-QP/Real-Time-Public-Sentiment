import numpy as np
import pandas as pd
import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import config

class VisualizationManager:
    def __init__(self, config: dict):
        """
        Initialize Visualization Manager
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config
        
    def print_training_history(self, history: Dict) -> None:
        """
        Print training and validation loss information
        
        Args:
            history (Dict): Training history from model
        """
        print("\nTraining History Summary:")
        print(f"Final training loss: {history['loss'][-1]:.6f}")
        print(f"Final validation loss: {history['val_loss'][-1]:.6f}")
        print(f"Best validation loss: {min(history['val_loss']):.6f} at epoch {history['val_loss'].index(min(history['val_loss']))+1}")
        
    def print_predictions_summary(self, y_true: np.ndarray, y_pred: np.ndarray, 
                        set_name: str = "Test") -> None:
        """
        Print prediction summary statistics
        
        Args:
            y_true (np.ndarray): True values
            y_pred (np.ndarray): Predicted values
            set_name (str): Name of the dataset (Train/Val/Test)
        """
        errors = y_true - y_pred
        
        print(f"\n{set_name} Set Prediction Summary:")
        print(f"Mean Error: {np.mean(errors):.4f}")
        print(f"Standard Deviation of Error: {np.std(errors):.4f}")
        print(f"Min Error: {np.min(errors):.4f}")
        print(f"Max Error: {np.max(errors):.4f}")
        
    def print_sentiment_impact(self, feature_weights: Dict) -> None:
        """
        Print information about the impact of sentiment features
        
        Args:
            feature_weights (Dict): Learned weights for different feature groups
        """
        print("\nSentiment Feature Impact:")
        
        # Display weights
        for feature_group, weight in feature_weights.items():
            print(f"{feature_group}: {weight:.4f}")
            
        # Calculate relative importance
        total_weight = sum(feature_weights.values())
        for feature_group, weight in feature_weights.items():
            relative_importance = (weight / total_weight) * 100
            print(f"Relative importance of {feature_group}: {relative_importance:.2f}%")
    
    def print_sentiment_summary(self, db_path: Optional[str] = None, days: int = 5) -> None:
        """
        Print summary of sentiment data and its correlation with price
        
        Args:
            db_path (str, optional): Path to the database
            days (int): Number of recent days to include
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if db_path is None:
            db_path = os.path.abspath(os.path.join(script_dir, self.config["db_path"]))
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Construct query
        sentiment_features = ", ".join(self.config["use_sentiment_features"])
        
        query = f"""
            SELECT createdDate, close, {sentiment_features}
            FROM tweets
            WHERE createdDate >= '{start_date_str}'
            AND close IS NOT NULL
            ORDER BY createdDate ASC
        """
        
        # Execute query
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert time column to datetime
        df['createdDate'] = pd.to_datetime(df['createdDate'], format='%Y-%m-%d %I:%M %p')
        
        # Calculate sentiment scores
        df['positive_sentiment'] = df[['joy', 'love', 'optimism', 'trust', 'anticipation']].mean(axis=1)
        df['negative_sentiment'] = df[['anger', 'disgust', 'fear', 'sadness', 'pessimism']].mean(axis=1)
        df['net_sentiment'] = df['positive_sentiment'] - df['negative_sentiment']
        
        # Calculate correlation with price
        correlation = df['net_sentiment'].corr(df['close'])
        
        print(f"\nSentiment Analysis Summary (Last {days} days):")
        print(f"Average positive sentiment: {df['positive_sentiment'].mean():.4f}")
        print(f"Average negative sentiment: {df['negative_sentiment'].mean():.4f}")
        print(f"Average net sentiment: {df['net_sentiment'].mean():.4f}")
        print(f"Correlation between net sentiment and price: {correlation:.4f}")
        
        # Check if any sentiment features show strong correlation with price
        for feature in self.config["use_sentiment_features"]:
            feature_corr = df[feature].corr(df['close'])
            if abs(feature_corr) > 0.3:  # Arbitrary threshold for "strong" correlation
                print(f"Strong correlation found: {feature} and price: {feature_corr:.4f}")
    
    def create_all_prints(self, history: Dict, y_true: np.ndarray, 
                        y_pred: np.ndarray, set_name: str = "Test") -> None:
        """
        Print all visualization data to terminal
        
        Args:
            history (Dict): Training history
            y_true (np.ndarray): True values
            y_pred (np.ndarray): Predicted values
            set_name (str): Name of the dataset (Train/Val/Test)
        """
        # Print all summaries
        self.print_training_history(history)
        self.print_predictions_summary(y_true, y_pred, set_name)
        
        # Additional sentiment-specific summaries can be called here if needed:
        # self.print_sentiment_summary()