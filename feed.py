import base64
from PIL import Image
import io
from openai import OpenAI
import json
import re
from ltp import LTP, StnSplit
import sqlite3
import os
from datetime import datetime

from config import openai_api_base, openai_api_key
from prompt import generate_img_prompt, generate_data_prompt, generate_json_from_image_prompt

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

def get_types_from_db():
    db_file = 'UserData.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT supersets, subsets FROM type')
        types = cursor.fetchall()
        return {supersets: subsets.split(', ') if subsets else [] for supersets, subsets in types}
    except sqlite3.OperationalError:
        print("Warning: 'type' table not found. Creating default types.")
        setup_database()
        cursor.execute('SELECT supersets, subsets FROM type')
        types = cursor.fetchall()
        return {supersets: subsets.split(', ') if subsets else [] for supersets, subsets in types}
    finally:
        conn.close()

def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format=image.format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_img(img_url):
    types = get_types_from_db()
    type_examples = ', '.join(types.keys())
    
    query = generate_img_prompt.replace(
        "ticket, receipt, content",
        f"{type_examples}. If none of these fit, you may suggest a new type."
    )

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
            model="gpt-4o",
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
    types = get_types_from_db()
    type_examples = ', '.join(types.keys())
    
    prompt = generate_data_prompt.replace(
        '"type": Use "ticket" (including flight, train tickets), "receipt", or "content" (for posts, articles, books)',
        f'"type": Use one of the following types: {type_examples}. If none fit, suggest a new type.'
    )

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
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            json_str = json_match.group()
            try:
                json_str = re.sub(r'\s+', ' ', json_str)
                json_str = json_str.replace('\n', ' ')
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
    ltp = LTP()
    stn_split = StnSplit()
    sentences = stn_split.split(text)
    result = ltp.pipeline(sentences, tasks=["cws", "pos", "ner"])
    
    entities = []
    for sentence_ner in result.ner:
        for entity in sentence_ner:
            _, entity_name, _, _ = entity
            entities.append(entity_name)
    
    print(">>>entities:", entities)
    return entities

def setup_database():
    db_file = 'UserData.db'
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supersets TEXT NOT NULL,
        subsets TEXT
    )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM type')
    if cursor.fetchone()[0] == 0:
        type_data = [
            ('ticket', 'flight ticket, train ticket'),
            ('receipt', 'invoice'),
            ('content', 'post, web article, book')
        ]
        cursor.executemany('INSERT INTO type (supersets, subsets) VALUES (?, ?)', type_data)
    
    conn.commit()
    conn.close()
    
    print(f">>>Database {db_file} setup completed.")

def save_to_database(data):
    db_file = 'UserData.db'
    
    conn = sqlite3.connect(db_file)
    conn.text_factory = str
    cursor = conn.cursor()
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if isinstance(data.get('people'), list):
            people = json.dumps(data['people'], ensure_ascii=False)
        else:
            people = data.get('people')
        
        sql = '''
        INSERT INTO content (
            added_time, type, item, location, location_start, location_end,
            date, time, people, serial_number, status, total_amount,
            currency_type, NER, additional_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
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
            json.dumps(data.get('NER', []), ensure_ascii=False),
            data.get('additional_info')
        )
        
        cursor.execute(sql, values)
        
        content_type = data.get('type')
        item = data.get('item')
        if content_type and item:
            cursor.execute('SELECT supersets, subsets FROM type WHERE supersets = ?', (content_type,))
            existing_type = cursor.fetchone()
            
            if existing_type:
                _, subsets = existing_type
                if subsets:
                    subset_list = [s.strip() for s in subsets.split(',')]
                    if item not in subset_list:
                        subset_list.append(item)
                        new_subsets = ', '.join(subset_list)
                        cursor.execute('UPDATE type SET subsets = ? WHERE supersets = ?', (new_subsets, content_type))
                else:
                    cursor.execute('UPDATE type SET subsets = ? WHERE supersets = ?', (item, content_type))
            else:
                cursor.execute('INSERT INTO type (supersets, subsets) VALUES (?, ?)', (content_type, item))
        
        conn.commit()
        print(">>>Data successfully saved to database and type table updated if necessary.")
    
    except Exception as e:
        print(f">>>Error saving data to database: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()  # Ensure database is set up before any operations
    
    img_url = input(">>>Drop img here:").strip().strip("'\"")
    print(f"Final image path: {img_url}")
    print(">>>Starting process...")
    result_sum = generate_img(img_url)
    result_sum = result_sum + "NER:" + str(NER(result_sum))
    print(">>>Generating structured data...")
    result_data = generate_data(result_sum)
    print(">>>result:")
    print(json.dumps(result_data, indent=2, ensure_ascii=False))
    save_to_database(result_data)
