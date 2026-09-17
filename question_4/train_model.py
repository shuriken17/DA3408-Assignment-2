import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

df = pd.read_csv("spam_dataset.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df["text"].tolist(), df["label"].tolist(),
    test_size=0.2, random_state=42, stratify=df["label"].tolist(),
)

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
    ("nb", MultinomialNB(alpha=0.1)),
])
pipe.fit(X_train, y_train)

preds = pipe.predict(X_test)
print(f"accuracy: {accuracy_score(y_test, preds):.4f}")
print(classification_report(y_test, preds))

joblib.dump(pipe, "model.joblib")
print("saved pipeline : model.joblib")
