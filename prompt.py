generate_img_prompt='''
    Extract key information that may be contained in the main interface of the image, maybe including but not limited to: Critical time, location, people, summary, order, ticket, or purchase, etc. 
    Provide a summary, focusing on: type of the event, person related, serial number, status (if finished), total amount and currency, date and time,location (destination for travel, delivery address for shopping, etc.),and any other crucial information. 
    Summarize these details concisely, highlighting the relevant information for each category.
    '''

generate_data_prompt="""
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
        "NER": string,
        "additional_info": string or null
    }

    Ensure that:
    - "type" is content type. Possible values: ticket(include: flight ticket, train ticket, etc), receipt, content(include: post, web article, book, etc); 
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
    - "NER" is the related entities;
    - Do not nest structures without authorization;

    If any information is not available or cannot be determined, use null for that field.

    Summary to analyze:
    """

generate_json_from_image_prompt = '''
    Extract key information that may be contained in the main interface of the image, maybe including but not limited to: time, location, people, summary, order, ticket, or purchase, etc. 
    Provide a summary, focusing on: type of the event, person related, serial number, finished (true/false), total amount and currency, date and time,location (destination for travel, delivery address for shopping, etc.),and any other crucial information. 
    Summarize these details concisely, out put json.
    '''