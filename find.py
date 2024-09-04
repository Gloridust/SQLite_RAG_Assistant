import sqlite3
import json
from openai import OpenAI
from config import openai_api_base, openai_api_key
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

def get_db_structure():
    conn = sqlite3.connect('UserData.db')
    cursor = conn.cursor()

    # Get type table data
    cursor.execute("SELECT * FROM type")
    type_data = cursor.fetchall()
    type_structure = [{"id": row[0], "supersets": row[1], "subsets": row[2]} for row in type_data]

    # Get content table structure
    cursor.execute("PRAGMA table_info(content)")
    content_structure = [col[1] for col in cursor.fetchall()]

    conn.close()

    return json.dumps({"type": type_structure, "content": content_structure})

def generate_sql_query(user_query, db_structure):
    prompt = f"""
    Given the following database structure and user query, generate an SQL query to fetch the relevant information.
    
    Database Structure:
    {db_structure}
    
    User Query: "{user_query}"
    
    Generate an SQL query that:
    1. Uses the 'content' table
    2. Incorporates fuzzy matching using LIKE statements
    3. Uses OR conditions to broaden the search when appropriate
    4. Always includes a search in the 'additional_info' column
    5. Orders the results by date (most recent first) if applicable
    6. Limits the results to 5 entries

    Return only the SQL query, without any explanation or additional text.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an SQL expert. Generate SQL queries based on natural language requests and database structures."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()

def execute_query(sql_query):
    conn = sqlite3.connect('UserData.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return [dict(zip(column_names, row)) for row in results]
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.close()

def format_results(results):
    if not results:
        return "No results found."

    formatted_output = ""
    for item in results:
        formatted_output += "\n--- Result ---\n"
        for key, value in item.items():
            if key == 'added_time':
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
            formatted_output += f"{key}: {value}\n"
    
    return formatted_output

def main():
    user_query = input("Enter your query: ")
    db_structure = get_db_structure()
    sql_query = generate_sql_query(user_query, db_structure)
    print(f"\nGenerated SQL Query:\n{sql_query}\n")
    
    results = execute_query(sql_query)
    if results:
        formatted_results = format_results(results)
        print(formatted_results)
    else:
        print("No results found or an error occurred.")

if __name__ == "__main__":
    main()