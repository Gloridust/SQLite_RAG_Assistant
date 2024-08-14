import base64
from PIL import Image
import io
from openai import OpenAI
from config import openai_api_base, openai_api_key
import json
import re

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format=image.format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_img(img_url):
    query = '''
    Extract key information that may be contained in the main interface of the image, maybe including but not limited to: Critical time, location, people, summary, order, ticket, or purchase, etc. 
    Provide a summary, focusing on: type of the event, person related, serial number, status (if finished), total amount and currency, date and time,location (destination for travel, delivery address for shopping, etc.),and any other crucial information. 
    Summarize these details concisely, highlighting the relevant information for each category.
    '''
    
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
            max_tokens=1024,
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
    prompt = """
    Based on the following summary, extract and structure the information into a JSON format that matches our database schema. 
    Fill in as much useful information as possible in the corresponding places Directly and succinctly. If any field is not applicable or the information is not available, use null. 
    Output in the following JSON structure, without any additional text.

    {
        "type": string or null,
        "item": string or null,
        "location": string or null,
        "location_start": string or null,
        "location_end": string or null,
        "date": string or null,
        "time": string or null,
        "people": list or null,
        "serial_number": string or null,
        "status": string or null,
        "total_amount": number or null,
        "currency_type": string or null,
        "additional_info": string or null
    }

    Ensure that:
    - "type" is content type. Possible values: ORDER(flight ticket, train ticket, restaurant order, etc), PURCHASE_RECEIPT, CONTENT(twitter post, web article, book, etc); 
    - "item" is the related item, such as item purchased, the name of the event, etc;
    - "location" is the location and detailed address when the event started;
    - "location_start" is the beginning location of a trip;
    - "location_end" is the end location of a trip;
    - "currency_type" is three letters of currency such as CNY, USD, JPY;
    - "date" is in ISO 8601 format (YYYY-MM-DD), and "time" is HH:MM;
    - "people" is the people's name related;
    - "serial_number" is the relevant number, which can be an order number, track number, etc;
    - "status" is the status of this event, you can ONLY fill "finished" or "unfinished";
    - "additional_info" includes any other relevant details, such as seat number, flight number, etc.
    - Do not nest structures without authorization;

    If any information is not available or cannot be determined, use null for that field.

    Summary to analyze:
    """

    try:
        print(">>>Generating structured data from summary...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured json data from text."},
                {"role": "user", "content": prompt + result_sum}
            ],
            temperature=0.3,
            max_tokens=1024
        )

        raw_response = response.choices[0].message.content.strip()
        print(">>>Raw output from GPT:")
        print(raw_response)

        # 使用正则表达式提取 JSON 部分
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            json_str = json_match.group()
            print(">>>Extracted JSON string:")
            print(json_str)
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

if __name__ == "__main__":
    img_url = "./demo_src/airticketgloo.jpg"
    print(">>>Starting process...")
    result_sum = generate_img(img_url)
    print(">>>Generating structured data...")
    result_data = generate_data(result_sum)
    print(">>>result:")
    print(json.dumps(result_data, indent=2, ensure_ascii=False))