import sqlite3
import json
import re
from datetime import datetime
from openai import OpenAI
from config import openai_api_base, openai_api_key

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
    content_structure = [column[1] for column in cursor.fetchall()]

    conn.close()

    return json.dumps({
        "type_table": type_structure,
        "content_table_columns": content_structure
    })

def clean_sql_query(query):
    # Remove Markdown code block syntax
    query = re.sub(r'```sql\s*|\s*```', '', query)
    # Remove any leading/trailing whitespace
    query = query.strip()
    return query

def generate_sql_query(user_question, db_structure):
    prompt = f"""
Given the following database structure and user question, generate an SQL query to retrieve relevant information.
The query should use fuzzy matching (LIKE operator) and connect multiple conditions with OR where appropriate.
Always include the 'additional_info' column in the SELECT statement.
Order the results by date (most recent first) and limit to 5 results.
Use 'content' as the table name, not 'content_table'.

Database structure:
{db_structure}

User question: "{user_question}"

Generate only the SQL query without any additional text, explanation, or Markdown formatting.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a SQL query generator. Output only the SQL query without any formatting or explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    return clean_sql_query(response.choices[0].message.content.strip())

def execute_query(query):
    conn = sqlite3.connect('UserData.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def generate_response(user_question, query_results):
    results_str = json.dumps(query_results, ensure_ascii=False, indent=2)
    prompt = f"""
Based on the user's question and the database query results, generate a concise and informative answer.
If no relevant information is found, politely inform the user.

User question: "{user_question}"

Query results:
{results_str}

Provide a natural language response to the user's question based on the query results.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant providing information based on database query results."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

def main():
    user_question = input("请输入你的问题: ")
    db_structure = get_db_structure()
    sql_query = generate_sql_query(user_question, db_structure)
    print("Generated SQL query:")
    print(sql_query)
    query_results = execute_query(sql_query)
    response = generate_response(user_question, query_results)
    print("\n回答：")
    print(response)

if __name__ == "__main__":
    main()