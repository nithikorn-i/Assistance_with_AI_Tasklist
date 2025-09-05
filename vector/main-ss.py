# main.py

# นำเข้า library ที่จำเป็นสำหรับการสร้าง API และการเชื่อมต่อ
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from normalization.spellCheck import spell_Check
import weaviate
import json

# สร้าง instance ของ FastAPI
app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')


# --- 1. ตั้งค่าการเชื่อมต่อกับ Weaviate ---
# ระบุ URL ของ Weaviate server ที่คุณติดตั้งไว้ (จากข้อมูลที่ให้มา)
WEAVIATE_URL = "http://34.63.29.212:8080"
# สร้าง client เพื่อใช้สื่อสารกับ Weaviate
client = weaviate.Client(url=WEAVIATE_URL)

# --- 2. กำหนดและสร้าง Schema ใน Weaviate ---

# กำหนดชื่อ Class (เปรียบเสมือนชื่อ Table ใน SQL) ที่จะใช้เก็บข้อมูล
CLASS_NAME = "Manual4"

# ตรวจสอบก่อนว่า Class นี้มีอยู่แล้วใน Weaviate หรือยัง
# client.schema.delete_class(CLASS_NAME) ลบ Class ออกก่อนเพื่อทดสอบใหม่ --- IGNORE ---
if not client.schema.exists(CLASS_NAME):
    # หากยังไม่มี, ให้กำหนดโครงสร้างของ Class (Schema)
    class_obj = {
        "class": CLASS_NAME,
        # ระบุให้ Weaviate ใช้ตัวสร้าง vector จากข้อความที่ติดตั้งไว้ใน Docker
        "vectorizer": "text2vec-transformers",
        # ตั้งค่าเพิ่มเติมสำหรับโมดูล vectorizer
        "moduleConfig": {
            "text2vec-transformers": {
                "poolingStrategy": "masked_mean",
                "vectorizeClassName": False
            }
        },
        # กำหนด Properties (เปรียบเสมือน Columns) ของข้อมูลที่จะเก็บ
        "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Main instruction content"
        },
        {
            "name": "chapter",
            "dataType": ["text"],
            "description": "Chapter number and title"
        },
        {
            "name": "section",
            "dataType": ["text"],
            "description": "Section title"
        },
        {
            "name": "sub_section",
            "dataType": ["text"],
            "description": "Sub-section title"
        },
        {
            "name": "sub_sub_section",
            "dataType": ["text"],
            "description": "Sub-sub-section title"
        },
        {
            "name": "img",
            "dataType": ["text"],
            "description": "Image path 1"
        },
        {
            "name": "img2",
            "dataType": ["text"],
            "description": "Image path 2"
        },
        {
            "name": "seq",
            "dataType": ["text"],
            "description": "Sequence number"
        },
        {   "name": "vector",
            "dataType": ["number[]"],
            "description": "Vector representation of the content"
        }
    ]
    }
    # สั่งให้ client สร้าง Class ตาม Schema ที่กำหนดไว้
    client.schema.create_class(class_obj)
    print(f"Class '{CLASS_NAME}' ถูกสร้างขึ้นใน Weaviate แล้ว")

    # --- 3. นำเข้าข้อมูล (Data Indexing) ---
    # ส่วนนี้จะทำงานก็ต่อเมื่อ Class ถูกสร้างขึ้นใหม่เท่านั้น
    print("กำลังนำเข้าข้อมูล... Weaviate จะทำการสร้าง Vector ให้อัตโนมัติ")
    # เปิดไฟล์ data.json เพื่ออ่านข้อมูล
    with open("metadata_chunck.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    # ใช้ batch process เพื่อเพิ่มข้อมูลจำนวนมากได้อย่างมีประสิทธิภาพ
    with client.batch as batch:
     for item in data:

        metadata = item["metadata"]

        # รวมข้อความเพื่อสร้าง vector
        obj_text = f"""{item['content']}
        Chapter: {metadata.get('chapter')}
        Section: {metadata.get('section')}
        Sub-section: {metadata.get('sub_section')}
        Sub-sub-section: {metadata.get('sub_sub_section')}"""

        vector = model.encode(obj_text).tolist()
        
        properties = {
            "content": item.get("content"),
            "chapter": item["metadata"].get("chapter"),
            "section": item["metadata"].get("section"),
            "sub_section": item["metadata"].get("sub_section"),
            "sub_sub_section": item["metadata"].get("sub_sub_section"),
            "img": item["metadata"].get("img"),
            "img2": item["metadata"].get("img2"),
            "seq": str(item["metadata"].get("seq")) if item["metadata"].get("seq") else None,
            "vector": vector
        }
        batch.add_data_object(
            data_object=properties,
            class_name="Manual4",
            vector=vector
        )
    print("ข้อมูลถูกนำเข้าไปยัง Weaviate เรียบร้อยแล้ว")
else:
    # หาก Class มีอยู่แล้ว ก็จะข้ามขั้นตอนการสร้างและนำเข้าข้อมูลไป
    print(f"Class '{CLASS_NAME}' มีอยู่แล้ว ข้ามขั้นตอนการสร้าง Schema และ Indexing")


# --- 4. สร้าง API Endpoint ---

# สร้าง Pydantic model เพื่อกำหนดรูปแบบของ request body ที่จะรับเข้ามา
class QueryInput(BaseModel):
    query: str
    filter: str

# สร้าง endpoint ชื่อ /search สำหรับรับคำค้นหาด้วย HTTP POST method
@app.post("/search")
def search(input: QueryInput):
    # กำหนดจำนวนผลลัพธ์สูงสุดที่ต้องการ
    k = 3
    
    # Normalization query
    normaText = {
        'query': input.query if input.query == '' else spell_Check(input.query),
    }

    # ใช้ 'nearText' เพื่อทำการค้นหาเชิงความหมาย (semantic search)
    # โดยส่งข้อความคำค้น (query) เข้าไปตรงๆ
    nearText = {
        "concepts": [normaText]
    }

    # สร้างคำสั่ง Query ไปยัง Weaviate
    result = (
        client.query
        .get(CLASS_NAME, ["content", "chapter", "section", "sub_section", "sub_sub_section", "img", "img2", "seq"]) # 1. ดึงข้อมูลจาก Class 'Machine' และขอ properties ที่ระบุ
        .with_near_text(nearText)                 
        .with_limit(k)                             
        .with_additional(['certainty', 'distance']) 
        .do()                                      
    )

    # ผลลัพธ์ที่ได้จะอยู่ในรูปแบบ JSON, เราต้องดึงส่วนที่ต้องการออกมา
    top_matches = result['data']['Get'][CLASS_NAME]

    # ส่งคืนผลลัพธ์ในรูปแบบ JSON
    return {
        "query": input.query,
        "top_matches": top_matches
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)