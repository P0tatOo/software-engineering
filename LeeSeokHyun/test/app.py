from flask import Flask, jsonify
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# 데이터베이스 연결 및 데이터 로드
conn = sqlite3.connect('C:\\Users\\LEESEOKHYUN\\Desktop\\data.db', check_same_thread=False)
user_df = pd.read_sql_query("SELECT * FROM user", conn)
movie_df = pd.read_sql_query("SELECT * FROM movie", conn)

def recommend_movies(user_id):
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_age = user['age']
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []
    suitable_movies = movie_df[movie_df['rating'] <= user_age]
    
    if not user_likelist:
        recommended_movies = suitable_movies.sample(n=10)
        return recommended_movies

    liked_movies = movie_df[movie_df['title'].isin(user_likelist)]
    liked_descriptions = liked_movies['description'].tolist()
    vectorizer = TfidfVectorizer().fit_transform(liked_descriptions + suitable_movies['description'].tolist())
    vectors = vectorizer.toarray()
    liked_vectors = vectors[:len(liked_descriptions)]
    movie_vectors = vectors[len(liked_descriptions):]
    similarity_matrix = cosine_similarity(liked_vectors, movie_vectors)
    similarity_scores = similarity_matrix.max(axis=0)
    top_indices = similarity_scores.argsort()[-10:][::-1]
    recommended_movies = suitable_movies.iloc[top_indices]
    return recommended_movies

@app.route('/recommend/<user_id>', methods=['GET'])
def recommend(user_id):
    recommendations = recommend_movies(user_id)
    recommendations['rank'] = range(1, len(recommendations) + 1)
    result = recommendations[['rank', 'title', 'rating', 'description']].to_dict(orient='records')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
