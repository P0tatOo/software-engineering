import sqlite3 as db

conn = db.connect('data.db')
c = conn.cursor()

check_id_flag = 0

def log_in(id: str, pw: str):
    c.execute('SELECT id, pw, age, likelist FROM user WHERE id = ?', (id,))
    rr = c.fetchone()
    if rr is None:
        print("아이디 없음")
    else:
        stored_pw = rr[1]
        if stored_pw == pw:
            print("성공")
        else:
            print("비밀번호 불일치")

def check_id_in(id: str):
    global check_id_flag
    check_id_flag = 0
    c.execute('SELECT id FROM user WHERE id = ?', (id,))
    rr = c.fetchone()
    if rr is not None:
        check_id_flag = -1
    else:
        check_id_flag = 1

def register(id: str, pw: str, age: int, likelist: str):
    if check_id_flag == 0:
        print("회원가입 실패: 중복 확인을 먼저 진행해주세요.")
        return
    try:
        if check_id_flag == -1:
            print("회원가입 실패: 중복된 ID가 존재합니다.")
            return
        if check_id_flag == 1:
            c.execute('INSERT INTO user (id, pw, age, likelist) VALUES (?, ?, ?, ?)', (id, pw, age, likelist))
            conn.commit()
            print("회원가입 성공")
    except db.IntegrityError:
        print("회원가입 실패: 중복된 ID가 존재합니다.")

def go_to_register_screen():
    global check_id_flag
    check_id_flag = 0

# 함수 호출 예시
go_to_register_screen()

c.close()
conn.close()
