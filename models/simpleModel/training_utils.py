import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, Tuple, List
import json
import os
from datetime import datetime

class TrainingManager:
    def __init__(self, config: dict, model, data_loader):
        """
        Initialize Training Manager
        
        Args:
            config (dict): Configuration parameters
            model: LSTM model instance
            data_loader: DataLoader instance
        """
        self.config = config
        self.model = model
        self.data_loader = data_loader
        
    def train_model(self) -> Tuple[Dict, Dict]:
        """
        Train the model and evaluate performance
        
        Returns:
            Tuple[Dict, Dict]: Training history and evaluation metrics
        """
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test = self.data_loader.prepare_data()
        
        # Train model
        history = self.model.train(X_train, y_train, X_val, y_val)
        
        # Get predictions
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)
        test_pred = self.model.predict(X_test)
        
        # Inverse transform predictions and actual values
        train_pred = self.data_loader.inverse_transform_predictions(train_pred)
        val_pred = self.data_loader.inverse_transform_predictions(val_pred)
        test_pred = self.data_loader.inverse_transform_predictions(test_pred)
        
        y_train_orig = self.data_loader.inverse_transform_predictions(y_train)
        y_val_orig = self.data_loader.inverse_transform_predictions(y_val)
        y_test_orig = self.data_loader.inverse_transform_predictions(y_test)
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            y_train_orig, y_val_orig, y_test_orig,
            train_pred, val_pred, test_pred
        )
        
        # Save results
        self._save_results(history, metrics)
        
        return history, metrics
    
    def _calculate_metrics(self, y_train: np.ndarray, y_val: np.ndarray, 
                         y_test: np.ndarray, train_pred: np.ndarray, 
                         val_pred: np.ndarray, test_pred: np.ndarray) -> Dict:
        """
        Calculate evaluation metrics for all datasets
        
        Returns:
            Dict: Dictionary containing all metrics
        """
        metrics = {}
        
        # Calculate metrics for each dataset
        for name, y_true, y_pred in [
            ("train", y_train, train_pred),
            ("val", y_val, val_pred),
            ("test", y_test, test_pred)
        ]:
            metrics[name] = {
                "mse": mean_squared_error(y_true, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
                "mae": mean_absolute_error(y_true, y_pred),
                "r2": r2_score(y_true, y_pred),
                "mape": np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
            }
        
        return metrics
    
    def _save_results(self, history: Dict, metrics: Dict) -> None:
        """
        Save training history and metrics to files
        
        Args:
            history (Dict): Training history
            metrics (Dict): Evaluation metrics
        """
        # Create results directory if it doesn't exist
        os.makedirs(self.config["results_path"], exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save history
        history_path = os.path.join(
            self.config["results_path"], 
            f"training_history_{timestamp}.json"
        )
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=4)
        
        # Save metrics
        metrics_path = os.path.join(
            self.config["results_path"], 
            f"metrics_{timestamp}.json"
        )
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        
    def get_prediction_sequences(self) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Get actual and predicted sequences for visualization
        
        Returns:
            Tuple[List[np.ndarray], List[np.ndarray]]: 
                Actual and predicted sequences
        """
        # Prepare data
        X_test, y_test = self.data_loader.prepare_sequences(
            self.data_loader.load_stock_data()
        )
        
        # Get predictions
        predictions = self.model.predict(X_test)
        
        # Inverse transform
        y_test = self.data_loader.inverse_transform_predictions(y_test)
        predictions = self.data_loader.inverse_transform_predictions(predictions)
        
        return y_test, predictions