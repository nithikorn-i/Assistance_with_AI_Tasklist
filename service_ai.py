import logging
from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel

# เรียกใช้ API ของ Gemini 
client = genai.Client(api_key="AIzaSyAh-L-PWda3EVPaPRlyPeLLgpT0ZtQHAQE")

# Simulated user context
chat_history = [
    # "User: อะไรคือสัตว์ที่มีขาเยอะที่สุด?",
    # "Bot: ตะขาบ ครับ"
]
user_persona = "The user is a zoology"
# User's new query
user_query = "อะไรคือสัตว์ทีมีขาเยอะที่สุด"


class ResponseJson(BaseModel):
        question: str
        answer: str
        
class ResponseIntentJson(BaseModel):
        corrected_query: str
        related_chapters: List[str]

# function สำหรับทำ final prompt
def makeFinalPrompt(persona, history, user_query, top_n_content):
    formatted_content = ""
    for i, item in enumerate(top_n_content, 1):
        # ดึง content และ metadata ตามประเภทของ item
        content = item.get('content', '')
        machine = item.get('machine', '')
        chapter = item.get('chapter', '')
        section = item.get('section', '')

        formatted_content += f"""
        ---
        Top {i}:
        Content: {content}
        Source: Machine: {machine}, Chapter: {chapter}, Section: {section}
        ---"""

    final_prompt = f"""
    User Persona: {persona}
    Chat History:
        {chr(10).join([h["text"] if isinstance(h, dict) else str(h) for h in history])}

    Current Question:
    {user_query}

    ---
    Top n Content:
    {formatted_content}
    """
    
    print("Prompt : ", final_prompt)
    
    return chatWithAI(final_prompt, "gemini-2.5-flash", False, user_query)

# function สำหรับทำ final prompt
def makeIntentPrompt(user_query: str) -> ResponseIntentJson: 
    # โหลด knowledge base
    with open("knowledge_base.json", "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
    
    # สร้าง prompt
    prompt = f"""
You are an assistant that analyzes a query against a knowledge base.

1. Correct spelling or grammar mistakes in the query.
2. Identify the most relevant chapter(s) from the provided knowledge base.
3. Return the result strictly as a JSON string with this format:
{{
  "corrected_query": "...",
  "related_chapters": ["chapter1", "chapter2", ...]
}}

Knowledge base:
{json.dumps(knowledge_base, indent=2)}

User query:
{user_query}
"""

    # เรียก Gemini API
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    raw_text = response.text

    print("response : ", raw_text)
    
    clean_text = raw_text.strip().lstrip("```json").rstrip("```").strip()

    # แปลง string JSON เป็น dict
    response_dict = json.loads(clean_text)

    # แปลงเป็น BaseModel
    responseIntentJson = ResponseIntentJson(**response_dict)

    return responseIntentJson


# ฟังก์ชันสำหรับ รับคำตอบจาก AI มาแสดงผล
import json

def resposneText(query, response):
    print("Question:")
    print(query)

    print("✅ Answer from Gemini:")

    # ดึงข้อความ JSON string
    text_out = response.text.strip()

    # แปลง JSON string → Python list of dict
    data_list = json.loads(text_out)

    # map เข้า Pydantic model
    parsed_list: List[ResponseJson] = [ResponseJson(**item) for item in data_list]

    # print ตัวอย่างคำตอบ
    for item in parsed_list:
        print(item.answer)

    return parsed_list

# ฟังก์ชันที่ไว้เรียกใช้ AI
def chatWithAI(prompt, model, useGoogleSearch, user_query):
    
    # ไว้สำหรับกับหนดค่าให้ AI แสดงผลลัพธ์ในรูปแบบที่เราต้องการ
    jsonResponseConfig = {
        "response_mime_type": "application/json",
        "response_schema": list[ResponseJson]
    }
    
    # ไว้ใช้กำหนด config ของ AI ไม่จำเป็นต้องมีได้
    config = types.GenerateContentConfig(**jsonResponseConfig)

    # เงื่อนไขเมื่อต้องการให้ AI หาข้อมูลเพิ่มเติมจาก Google
    if useGoogleSearch:
        grounding_tool = types.Tool(
            google_search = types.GoogleSearch()
        )

        config = types.GenerateContentConfig(
            tools = [grounding_tool]
        )
    
    try:
        logging.info(f"Sending prompt to {model.capitalize()}")
        # ให้ AI สร้างคำตอบ จาก prompt ที่เราส่งเข้ามา
        response = client.models.generate_content(
        model = model,
        contents = prompt,
        config = config
        )
        # print(f"Respoon From {model.capitalize()}")
        return resposneText(user_query, response)
    except Exception as e:
        logging.error(f"Gemini generated failed: {e}")
        return f"[ERROR] Gemini generated failed: {e}"

# final_prompt = makeFinalPrompt(user_persona, chat_history, user_query)
# print(final_prompt)

# print(chatWithAI(final_prompt, "gemini-2.5-flash", False)) 

# print(chatWithAI(final_prompt, "gemini-2.5-flash-lite", False))

# print(chatWithAI(final_prompt, "gemini-2.0-flash", False))



