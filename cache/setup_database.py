import sqlite3
import os
from datetime import datetime

def setup_database():
    db_file = 'UserData.db'
    
    # 检查数据库文件是否存在
    if os.path.exists(db_file):
        print(f"Database {db_file} already exists.")
        return
    
    # 创建新的数据库连接
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 创建 content 表
    cursor.execute('''
    CREATE TABLE content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        added_time TEXT NOT NULL,
        type TEXT,
        item TEXT,
        location TEXT,
        location_start TEXT,
        location_end TEXT,
        date TEXT,
        time TEXT,
        people TEXT,
        serial_number TEXT,
        status TEXT,
        total_amount REAL,
        currency_type TEXT,
        NER TEXT NOT NULL,
        additional_info TEXT
    )
    ''')
    
    # 创建 type 表
    cursor.execute('''
    CREATE TABLE type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supersets TEXT NOT NULL,
        subsets TEXT
    )
    ''')
    
    # 插入 type 表的数据
    type_data = [
        ('ticket', 'flight ticket, train ticket'),
        ('receipt', None),
        ('content', 'post, web article, book')
    ]
    cursor.executemany('INSERT INTO type (supersets, subsets) VALUES (?, ?)', type_data)
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    print(f"Database {db_file} created successfully with required tables and data.")

# 运行函数
setup_database()