import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np
import os
from datetime import datetime

class StockSentimentLSTM:
    def __init__(self, config: dict):
        """
        Initialize the LSTM model for stock price prediction with sentiment analysis
        """
        self.config = config
        self.model = self._build_model()
        self.history = None
        
    def _build_model(self) -> Sequential:
        """
        Build and compile the LSTM model architecture
        """
        # Count total number of features
        total_features = (len(self.config["use_financial_features"]) + 
                         len(self.config["use_sentiment_features"]) + 
                         len(self.config["use_engagement_features"]))
        
        model = Sequential()
        
        # First LSTM layer with Bidirectional wrapper
        model.add(Bidirectional(
            LSTM(
                units=self.config["lstm_units"][0],
                return_sequences=True
            ),
            input_shape=(self.config["sequence_length"], total_features)
        ))
        model.add(Dropout(self.config["dropout_rate"]))
        
        # Second LSTM layer
        model.add(LSTM(
            units=self.config["lstm_units"][1],
            return_sequences=True
        ))
        model.add(Dropout(self.config["dropout_rate"]))
        
        # Third LSTM layer
        model.add(LSTM(
            units=self.config["lstm_units"][2],
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
    
    def summary(self):
        """
        Print the model summary
        """
        return self.model.summary()
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray) -> dict:
        """
        Train the model with early stopping
        """
        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.config["patience"],
            restore_best_weights=True,
            verbose=1
        )
        
        # Train the model
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config["epochs"],
            batch_size=self.config["batch_size"],
            callbacks=[early_stopping],
            verbose=1
        )
        
        # Print weights used for features
        print("\nFeature weights used:")
        print(f"Financial Features: {self.config['financial_weight']:.4f}")
        print(f"Sentiment Features: {self.config['sentiment_weight']:.4f}")
        print(f"Engagement Features: {self.config['engagement_weight']:.4f}")
        
        return self.history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model
        """
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray):
        """
        Evaluate the model on test data
        """
        return self.model.evaluate(X, y, verbose=0)
    
    def save(self):
        """
        Save the model to disk with timestamp
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
        filename = os.path.basename(self.config["model_save_path"])
        name_parts = os.path.splitext(filename)
        save_path = os.path.join(versions_dir, f"{name_parts[0]}_{timestamp}{name_parts[1]}")
        
        # Save the model
        self.model.save(save_path)
        print(f"Model successfully saved to {save_path}")
        
        # Save weights info
        weights_path = os.path.join(versions_dir, f"feature_weights_{timestamp}.txt")
        with open(weights_path, 'w') as f:
            f.write("Feature weights used:\n")
            f.write(f"Financial: {self.config['financial_weight']:.4f}\n")
            f.write(f"Sentiment: {self.config['sentiment_weight']:.4f}\n")
            f.write(f"Engagement: {self.config['engagement_weight']:.4f}\n")
        
        print(f"Feature weights saved to {weights_path}")
        
    def load(self, filepath):
        """
        Load a saved model from disk
        """
        self.model = load_model(filepath)
        print(f"Model successfully loaded from {filepath}")