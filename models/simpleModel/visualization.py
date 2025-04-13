import numpy as np
from typing import Dict, List

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