import base64
from PIL import Image
import io
from openai import OpenAI
import json
import re
from ltp import LTP,StnSplit
# from pydantic import BaseModel, ValidationError

from config import openai_api_base, openai_api_key
from prompt import generate_img_prompt,generate_data_prompt,generate_json_from_image_prompt


client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

# class ExtractedData(BaseModel):
#     type: str | None
#     item: str | None
#     location: str | None
#     location_start: str | None
#     location_end: str | None
#     date: str | None
#     time: str | None
#     people: list[str] | None
#     serial_number: str | None
#     status: str | None
#     total_amount: float | None
#     currency_type: str | None
#     additional_info: str | None

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
                {"role": "system", "content": "You are a helpful assistant that extracts structured json data from text."},
                {"role": "user", "content": prompt + result_sum}
            ],
            temperature=0.3,
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


if __name__ == "__main__":
    img_url = input(">>>Drop img here:").strip().strip("'\"")
    print(f"Final image path: {img_url}")
    
    # try:
    #     with Image.open(img_url) as img:
    #         img.show()
    # except Exception as e:
    #     print(f"Error processing image at path: {img_url}")
    #     print(f"Error details: {e}")

    print(">>>Starting process...")
    result_sum = generate_img(img_url)
    result_sum = result_sum + "NER:" + str(NER(result_sum))
    print(">>>Generating structured data...")
    result_data = generate_data(result_sum)
    print(">>>result:")
    print(json.dumps(result_data, indent=2, ensure_ascii=False))