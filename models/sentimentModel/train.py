import os
import numpy as np
from data_loader import DataLoader
from model import StockSentimentLSTM
from config import config
import time
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime

def main():
    """Main function to train the model and evaluate it"""
    print(f"\n{'=' * 50}")
    print("Training Sentiment-Enhanced Stock Price Prediction Model")
    print(f"Feature weights: Financial={config['financial_weight']}, " 
          f"Sentiment={config['sentiment_weight']}, Engagement={config['engagement_weight']}")
    print(f"{'=' * 50}\n")
    
    try:
        # Initialize components
        data_loader = DataLoader(config)
        model = StockSentimentLSTM(config)
        
        # Print model summary
        model.summary()
        
        # Prepare data
        print("\nPreparing data...")
        start_time = time.time()
        X_train, X_val, X_test, y_train, y_val, y_test = data_loader.prepare_data()
        print(f"Data preparation completed in {time.time() - start_time:.2f} seconds")
        
        # Train the model
        print("\nTraining the model...")
        start_time = time.time()
        history = model.train(X_train, y_train, X_val, y_val)
        training_time = time.time() - start_time
        print(f"Training completed in {training_time:.2f} seconds")
        
        # Make predictions
        print("\nMaking predictions...")
        train_preds = model.predict(X_train).flatten()
        val_preds = model.predict(X_val).flatten()
        test_preds = model.predict(X_test).flatten()
        
        # Convert predictions back to original scale
        train_preds_orig = data_loader.inverse_transform_predictions(train_preds)
        val_preds_orig = data_loader.inverse_transform_predictions(val_preds)
        test_preds_orig = data_loader.inverse_transform_predictions(test_preds)
        
        # Convert targets back to original scale
        y_train_orig = data_loader.inverse_transform_predictions(y_train)
        y_val_orig = data_loader.inverse_transform_predictions(y_val)
        y_test_orig = data_loader.inverse_transform_predictions(y_test)
        
        # Calculate metrics
        train_metrics = calculate_metrics(y_train_orig, train_preds_orig)
        val_metrics = calculate_metrics(y_val_orig, val_preds_orig)
        test_metrics = calculate_metrics(y_test_orig, test_preds_orig)
        
        # Save the model
        model.save()
        
        # Print training history summary
        print("\nTraining History Summary:")
        print(f"Final training loss: {history['loss'][-1]:.6f}")
        print(f"Final validation loss: {history['val_loss'][-1]:.6f}")
        best_epoch = history['val_loss'].index(min(history['val_loss'])) + 1
        print(f"Best validation loss: {min(history['val_loss']):.6f} at epoch {best_epoch}")
        
        # Print prediction summary
        print("\nTest Set Prediction Summary:")
        errors = y_test_orig - test_preds_orig
        print(f"Mean Error: {np.mean(errors):.4f}")
        print(f"Standard Deviation of Error: {np.std(errors):.4f}")
        print(f"Min Error: {np.min(errors):.4f}")
        print(f"Max Error: {np.max(errors):.4f}")
        
        # Print metrics
        print("\nModel Performance Metrics:")
        for dataset, metrics in [("TRAIN", train_metrics), ("VAL", val_metrics), ("TEST", test_metrics)]:
            print(f"\n{dataset} Set Metrics:")
            for metric, value in metrics.items():
                print(f"{metric.upper()}: {value:.4f}")
                
    except Exception as e:
        print(f"ERROR: An error occurred during training: {str(e)}")
        import traceback
        traceback.print_exc()

def calculate_metrics(y_true, y_pred):
    """Calculate evaluation metrics"""
    # Handle NaN values
    y_true = np.nan_to_num(y_true)
    y_pred = np.nan_to_num(y_pred)
    
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # Handle division by zero in MAPE
    with np.errstate(divide='ignore', invalid='ignore'):
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1e-8))) * 100
    
    return {
        "mse": float(mse),
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "mape": float(mape)
    }

if __name__ == "__main__":
    main()