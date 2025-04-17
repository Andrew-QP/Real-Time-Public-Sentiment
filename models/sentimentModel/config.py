config = {
    # Data parameters
    "db_path": "../../rtsProjectDB.db",
    "train_ratio": 0.75, 
    "val_ratio": 0.1,
    "test_ratio": 0.15,
    
    # Feature parameters
    "sequence_length": 36,  
    "target_column": "close",
    "use_financial_features": ["open", "high", "low", "close", "volume"],
    "use_sentiment_features": [
        "anger", "anticipation", "disgust", "fear", "joy", 
        "love", "optimism", "pessimism", "sadness", "surprise", "trust"
    ],
    "use_engagement_features": ["replyCount", "viewCount", "likeCount", "retweetCount"],
    
    "financial_weight": 1.0,
    "sentiment_weight": 1.0,
    "engagement_weight": 1.0,
        
    # Model parameters
    "lstm_units": [160, 120, 80],  
    "dropout_rate": 0.2,  
    "learning_rate": 0.0001,
    "batch_size": 32,
    "epochs": 150,
    "patience": 40,
    
    # Output parameters
    "model_save_path": "sentiment_financial_model_10min_bidir.h5",
    "results_path": "../../results/",
}