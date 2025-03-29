from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

# Load pretrained goemotion model and tokenizer
modelName = "monologg/bert-base-cased-goemotions-original"
tokenizer = AutoTokenizer.from_pretrained(modelName)
model = AutoModelForSequenceClassification.from_pretrained(modelName)
print("Model successfully loaded!")

# 28 Labels from GoEmotion
goemotionsLabels = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval", "disgust",
    "embarrassment", "excitement", "fear", "gratitude", "grief", "joy", "love",
    "nervousness", "optimism", "pride", "realization", "relief", "remorse",
    "sadness", "surprise", "neutral"
]

# Map labels to 10 categories (simplify model)
emotionMapping = {
    "Positive": ["amusement", "excitement", "joy", "love"],
    "Hopeful": ["desire", "optimism", "caring"],
    "Pride": ["pride", "admiration", "gratitude", "relief"],
    "Approval": ["approval", "realization"],
    "Curiosity": ["surprise", "curiosity", "confusion"],
    "Fear": ["fear", "nervousness"],
    "Remorse": ["remorse", "embarrassment"],
    "Sadness": ["disappointment", "sadness", "grief"],
    "Disapproval": ["disgust", "anger", "annoyance", "disapproval"],
    "Neutral": ["neutral"]
}


def getTextSentiment(text):
    # Tokenize the text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

    # # Convert the input IDs back into tokens
    # tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])

    # # Print the tokens
    # print("Tokens:", tokens)

    # Get predictions (logits)
    with torch.no_grad():
        outputs = model(**inputs)

    # Convert logits to probabilities using softmax
    scores = torch.nn.functional.softmax(outputs.logits, dim=1)[0].tolist()

    # Map each emotion score to its corresponding label
    emotionScores = {label: scores[i] for i, label in enumerate(goemotionsLabels)}

    # Map to custom labels
    customScores = {category: 0 for category in emotionMapping}  # Initialize with zeros
    for category, emotions in emotionMapping.items():
        for emotion in emotions:
            if emotion in emotionScores:
                customScores[category] += emotionScores[emotion]

    return customScores






# Example usage
# tweet = "I hope $TSLA stock increases"
tweet = "I wish $TSLA will go up in price. I hate how thing are going right now. I believe this harsh reality is temporary."
sentimentScores = getTextSentiment(tweet)

print("Sentiment Scores for Tweet:")
print(sentimentScores)
