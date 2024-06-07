from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위해 필요한 비밀 키

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

    # 시나리오 1: Likelist가 비어있고 키워드도 있는 경우
    if not user_likelist and keyword:
        keyword_movies = movie_df[movie_df['description'].str.contains(keyword, case=False)]

        if not keyword_movies.empty:
            vectorizer = TfidfVectorizer().fit_transform(keyword_movies['description'].tolist() + suitable_movies['description'].tolist())
            vectors = vectorizer.toarray()
            keyword_vectors = vectors[:len(keyword_movies)]
            movie_vectors = vectors[len(keyword_movies):]

            similarity_matrix = cosine_similarity(keyword_vectors, movie_vectors)
            similarity_scores = similarity_matrix.max(axis=0)

            top_indices = similarity_scores.argsort()[-10:][::-1]
            recommended_movies = suitable_movies.iloc[top_indices]
            return recommended_movies
        else:
            return pd.DataFrame({"title": ["입력한 키워드에 해당하는 영화가 없습니다."]})

    # 시나리오 2: Likelist가 존재하고 키워드도 있는 경우
    elif user_likelist and keyword:
        liked_movies = movie_df[movie_df['title'].isin(user_likelist)]
        liked_descriptions = liked_movies['description'].tolist()

        keyword_movies = movie_df[movie_df['description'].str.contains(keyword, case=False)]

        if not keyword_movies.empty:
            vectorizer = TfidfVectorizer().fit_transform(liked_descriptions + keyword_movies['description'].tolist() + suitable_movies['description'].tolist())
            vectors = vectorizer.toarray()
            liked_vectors = vectors[:len(liked_descriptions)]
            keyword_vectors = vectors[len(liked_descriptions):len(liked_descriptions)+len(keyword_movies)]
            movie_vectors = vectors[len(liked_descriptions)+len(keyword_movies):]

            similarity_matrix = cosine_similarity(keyword_vectors, movie_vectors)
            similarity_scores = similarity_matrix.max(axis=0)

            top_indices = similarity_scores.argsort()[-10:][::-1]
            recommended_movies = suitable_movies.iloc[top_indices]
            return recommended_movies
        else:
            return pd.DataFrame({"title": ["입력한 키워드에 해당하는 영화가 없습니다."]})

    # 시나리오 3: Likelist가 비어있고 키워드도 없는 경우
    elif not user_likelist and not keyword:
        return suitable_movies.head(10)

    # 시나리오 4: Likelist가 존재하고 키워드도 없는 경우
    else:
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

@app.route('/', methods=['GET', 'POST'])
def index():
    user_id = 'id123'  # 예시 사용자 ID
    keyword = request.form.get('keyword') if request.method == 'POST' else None
    if keyword:
        session['keyword'] = keyword  # 키워드를 세션에 저장
    recommendations = recommend_movies(user_id, keyword)
    return render_template('index.html', recommendations=recommendations)

@app.route('/my_list')
def my_list():
    user_id = 'id123'  # 예시 사용자 ID
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []
    if user_likelist:
        my_list_movies = movie_df[movie_df['title'].isin(user_likelist)]
        return render_template('my_list.html', my_list_movies=my_list_movies)
    else:
        return render_template('my_list.html', my_list_movies=None)

@app.route('/movie/<title>')
def movie(title):
    movie = movie_df[movie_df['title'] == title].iloc[0]
    return render_template('movie.html', movie=movie)

@app.route('/back')
def back():
    keyword = session.get('keyword', None)
    return redirect(url_for('index', keyword=keyword))

if __name__ == '__main__':
    app.run(debug=True)
