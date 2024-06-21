from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위해 필요한 비밀 키

# 데이터베이스 연결
conn = sqlite3.connect(r'C:\Users\LEESEOKHYUN\Desktop\data.db', check_same_thread=False)
c = conn.cursor()

# 데이터프레임으로 사용자와 영화 데이터 불러오기
def load_data():
    global user_df, movie_df
    user_df = pd.read_sql_query("SELECT * FROM user", conn)
    movie_df = pd.read_sql_query("SELECT * FROM movie", conn)

load_data()

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

# 수정된 함수: 여러 키워드를 입력받아 가장 유사한 영화를 추천하는 기능 추가
def recommend_movies(user_id, keywords=None):
    # 데이터 갱신
    load_data()
    
    # 사용자 정보 가져오기
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_age = user['age']
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []

    # 사용자의 나이에 맞는 영화 필터링
    suitable_movies = movie_df[movie_df['rating'] <= user_age]

    # 키워드 전처리
    if keywords:
        # 키워드를 공백이나 반점으로 구분하여 처리
        keywords = [kw.strip() for kw in keywords.split(',')]  # 수정된 부분
    else:
        keywords = []

    def filter_movies_by_keywords(movies, keywords):
        if not keywords:
            return movies
        # 키워드가 제목이나 설명에 포함된 영화 필터링 (정확히 일치하는 경우만 필터링)
        return movies[movies.apply(lambda x: any(keyword.lower() in x['title'].lower().split() or keyword.lower() in x['description'].lower().split() for keyword in keywords), axis=1)]

    def count_keyword_matches(description, keywords):
        count = 0
        for keyword in keywords:
            if keyword.lower() in description.lower().split():
                count += 1
        return count

    def highlight_keywords(text, keywords):
        for keyword in keywords:
            text = text.replace(keyword, f'<span style="color: red;">{keyword}</span>')
        return text

    # 시나리오 1: Likelist가 비어있고 키워드도 있는 경우
    if not user_likelist and keywords:
        # 키워드가 포함된 영화 필터링
        keyword_movies = filter_movies_by_keywords(suitable_movies, keywords)  # 수정된 부분

        # 키워드가 포함된 영화가 있는지 확인
        if not keyword_movies.empty:
            keyword_movies['keyword_matches'] = keyword_movies['description'].apply(lambda desc: count_keyword_matches(desc, keywords))  # 수정된 부분
            keyword_movies = keyword_movies.sort_values(by='keyword_matches', ascending=False)  # 수정된 부분
            keyword_movies['description'] = keyword_movies['description'].apply(lambda desc: highlight_keywords(desc, keywords))  # 키워드 하이라이트
            recommended_movies = keyword_movies.head(10)
            return recommended_movies
        else:
            random_movies = suitable_movies.sample(n=10)
            return random_movies  # 키워드가 없을 때 랜덤으로 10개 추천

    # 시나리오 2: Likelist가 존재하고 키워드도 있는 경우
    elif user_likelist and keywords:
        # 좋아하는 영화들의 설명 가져오기
        liked_movies = movie_df[movie_df['title'].isin(user_likelist)]
        liked_descriptions = liked_movies['description'].tolist()

        # 키워드가 포함된 영화 필터링
        keyword_movies = filter_movies_by_keywords(suitable_movies, keywords)  # 수정된 부분

        # TF-IDF 및 코사인 유사도 계산
        if not keyword_movies.empty:
            keyword_movies['keyword_matches'] = keyword_movies['description'].apply(lambda desc: count_keyword_matches(desc, keywords))  # 수정된 부분
            keyword_movies = keyword_movies.sort_values(by='keyword_matches', ascending=False)  # 수정된 부분
            keyword_movies['description'] = keyword_movies['description'].apply(lambda desc: highlight_keywords(desc, keywords))  # 키워드 하이라이트
            recommended_movies = keyword_movies.head(10)
            return recommended_movies
        else:
            return pd.DataFrame({"title": ["입력한 키워드에 해당하는 영화가 없습니다."]})

    # 시나리오 3: Likelist가 비어있고 키워드도 없는 경우
    elif not user_likelist and not keywords:
        # 나이에 맞게 10개 영화 랜덤으로 추천
        return suitable_movies.sample(n=10)  # 수정된 부분

    # 시나리오 4: Likelist가 존재하고 키워드도 없는 경우
    else:
        # 좋아하는 영화들의 설명 가져오기
        liked_movies = movie_df[movie_df['title'].isin(user_likelist)]
        liked_descriptions = liked_movies['description'].tolist()

        # TF-IDF 및 코사인 유사도 계산
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
    keyword = request.form.get('keyword') if request.method == 'POST' else session.get('keyword')
    if request.method == 'POST':
        session['keyword'] = keyword
    recommendations = recommend_movies(user_id, keyword)
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []
    return render_template('index.html', recommendations=recommendations, user_likelist=user_likelist)

@app.route('/my_list')
def my_list():
    user_id = 'id123'  # 예시 사용자 ID
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []
    if user_likelist:
        my_list_movies = movie_df[movie_df['title'].isin(user_likelist)]
        return render_template('my_list.html', my_list_movies=my_list_movies if not my_list_movies.empty else None)
    else:
        return render_template('my_list.html', my_list_movies=None)

@app.route('/movie/<title>')
def movie(title):
    user_id = 'id123'  # 예시 사용자 ID
    user = user_df[user_df['id'] == user_id].iloc[0]
    user_likelist = user['likelist'].strip(',').split(', ') if user['likelist'] else []
    movie = movie_df[movie_df['title'] == title].iloc[0]
    is_liked = title in user_likelist
    session['last_page'] = request.referrer
    return render_template('movie.html', movie=movie, is_liked=is_liked)

@app.route('/back')
def back():
    last_page = session.get('last_page', url_for('index'))
    if 'my_list' in last_page:
        return redirect(url_for('my_list'))
    return redirect(last_page)

@app.route('/toggle_like', methods=['POST'])
def toggle_like():
    user_id = 'id123'  # 예시 사용자 ID
    title = request.json['title']
    is_liked = request.json['is_liked']

    if is_liked:
        add_to_list(user_id, title)
    else:
        del_from_list(user_id, title)

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
