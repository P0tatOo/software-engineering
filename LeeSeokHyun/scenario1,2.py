import sqlite3
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 데이터베이스 연결
conn = sqlite3.connect(r'C:\Users\LEESEOKHYUN\Desktop\data.db')
c = conn.cursor()

# 데이터프레임으로 사용자와 영화 데이터 불러오기
user_df = pd.read_sql_query("SELECT * FROM user", conn)
movie_df = pd.read_sql_query("SELECT * FROM movie", conn)

def del_from_list(id, title):
    title = title + ', '
    c.execute('SELECT * FROM user WHERE id = ?', (id, ))
    getList = c.fetchone()[3]
    newList = getList.replace(title, '')
    c.execute('UPDATE user SET likelist = ? WHERE id = ?', (newList, id))
    conn.commit()

# Likelist에서 특정 항목 추가 함수
def add_to_list(id, title):
    title = title + ', '
    c.execute('SELECT * FROM user WHERE id = ?', (id, ))
    getList = c.fetchone()[3]
    newList = getList + title
    c.execute('UPDATE user SET likelist = ? WHERE id = ?', (newList, id))
    conn.commit()

def recommend_movies(user_id, keyword=None):
    # 사용자 정보 가져오기
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_age = user['age']
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []

    # 사용자의 나이에 맞는 영화 필터링
    suitable_movies = movie_df[movie_df['rating'] <= user_age]

    # 시나리오 1: Likelist가 비어있고 키워드도 없는 경우
    if not user_likelist and not keyword:
        recommended_movies = suitable_movies.sample(n=10)
        return recommended_movies

    # 시나리오 2: Likelist가 존재하고 키워드는 없는 경우
    elif user_likelist and not keyword:
        # 좋아하는 영화들의 설명 가져오기
        liked_movies = movie_df[movie_df['title'].isin(user_likelist)]
        liked_descriptions = liked_movies['description'].tolist()

        # TF-IDF 및 코사인 유사도 계산
        vectorizer = TfidfVectorizer().fit_transform(liked_descriptions + suitable_movies['description'].tolist())
        vectors = vectorizer.toarray()
        liked_vectors = vectors[:len(liked_descriptions)]
        movie_vectors = vectors[len(liked_descriptions):]

        # 코사인 유사도 계산
        similarity_matrix = cosine_similarity(liked_vectors, movie_vectors)
        similarity_scores = similarity_matrix.max(axis=0)
        
        # 유사도가 높은 상위 10개 영화 가져오기
        top_indices = similarity_scores.argsort()[-10:][::-1]
        recommended_movies = suitable_movies.iloc[top_indices]
        return recommended_movies

# 예시 사용법:
user_id = 'id123'
recommendations = recommend_movies(user_id)

# 추천 결과를 표 형식으로 보여주는 함수
def display_recommendations_table(recommendations):
    # 추천 영화에 순위(rank) 추가
    recommendations['rank'] = range(1, len(recommendations) + 1)
    
    # 추천 결과를 표 형식으로 출력
    result = recommendations[['rank', 'title', 'rating', 'description']]
    print(result)

# 추천 결과 출력
display_recommendations_table(recommendations)
