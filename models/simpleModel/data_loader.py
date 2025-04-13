import sqlite3
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List

class DataLoader:
    def __init__(self, config: dict):
        """
        Initialize DataLoader with configuration parameters
        
        Args:
            config (dict): Configuration dictionary containing data parameters
        """
        self.config = config
        self.scaler = MinMaxScaler()
        
    def load_stock_data(self) -> pd.DataFrame:
        """
        Load stock data from SQLite database
        
        Returns:
            pd.DataFrame: DataFrame containing stock price data
        """
        # Get absolute path to database
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(script_dir, self.config["db_path"]))
        print(f"Loading database from: {db_path}")
        
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM stockPrice ORDER BY time ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert time column to datetime
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        
        print(f"Successfully loaded {len(df)} rows of stock data")
        return df
    
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequence data for LSTM input with 10-minute prediction horizon
        
        Args:
            data (pd.DataFrame): Input DataFrame with stock price data
                
        Returns:
            Tuple[np.ndarray, np.ndarray]: X (sequences) and y (targets)
        """
        # Select features specified in config
        features = self.config["use_features"]
        df = data[features].copy()
        
        X, y = [], []
        
        # The prediction horizon (10 minutes ahead)
        prediction_horizon = 10
        
        for i in range(len(df) - self.config["sequence_length"] - prediction_horizon + 1):
            # Create sequence of specified length
            sequence = df.iloc[i:(i + self.config["sequence_length"])].values
            
            # Target is now 10 minutes ahead instead of 1 minute
            target = df.iloc[i + self.config["sequence_length"] + prediction_horizon - 1][self.config["target_column"]]
            
            X.append(sequence)
            y.append(target)
            
        print(f"Created {len(X)} sequences of length {self.config['sequence_length']} for {prediction_horizon}-minute ahead prediction")
        return np.array(X), np.array(y)
    
    def train_val_test_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, 
                                                                         np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train, validation, and test sets
        
        Args:
            X (np.ndarray): Input sequences
            y (np.ndarray): Target values
            
        Returns:
            Tuple containing train, validation, and test sets
        """
        # Calculate split indices
        n = len(X)
        train_end = int(n * self.config["train_ratio"])
        val_end = train_end + int(n * self.config["val_ratio"])
        
        # Split the data
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        print(f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def inverse_transform_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        Inverse transform scaled predictions back to original scale
        
        Args:
            predictions (np.ndarray): Scaled predictions
            
        Returns:
            np.ndarray: Predictions in original scale
        """
        # Reshape predictions if needed (handles both (n,) and (n,1) shapes)
        if len(predictions.shape) > 1:
            predictions = predictions.flatten()
            
        # Create a dummy array with zeros for all features
        dummy = np.zeros((len(predictions), len(self.config["use_features"])))
        
        # Put predictions in the correct column (target column)
        target_idx = self.config["use_features"].index(self.config["target_column"])
        dummy[:, target_idx] = predictions
        
        # Inverse transform
        inv_transformed = self.scaler.inverse_transform(dummy)
        
        # Return only the target column
        return inv_transformed[:, target_idx]
    
    def prepare_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, 
                                np.ndarray, np.ndarray, np.ndarray]:
        """
        Main method to prepare all data for training with proper scaling to avoid leakage
        
        Returns:
            Tuple containing train, validation, and test sets
        """
        # Load data
        df = self.load_stock_data()
        
        # Select features specified in config
        features = self.config["use_features"]
        df_features = df[features].copy()
        
        # Create sequences without scaling first
        X, y = [], []
        target_idx = features.index(self.config["target_column"])
        
        for i in range(len(df_features) - self.config["sequence_length"]):
            # Create sequence of specified length without scaling
            sequence = df_features.iloc[i:(i + self.config["sequence_length"])].values
            target = df_features.iloc[i + self.config["sequence_length"], target_idx]
            
            X.append(sequence)
            y.append(target)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created {len(X)} sequences of length {self.config['sequence_length']}")
        
        # Split data first (before scaling)
        n = len(X)
        train_end = int(n * self.config["train_ratio"])
        val_end = train_end + int(n * self.config["val_ratio"])
        
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        print(f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        
        # Fit scaler only on training data
        # Reshape training data to 2D for scaling
        train_data_flat = X_train.reshape(-1, len(features))
        self.scaler = MinMaxScaler()
        self.scaler.fit(train_data_flat)
        
        # Scale each dataset using the scaler fit only on training data
        # Process each sequence individually
        X_train_scaled = np.zeros_like(X_train)
        for i, seq in enumerate(X_train):
            X_train_scaled[i] = self.scaler.transform(seq)
        
        X_val_scaled = np.zeros_like(X_val)
        for i, seq in enumerate(X_val):
            X_val_scaled[i] = self.scaler.transform(seq)
        
        X_test_scaled = np.zeros_like(X_test)
        for i, seq in enumerate(X_test):
            X_test_scaled[i] = self.scaler.transform(seq)
        
        # Scale target values
        # Create dummy arrays for the inverse transform later
        y_train_2d = np.zeros((len(y_train), len(features)))
        y_train_2d[:, target_idx] = y_train
        y_train_2d = self.scaler.transform(y_train_2d)
        y_train_scaled = y_train_2d[:, target_idx]
        
        y_val_2d = np.zeros((len(y_val), len(features)))
        y_val_2d[:, target_idx] = y_val
        y_val_2d = self.scaler.transform(y_val_2d)
        y_val_scaled = y_val_2d[:, target_idx]
        
        y_test_2d = np.zeros((len(y_test), len(features)))
        y_test_2d[:, target_idx] = y_test
        y_test_2d = self.scaler.transform(y_test_2d)
        y_test_scaled = y_test_2d[:, target_idx]
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train_scaled, y_val_scaled, y_test_scaled