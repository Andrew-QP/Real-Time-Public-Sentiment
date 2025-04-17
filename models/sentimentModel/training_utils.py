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
        
    def train_model(self, financial_weight=1.0, sentiment_weight=1.0, engagement_weight=1.0) -> Tuple[Dict, Dict]:
        """
        Train the model and evaluate performance
        
        Args:
            financial_weight (float): Weight for financial features
            sentiment_weight (float): Weight for sentiment features
            engagement_weight (float): Weight for engagement features
            
        Returns:
            Tuple[Dict, Dict]: Training history and evaluation metrics
        """
        # Prepare data with optional feature weighting
        X_train, X_val, X_test, y_train, y_val, y_test = self.data_loader.prepare_data(
            financial_weight=financial_weight,
            sentiment_weight=sentiment_weight,
            engagement_weight=engagement_weight
        )
        
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
        self._save_results(history, metrics, {
            "financial_weight": financial_weight,
            "sentiment_weight": sentiment_weight,
            "engagement_weight": engagement_weight
        })
        
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
    
    def _save_results(self, history: Dict, metrics: Dict, weights: Dict) -> None:
        """
        Save training history and metrics to files
        
        Args:
            history (Dict): Training history
            metrics (Dict): Evaluation metrics
            weights (Dict): Feature weights used
        """
        # Create results directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(script_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Add feature attention weights if available
        attention_weights = {}
        try:
            attention_weights = {
                "feature_attention": self.model.get_attention_weights()
            }
        except (AttributeError, TypeError):
            pass
        
        # Combine results
        full_results = {
            "weights": weights,
            "attention_weights": attention_weights,
            "metrics": metrics,
            "timestamp": timestamp
        }
        
        # Save history
        history_path = os.path.join(
            results_dir, 
            f"sentiment_history_{timestamp}.json"
        )
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=4)
        
        # Save results
        results_path = os.path.join(
            results_dir, 
            f"sentiment_results_{timestamp}.json"
        )
        with open(results_path, 'w') as f:
            json.dump(full_results, f, indent=4)
        
        print(f"Results saved to {results_path}")
    
    def get_prediction_sequences(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get test set predictions for visualization
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: 
                Actual and predicted values
        """
        # Prepare data
        _, _, X_test, _, _, y_test = self.data_loader.prepare_data()
        
        # Get predictions
        predictions = self.model.predict(X_test)
        
        # Inverse transform
        y_test_orig = self.data_loader.inverse_transform_predictions(y_test)
        predictions_orig = self.data_loader.inverse_transform_predictions(predictions)
        
        return y_test_orig, predictions_orig