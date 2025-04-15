from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-emotion-multilabel-latest")
model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-emotion-multilabel-latest")

# Initialize the pipeline
emotion_classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, top_k=None)

# Define emotion labels
labels = ["anger", "anticipation", "disgust", "fear", "joy", "love", "optimism", "pessimism", "sadness", "surprise", "trust"]

def getTextSentiment(text):
    # Classify the given text
    results = emotion_classifier(text)
    emotion_scores = {label: 0 for label in labels}  # Initialize the sentiment dictionary
    emotion_scores = {r['label'].lower(): r['score'] for r in results[0]}
    return emotion_scores

# # Example usage
# text = "Bought some $TSLA and started my first ever ETF dividends portfolio :beaming_face_with_smiling_eyes:"
# sentiment_scores = getTextSentiment(text)

# print(sentiment_scores)
# # Display results
# print(f"Text: {text}")
# for emotion, score in sentiment_scores.items():
#     print(f"  {emotion}: {score:.4f}")
