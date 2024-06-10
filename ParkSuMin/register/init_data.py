import sqlite3 as db

def init_db():
    conn = db.connect('data.db')
    c = conn.cursor()

    # user 테이블 생성
    c.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id TEXT PRIMARY KEY,
        pw TEXT NOT NULL,
        age INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
