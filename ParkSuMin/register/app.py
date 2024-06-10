from flask import Flask, render_template, request, redirect, session
import sqlite3 as db

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db_connection():
    conn = db.connect('data.db')
    return conn

# 로그인 함수
def log_in(id: str, pw: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, pw FROM user WHERE id = ? AND pw = ?', (id, pw))
    rr = c.fetchone()
    conn.close()
    if rr is None:
        return False, "아이디 또는 비밀번호가 올바르지 않습니다."
    else:
        return True, "로그인 성공"

# 회원가입 함수
def register(id: str, pw: str, confirm_pw: str, age: int):
    if pw != confirm_pw:
        return False, "비밀번호와 비밀번호 확인 값이 일치하지 않습니다."
    
    if age < 1 or age > 999:
        return False, "나이 값이 올바르지 않습니다."
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM user WHERE id = ?', (id,))
        if c.fetchone():
            conn.close()
            return False, "이미 사용 중인 아이디입니다."
        
        c.execute('INSERT INTO user (id, pw, age) VALUES (?, ?, ?)', (id, pw, age))
        conn.commit()
        conn.close()
        return True, "회원가입 성공"
    except db.Error as e:
        return False, f"데이터베이스 오류: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    login_error = ""
    signup_error = ""
    
    if request.method == 'POST':
        if 'loginUsername' in request.form:
            username = request.form['loginUsername']
            password = request.form['loginPassword']
            success, message = log_in(username, password)
            if success:
                session['username'] = username
                return redirect('/welcome')
            else:
                login_error = message
        elif 'signupUsername' in request.form:
            username = request.form['signupUsername']
            password = request.form['signupPassword']
            confirm_password = request.form['confirmPassword']
            age = int(request.form['age'])
            success, message = register(username, password, confirm_password, age)
            if success:
                session['username'] = username
                return redirect('/welcome')
            else:
                signup_error = message
                return render_template('index.html', login_error=login_error, signup_error=signup_error, show_signup_form=True)
    
    return render_template('index.html', login_error=login_error, signup_error=signup_error, show_signup_form=False)

@app.route('/welcome')
def welcome():
    if 'username' in session:
        return f"환영합니다, {session['username']}님!"
    else:
        return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', message="페이지를 찾을 수 없습니다.", error_color="red"), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', message="서버 내부 오류가 발생했습니다.", error_color="red"), 500

if __name__ == '__main__':
    app.run(debug=True)
