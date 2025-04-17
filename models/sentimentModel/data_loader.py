import sqlite3
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple

class DataLoader:
    def __init__(self, config: dict):
        """
        Initialize DataLoader with configuration parameters
        """
        self.config = config
        self.scaler = MinMaxScaler()
        
    def convert_to_numeric(self, value):
        """
        Convert string values like '1.3K' to numeric values (1300)
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return 0.0
            
        # Remove any commas
        value = value.replace(',', '')
        
        # Check for K, M, B suffixes
        if 'K' in value or 'k' in value:
            # Remove the K and multiply by 1000
            return float(value.replace('K', '').replace('k', '')) * 1000
        elif 'M' in value or 'm' in value:
            # Remove the M and multiply by 1,000,000
            return float(value.replace('M', '').replace('m', '')) * 1000000
        elif 'B' in value or 'b' in value:
            # Remove the B and multiply by 1,000,000,000
            return float(value.replace('B', '').replace('b', '')) * 1000000000
        else:
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        
    def load_data(self) -> pd.DataFrame:
        """
        Load tweet data including financial data from SQLite database
        """
        # Get absolute path to database
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(script_dir, self.config["db_path"]))
        print(f"Loading database from: {db_path}")
        
        conn = sqlite3.connect(db_path)
        
        # Create the query with all needed features
        financial_features = ", ".join(self.config["use_financial_features"])
        sentiment_features = ", ".join(self.config["use_sentiment_features"])
        engagement_features = ", ".join(self.config["use_engagement_features"])
        
        query = f"""
            SELECT createdDate, 
                   {financial_features}, 
                   {sentiment_features}, 
                   {engagement_features}
            FROM tweets 
            WHERE {self.config["target_column"]} IS NOT NULL
            ORDER BY createdDate ASC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert time column to datetime
        df['createdDate'] = pd.to_datetime(df['createdDate'], format='%Y-%m-%d %I:%M %p')
        
        # Convert engagement features from strings (like "1.3K") to numeric values
        for feature in self.config["use_engagement_features"]:
            df[feature] = df[feature].apply(self.convert_to_numeric)
        
        print(f"Successfully loaded {len(df)} rows of data")
        
        return df
    
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequence data for LSTM input with 10-minute prediction horizon
        """
        # Select features specified in config
        financial_features = self.config["use_financial_features"]
        sentiment_features = self.config["use_sentiment_features"]
        engagement_features = self.config["use_engagement_features"]
        
        all_features = financial_features + sentiment_features + engagement_features
        df = data[all_features].copy()
        
        # Apply weights to features
        for feature in financial_features:
            df[feature] = df[feature] * self.config["financial_weight"]
            
        for feature in sentiment_features:
            df[feature] = df[feature] * self.config["sentiment_weight"]
            
        for feature in engagement_features:
            df[feature] = df[feature] * self.config["engagement_weight"]
        
        X, y = [], []
        sequence_length = self.config["sequence_length"]
        prediction_horizon = 1  # Predicting 10 minutes ahead
        
        for i in range(len(df) - sequence_length - prediction_horizon + 1):
            # Create sequence of specified length
            sequence = df.iloc[i:(i + sequence_length)].values
            
            # Target is the close price 10 minutes ahead
            target_idx = financial_features.index(self.config["target_column"])
            target = data.iloc[i + sequence_length + prediction_horizon - 1][financial_features[target_idx]]
            
            X.append(sequence)
            y.append(target)
            
        print(f"Created {len(X)} sequences of length {sequence_length} for 10-minute ahead prediction")
        print(f"Applied feature weights: financial={self.config['financial_weight']}, "
              f"sentiment={self.config['sentiment_weight']}, engagement={self.config['engagement_weight']}")
        
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
    
    def train_val_test_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, 
                                                                       np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train, validation, and test sets
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
    
    def prepare_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, 
                                np.ndarray, np.ndarray, np.ndarray]:
        """
        Main method to prepare all data for training
        """
        # Load data
        df = self.load_data()
        
        # Create sequences with feature weights applied
        X, y = self.prepare_sequences(df)
        
        # Split into train, validation, and test sets (before scaling)
        X_train, X_val, X_test, y_train, y_val, y_test = self.train_val_test_split(X, y)
        
        # Handle NaN values
        X_train = np.nan_to_num(X_train)
        X_val = np.nan_to_num(X_val)
        X_test = np.nan_to_num(X_test)
        y_train = np.nan_to_num(y_train)
        y_val = np.nan_to_num(y_val)
        y_test = np.nan_to_num(y_test)
        
        # Reshape data for scaling
        n_samples_train, n_steps, n_features = X_train.shape
        X_train_2d = X_train.reshape(-1, n_features)
        
        # Fit scaler on training data only
        self.scaler.fit(X_train_2d)
        
        # Transform all datasets
        X_train_2d = self.scaler.transform(X_train_2d)
        X_train_scaled = X_train_2d.reshape(n_samples_train, n_steps, n_features)
        
        n_samples_val = X_val.shape[0]
        X_val_2d = X_val.reshape(-1, n_features)
        X_val_2d = self.scaler.transform(X_val_2d)
        X_val_scaled = X_val_2d.reshape(n_samples_val, n_steps, n_features)
        
        n_samples_test = X_test.shape[0]
        X_test_2d = X_test.reshape(-1, n_features)
        X_test_2d = self.scaler.transform(X_test_2d)
        X_test_scaled = X_test_2d.reshape(n_samples_test, n_steps, n_features)
        
        # Scale target values (only for training)
        y_scaler = MinMaxScaler()
        y_train_scaled = y_scaler.fit_transform(y_train.reshape(-1, 1)).flatten()
        y_val_scaled = y_scaler.transform(y_val.reshape(-1, 1)).flatten()
        y_test_scaled = y_scaler.transform(y_test.reshape(-1, 1)).flatten()
        
        self.y_scaler = y_scaler  # Store for later use
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train_scaled, y_val_scaled, y_test_scaled
    
    def inverse_transform_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        Inverse transform scaled predictions back to original scale
        """
        # Reshape predictions if needed (handles both (n,) and (n,1) shapes)
        if len(predictions.shape) == 1:
            predictions = predictions.reshape(-1, 1)
            
        # Inverse transform
        return self.y_scaler.inverse_transform(predictions).flatten()