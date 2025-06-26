import spacy
from spacy import displacy
from pathlib import Path
from data.test_data import TEST_DATA


model_path = Path("new_NLP_model/model-best")
nlp = spacy.load(model_path)


correct_predictions = 0
false_predictions = 0
total_sentences = len(TEST_DATA)



for data in TEST_DATA:
    try:
        # Extract sentence and entity information
        sentence = data[0]  # The text
        entities = data[1]  # The entity information
        
        # Get the first entity's position and label
        start, end, label = entities['entities'][0]
        
        # Get the true username from the sentence
        true_username = sentence[start:end]
        
        # Get model prediction
        doc = nlp(sentence)
        predicted_username = doc.ents[0].text if doc.ents else None
        
        # Compare predictions
        is_correct = predicted_username == true_username
        
        # Update statistics
        if is_correct:
            correct_predictions += 1
        else:
            false_predictions += 1
            
        # Visualize the result
        colors = {"USERNAME": "lightgreen"}
        options = {"colors": colors}
        displacy.render(doc, style="ent", options=options)
        
    except Exception as e:
        print(f"Error processing sentence: {sentence}")
        print(f"Error details: {str(e)}")
        continue

# Calculate final accuracy
accuracy = (correct_predictions / total_sentences) * 100

print("\n📊 Testing Results:")
print(f"✅ Correct predictions: {correct_predictions}")
print(f"❌ Incorrect predictions: {false_predictions}")
print(f"📈 Accuracy: {accuracy:.2f}%")

