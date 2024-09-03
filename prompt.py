generate_img_prompt = '''
Analyze the main interface of the image and extract key information, including but not limited to:
1. Event type (e.g., ticket, receipt, content)
2. Related individuals
3. Identification numbers (e.g., serial number, order number)
4. Status (if applicable)
5. Financial details (total amount and currency)
6. Temporal information (date and time)
7. Spatial information (location, destination, address)
8. Any other crucial details

Provide a concise summary highlighting the relevant information for each category. Focus on accuracy and brevity in your description.
'''

generate_data_prompt="""
Extract and structure the information from the provided summary into a JSON format matching our database schema. Fill in all applicable fields directly and concisely. Use null for unavailable or inapplicable information.

Output the following JSON structure without any additional text:

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
    "NER": string,
    "additional_info": string or null
}

Guidelines:
- "type": Use "ticket" (including flight, train tickets), "receipt", or "content" (for posts, articles, books)
- "item": Provide a single, concise word or short phrase that best describes the content (e.g., "report", "invoice", "article", "book"). Avoid long descriptions.
- "location": Provide the event's starting location and detailed address
- "location_start" and "location_end": Use for trip start and end locations
- "currency_type": Use three-letter codes (e.g., CNY, USD, JPY)
- "date": Format as YYYY-MM-DD
- "time": Format as HH:MM
- "people": List related individuals' names
- "serial_number": Include order numbers, tracking numbers, etc.
- "status": Use ONLY "finished" or "unfinished"
- "additional_info": Include other relevant details (e.g., seat number, flight number, or a brief description of the content)
- "NER": List related named entities

Do not nest structures without authorization. Use null for any unavailable information.

Summary to analyze:
"""

generate_json_from_image_prompt = '''
Extract key information that may be contained in the main interface of the image, maybe including but not limited to: time, location, people, summary, order, ticket, or purchase, etc. 
Provide a summary, focusing on: type of the event, person related, serial number, finished (true/false), total amount and currency, date and time, location (destination for travel, delivery address for shopping, etc.), and any other crucial information. 
Summarize these details concisely, output json.
'''