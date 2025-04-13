import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np
from typing import Tuple, Dict, Optional
import os
from datetime import datetime

class StockPriceLSTM:
    def __init__(self, config: dict):
        """
        Initialize the LSTM model for stock price prediction
        
        Args:
            config (dict): Configuration dictionary containing model parameters
        """
        self.config = config
        self.model = self._build_model()
        self.history = None
        
    def _build_model(self) -> Sequential:
        """
        Build and compile the LSTM model architecture
        
        Returns:
            Sequential: Compiled Keras model
        """
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(
            units=self.config["lstm_units"][0],
            return_sequences=True,
            input_shape=(self.config["sequence_length"], len(self.config["use_features"]))
        ))
        model.add(Dropout(self.config["dropout_rate"]))
        
        # Second LSTM layer
        model.add(LSTM(
            units=self.config["lstm_units"][1],
            return_sequences=False
        ))
        model.add(Dropout(self.config["dropout_rate"]))
        
        # Output layer
        model.add(Dense(units=1))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.config["learning_rate"]),
            loss='mean_squared_error',
            metrics=['mae']  # Also track Mean Absolute Error
        )
        
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
            X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """
        Train the model with early stopping only (no checkpoint)
        
        Args:
            X_train (np.ndarray): Training sequences
            y_train (np.ndarray): Training targets
            X_val (np.ndarray): Validation sequences
            y_val (np.ndarray): Validation targets
            
        Returns:
            Dict: Training history
        """
        # Callbacks - only using early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.config["patience"],
            restore_best_weights=True,
            verbose=1
        )
        
        # Train the model without the checkpoint callback
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config["epochs"],
            batch_size=self.config["batch_size"],
            callbacks=[early_stopping],
            verbose=1
        )
        
        return self.history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model
        
        Args:
            X (np.ndarray): Input sequences
            
        Returns:
            np.ndarray: Predicted values
        """
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Evaluate the model on test data
        
        Args:
            X (np.ndarray): Test sequences
            y (np.ndarray): True values
            
        Returns:
            Tuple[float, float]: MSE and MAE scores
        """
        mse, mae = self.model.evaluate(X, y, verbose=0)
        return mse, mae
    
    def save(self, filepath: Optional[str] = None) -> None:
        """
        Save the model to disk with timestamp in the versions directory
        
        Args:
            filepath (str, optional): Path to save the model. 
                                    If None, uses config path
        """
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create versions directory
        versions_dir = os.path.join(script_dir, "saved_versions")
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir)
        
        # Create filename with timestamp
        if filepath:
            filename = os.path.basename(filepath)
        else:
            filename = os.path.basename(self.config["model_save_path"])
        
        # Split filename and extension
        name_parts = os.path.splitext(filename)
        save_path = os.path.join(versions_dir, f"{name_parts[0]}_{timestamp}{name_parts[1]}")
        
        self.model.save(save_path)
        print(f"Model successfully saved to {save_path}")
        
    def load(self, filepath: Optional[str] = None) -> None:
        """
        Load a saved model from disk
        
        Args:
            filepath (str, optional): Path to load the model from. 
                                    If None, uses config path
        """
        load_path = filepath or self.config["model_save_path"]
        self.model = load_model(load_path)
        print(f"Model successfully loaded from {load_path}")