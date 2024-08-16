import base64
from PIL import Image
import io
from openai import OpenAI
import json
import re
from ltp import LTP,StnSplit
# from pydantic import BaseModel, ValidationError
import sqlite3
import os
from datetime import datetime

from config import openai_api_base, openai_api_key
from prompt import generate_img_prompt,generate_data_prompt,generate_json_from_image_prompt


client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format=image.format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_img(img_url):
    query = generate_img_prompt
    
    try:
        print(f">>>Processing image: {img_url}")
        image = Image.open(img_url)
        base64_image = encode_image_to_base64(image)
        print(">>>Image encoded successfully")
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }]
        
        print(">>>Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2048,
        )
        
        result = response.choices[0].message.content
        print(">>>generate_img output:")
        print(result)
        return result
    
    except Exception as e:  
        error_message = f">>>Error processing image: {str(e)}<<<"
        print(error_message)
        return error_message

def generate_data(result_sum):
    prompt = generate_data_prompt

    try:
        print(">>>Generating structured data from summary...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant that extracts structured json data from text.{prompt}"},
                {"role": "user", "content": result_sum}
            ],
            temperature=0.2,
            response_format={"type":"json_object"},
            max_tokens=2048
        )

        raw_response = response.choices[0].message.content.strip()
        # print(">>>Raw output from GPT:")
        # print(raw_response)

        # 使用正则表达式提取 JSON 部分
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            json_str = json_match.group()
            # print(">>>Extracted JSON string:")
            # print(json_str)
            try:
                # 预处理 JSON 字符串
                json_str = re.sub(r'\s+', ' ', json_str)  # 将多个空白字符替换为单个空格
                json_str = json_str.replace('\n', ' ')    # 移除换行符
                data = json.loads(json_str)
                print(">>>Parsed JSON data:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            except json.JSONDecodeError as e:
                print(f">>>Error parsing JSON: {str(e)}")
                return {"error": "Failed to parse JSON from GPT response"}
        else:
            print(">>>No valid JSON found in GPT response")
            return {"error": "No valid JSON found in GPT response"}

    except Exception as e:
        error_message = f"Error processing data: {str(e)}"
        print(f">>>Error in generate_data: {error_message}")
        return {"error": error_message}

def NER(text):
    # 初始化LTP模型
    ltp = LTP()
    
    # 使用StnSplit进行分句
    stn_split = StnSplit()
    sentences = stn_split.split(text)
    
    # 对整个文本进行处理
    result = ltp.pipeline(sentences, tasks=["cws", "pos", "ner"])
    
    # 提取所有命名实体，只保留实体名称
    entities = []
    for sentence_ner in result.ner:
        for entity in sentence_ner:
            _, entity_name, _, _ = entity
            entities.append(entity_name)
    
    print(">>>entities:", entities)
    return entities

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
    
    print(f">>>Database {db_file} created successfully with required tables and data.")

def save_to_database(data):
    db_file = 'UserData.db'
    
    # 连接到数据库，并设置 text_factory
    conn = sqlite3.connect(db_file)
    conn.text_factory = str  # 这将确保文本以 UTF-8 格式存储
    cursor = conn.cursor()
    
    try:
        # 准备插入数据
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 处理 people 列表
        if isinstance(data.get('people'), list):
            people = json.dumps(data['people'], ensure_ascii=False)
        else:
            people = data.get('people')
        
        # 准备 SQL 语句
        sql = '''
        INSERT INTO content (
            added_time, type, item, location, location_start, location_end,
            date, time, people, serial_number, status, total_amount,
            currency_type, NER, additional_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # 准备数据元组
        values = (
            current_time,
            data.get('type'),
            data.get('item'),
            data.get('location'),
            data.get('location_start'),
            data.get('location_end'),
            data.get('date'),
            data.get('time'),
            people,
            data.get('serial_number'),
            data.get('status'),
            data.get('total_amount'),
            data.get('currency_type'),
            json.dumps(data.get('NER', []), ensure_ascii=False),  # 确保 NER 也正确编码
            data.get('additional_info')
        )
        
        # 执行插入操作
        cursor.execute(sql, values)
        
        # 提交事务
        conn.commit()
        print(">>>Data successfully saved to database.")
    
    except Exception as e:
        print(f">>>Error saving data to database: {str(e)}")
        conn.rollback()
    
    finally:
        # 关闭连接
        conn.close()


if __name__ == "__main__":
    img_url = input(">>>Drop img here:").strip().strip("'\"")
    print(f"Final image path: {img_url}")
    print(">>>Starting process...")
    result_sum = generate_img(img_url)
    result_sum = result_sum + "NER:" + str(NER(result_sum))
    print(">>>Generating structured data...")
    result_data = generate_data(result_sum)
    print(">>>result:")
    print(json.dumps(result_data, indent=2, ensure_ascii=False))
    setup_database()
    save_to_database(result_data)