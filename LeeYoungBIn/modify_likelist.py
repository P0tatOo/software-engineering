import sqlite3 as sql

conn = sql.connect("data.db")
c = conn.cursor()
id = "id123"
del_title = "Paranoia"    #삭제할 작품 제목
add_title = "Jaws"        #추가할 작품 제목

#LikeList에서 특정 항목 제거 함수
def del_from_list(id, title):
    title = title + ', '
    c.execute('SELECT * FROM user WHERE id = ?', (id, ))
    getList = c.fetchone()[3]
    newList = getList.replace(title, '')
    c.execute('UPDATE user SET likelist = ? WHERE id = ?', (newList, id))
    conn.commit()

#Likelist에서 특정 항목 추가 함수
def add_to_list(id, title):
    title = title + ', '
    c.execute('SELECT * FROM user WHERE id = ?', (id, ))
    getList = c.fetchone()[3]
    newList = getList+title
    c.execute('UPDATE user SET likelist = ? WHERE id = ?', (newList, id))
    conn.commit()

#테스트용 임시 코드
#del_from_list(id, del_title)
#add_to_list(id, add_title)
