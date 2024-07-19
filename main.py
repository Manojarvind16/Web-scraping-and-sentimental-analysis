import streamlit as st
import pandas as pd
from textblob import TextBlob
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('vader_lexicon')

# Function to clean the text
def clean_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    stop_words = set(stopwords.words('english'))
    return ' '.join(word for word in text.split() if word not in stop_words)

# Function to get sentiment score using VADER
def get_vader_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentiment_dict = sid.polarity_scores(text)
    return sentiment_dict['compound']

# Load and process multiple CSV files
def load_data(files):
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        df['cleaned_review'] = df['Review'].apply(clean_text)
        df['vader_sentiment'] = df['cleaned_review'].apply(get_vader_sentiment)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Function to analyze reviews for specific query
def analyze_reviews(df, query):
    query_reviews = df[df['cleaned_review'].str.contains(query, case=False, na=False)]
    if not query_reviews.empty:
        avg_sentiment = query_reviews['vader_sentiment'].mean()
        return avg_sentiment, query_reviews
    else:
        return None, None

# Function to match query with reviews using TF-IDF and cosine similarity
def match_query(df, query):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['cleaned_review'])
    query_vec = vectorizer.transform([query])
    cosine_similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    df['similarity'] = cosine_similarities
    return df.sort_values(by='similarity', ascending=False).head(10)

# File paths
csv_files = [r'C:\Users\manoj\OneDrive\Desktop\Flipkart\Motorola Edge 50 Pro 5G_reviews.csv',
             r'C:\Users\manoj\OneDrive\Desktop\Flipkart\OnePlus 11R 5G_reviews.csv',
             r'C:\Users\manoj\OneDrive\Desktop\Flipkart\POCO X6 Pro 5G_reviews.csv',
             r'C:\Users\manoj\OneDrive\Desktop\Flipkart\realme 12 Pro+ 5G_reviews.csv',
             r'C:\Users\manoj\OneDrive\Desktop\Flipkart\SAMSUNG Galaxy S22 5G_reviews.csv']

# Streamlit App
st.title('Product Review Sentiment Analysis')

# Load data
df = load_data(csv_files)
st.write(df)

# Query Input
query = st.text_input('Enter a query to analyze product reviews (e.g., "best camera quality", "battery life"):')

if query:
    cleaned_query = clean_text(query)
    
    # Analyze reviews for the specific query
    avg_sentiment, query_reviews = analyze_reviews(df, cleaned_query)
    
    if avg_sentiment is not None:
        st.write(f"Average sentiment for reviews mentioning '{query}': {avg_sentiment:.2f}")
        st.write(query_reviews)
        
        # Plot sentiment distribution
        fig, ax = plt.subplots()
        query_reviews['vader_sentiment'].hist(bins=20, ax=ax)
        ax.set_title(f'Sentiment distribution for "{query}"')
        ax.set_xlabel('Sentiment')
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
    else:
        st.write(f"No reviews found mentioning '{query}'.")
    
    # Match query with reviews
    matched_reviews = match_query(df, cleaned_query)
    st.write(f"Top matching reviews for '{query}':")
    st.write(matched_reviews)
