import sys
import re
from sklearn.feature_extraction.text import TfidfVectorizer

def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        paragraphs = file.read().split('\n\n')  # Split paragraphs by empty lines 
        # Text1 = pre text; Text2 = post text
    return paragraphs

def custom_tokenizer(text):
    # Treating appostrophes correclty
    return re.findall(r"\b[a-zA-Z0-9]+(?:'\w+)?\b", text)

def perform_tfidf(texts):
    vectorizer = TfidfVectorizer(tokenizer=custom_tokenizer)
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()
    results = {}
    for i, text in enumerate(texts):
        feature_index = tfidf_matrix[i, :].nonzero()[1]
        tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
        tfidf_values = {feature_names[i]: score for i, score in tfidf_scores}
        # Sort the terms by TF-IDF score in descending order
        sorted_tfidf_values = {k: v for k, v in sorted(tfidf_values.items(), key=lambda item: item[1], reverse=True)}
        results[f"Text {i + 1}"] = sorted_tfidf_values
    return results

def print_tfidf_results(file_name, results):
    print("-"*30)
    print(f"\nResults for {file_name}:")
    for text, tfidf_values in results.items():
        print(f"{text}:")
        # Print only the top 20 terms
        for idx, (term, score) in enumerate(tfidf_values.items()):
            if idx == 20:
                break
            print(f"  {term}: {score:.4f}")
        print()

if len(sys.argv) < 2:
    print(f"Usage: python {sys.argv[0]} <file_path1> <file_path2> ...")
    sys.exit(1)

file_paths = sys.argv[1:]
for file_path in file_paths:
    paragraphs = read_text_from_file(file_path)
    tfidf_results = perform_tfidf(paragraphs)
    print_tfidf_results(file_path, tfidf_results)
