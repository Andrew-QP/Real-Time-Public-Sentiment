import os
from data_loader import DataLoader
from model import StockPriceLSTM
from training_utils import TrainingManager
from visualization import VisualizationManager
from config import config

def main():
    # Initialize components
    data_loader = DataLoader(config)
    model = StockPriceLSTM(config)
    training_manager = TrainingManager(config, model, data_loader)
    visualization_manager = VisualizationManager(config)
    
    # Train model and get results
    history, metrics = training_manager.train_model()
    
    # Save the model with timestamp - the save method now handles directory creation
    model.save(config["model_save_path"])
    
    # Get predictions for visualization
    y_test, predictions = training_manager.get_prediction_sequences()
    
    # Print visualization data instead of creating plots
    visualization_manager.create_all_prints(history, y_test, predictions, "Test")
    
    # Print metrics
    print("\nModel Performance Metrics:")
    for dataset in metrics:
        print(f"\n{dataset.upper()} Set Metrics:")
        for metric, value in metrics[dataset].items():
            print(f"{metric.upper()}: {value:.4f}")

if __name__ == "__main__":
    main()