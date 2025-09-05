from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import weaviate
import uuid
from datetime import UTC, datetime
import os
import json
from typing import Any, Dict, List, Optional
from collections import defaultdict

from service_ai import ResponseIntentJson, ResponseJson, makeFinalPrompt, makeIntentPrompt
from vector.main import Matches, QueryInput, make_upload_schema, search
from normalization.spellCheck import spell_Check

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')

# เชื่อม static folder
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ตั้งค่า Jinja2 template folder
templates_dir = os.path.join(BASE_DIR, "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

# Weaviate Configuration
WEAVIATE_URL = "http://34.63.29.212:8080"  # เปลี่ยนตาม URL ของคุณ
CLASS_NAME = "ChatHistory"
CLASS_UPLOAD = "UploadManual"

# Initialize Weaviate Client
try:
    client = weaviate.Client(url=WEAVIATE_URL)
    if not client.is_ready():
        raise ConnectionError("Could not connect to Weaviate")
    print("✅ Connected to Weaviate successfully")
except Exception as e:
    print(f"❌ Failed to connect to Weaviate: {str(e)}")
    raise

# กำหนดโครงสร้างข้อมูลใหม่
def initialize_weaviate_schema():
    # เช็คว่ามี class อยู่หรือไม่ ถ้ามีแล้วก็ไม่ลบ
    if not client.schema.exists(CLASS_NAME):
        # ถ้าไม่มี class ให้สร้างใหม่
        class_obj = {
            "class": CLASS_NAME,
            "vectorizer": "none",
            "properties": [
                {"name": "chatId", "dataType": ["string"]},
                {"name": "sender", "dataType": ["string"]},
                {"name": "text", "dataType": ["text"]},
                {"name": "timestamp", "dataType": ["string"]}
            ]
        }
        client.schema.create_class(class_obj)
        print(f"✅ Created new class: {CLASS_NAME}")
    else:
        print(f"ℹ️ Class {CLASS_NAME} already exists")
initialize_weaviate_schema()


def get_chat_history(chat_id: str) -> List[Dict]:
    """
    ดึงประวัติ chat จาก Weaviate ตาม chat_id
    """
    result = client.query.get(
        CLASS_NAME,
        ["sender", "text", "timestamp"]
    ).with_where({
        "path": ["chatId"],
        "operator": "Equal",
        "valueString": chat_id
    }).with_sort({
        "path": ["timestamp"],
        "order": "asc"
    }).do()

    messages = []
    objects = result.get('data', {}).get('Get', {}).get(CLASS_NAME, [])
    for obj in objects:
        messages.append({
            "sender": obj.get('sender', ''),
            "text": obj.get('text', ''),
            "timestamp": obj.get('timestamp', '')
        })

    return messages

def build_toc(data):
    chapters = defaultdict(set)
    for item in data:
        chapter = item["metadata"]["chapter"]
        section = item["metadata"]["section"]
        chapters[chapter].add(section)

    toc = []
    for chapter, sections in chapters.items():
        toc.append({
            "chapter": chapter,
            "sections": sorted(list(sections))
        })
    return toc

# Models
class ChatInput(BaseModel):
    chatId: str
    message: str
    sender: str

# Routes
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat")
async def chat(input: ChatInput):
    try:
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        # vector = model.encode(input.message).tolist()
        
        # dataIntent: ResponseIntentJson = makeIntentPrompt(input.message)
        
        # print("related_chapters : ", dataIntent.related_chapters)
        
        # dataQuery: QueryInput = {
        #     # Normalization query
        #     "query": dataIntent.corrected_query,
        #     "machine": 'YRM',
        #     "chapters": dataIntent.related_chapters
        # }
        
        dataQuery: QueryInput = {
            # Normalization query
            "query": input.message if input.message == '' else spell_Check(input.message),
            "machine": 'YRM'

        }

        data_matche: Matches = search(dataQuery)
        
        print("============================<top_matches>==============================")
        
        print("data_matche : ", data_matche.top_matches)
        
        print("============================<top_matches>==============================")
        
        user_msg = {
            "chatId": input.chatId,
            "sender": input.sender,
            "text": input.message,
            "timestamp": timestamp
        }
        
        client.data_object.create(
            data_object=user_msg,
            class_name=CLASS_NAME
        )
        
        user_persona = ""
        
        chat_history = get_chat_history(input.chatId)
        
        print("chat_history : ", chat_history)
        
        responseData: List[ResponseJson] =  makeFinalPrompt(user_persona, chat_history, dataQuery["query"], data_matche.top_matches)
        
        ai_msg = {
            "chatId": input.chatId,
            "sender": "ai",
            "text": responseData[0].answer, 
            "timestamp": timestamp
        }

        client.data_object.create(
            data_object=ai_msg,
            class_name=CLASS_NAME
        )
        
        print("ai_msg : ", ai_msg)
        

        return {"response": responseData[0].answer} 

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/new-chat")
async def new_chat():
    try:
        chat_id = str(uuid.uuid4())
        return {"chatId": chat_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-history/{chat_id}")
async def get_history(chat_id: str):
    try:
        messages = get_chat_history(chat_id)
        return {"messages": messages}
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-all-chats")
async def get_all_chats():
    try:
        # ดึงข้อมูลทั้งหมดแล้วจัดกลุ่ม
        all_objects = client.data_object.get(class_name=CLASS_NAME, limit=1000)
        
        chats = {}
        for obj in all_objects.get('objects', []):
            props = obj.get('properties', {})
            chat_id = props.get('chatId')
            timestamp = props.get('timestamp')
            
            if chat_id and timestamp:
                if chat_id not in chats or timestamp > chats[chat_id]:
                    chats[chat_id] = timestamp
        
        # แปลงเป็นรูปแบบที่ต้องการและเรียงลำดับ
        result = [{"chatId": k, "lastActivity": v} for k, v in chats.items()]
        result.sort(key=lambda x: x["lastActivity"], reverse=True)
        
        return {"chats": result}
        
    except Exception as e:
        print(f"Error in get_all_chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/delete-chat/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        # ดึงข้อมูลทั้งหมดจาก chatId 
        result = client.query.get(
            CLASS_NAME,
            ["_additional { id }"]
        ).with_where({
            "path": ["chatId"],
            "operator": "Equal",
            "valueString": chat_id
        }).do()

        objs = result.get("data", {}).get("Get", {}).get(CLASS_NAME, [])
        for obj in objs:
            obj_id = obj["_additional"]["id"]
            client.data_object.delete(obj_id)
        
        return {"message": "Deleted chat " + chat_id}
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return Response(content=str(e), status_code=500)

# ========= Helper: ให้แน่ใจว่า schema ถูกต้อง (จำเป็นสำหรับ nearText) =========
def ensure_schema(class_name: str, force_recreate: bool = False):
    """
    - ถ้าไม่มีคลาส → สร้างใหม่ด้วย text2vec-transformers
    - ถ้ามีแต่ vectorizer ไม่ใช่ text2vec-transformers → ลบทิ้งแล้วสร้างใหม่
    - ถ้า force_recreate=True → ลบทิ้งแล้วสร้างใหม่เสมอ
    """
    info = client.schema.get()
    classes = (info.get("classes") or [])
    current = next((c for c in classes if c.get("class") == class_name), None)

    needs_recreate = (
        force_recreate or
        current is None or
        current.get("vectorizer") != "text2vec-transformers"
    )

    if needs_recreate:
        if current is not None:
            try:
                client.schema.delete_class(class_name)
                print(f"[schema] deleted old class '{class_name}' (vectorizer={current.get('vectorizer')})")
            except Exception as e:
                print(f"[schema] delete {class_name} failed: {e}")
        client.schema.create_class(make_upload_schema(class_name))
        print(f"[schema] created class '{class_name}' with text2vec-transformers")
    else:
        print(f"[schema] '{class_name}' OK (vectorizer=text2vec-transformers)")

# ========= Endpoint: Upload JSON หลายไฟล์ + Batch Index เข้า Weaviate =========

# Upload file metadata
@app.post("/upload-json")
async def upload_json(
    files: List[UploadFile] = File(..., description="อัปโหลดไฟล์ .json ได้หลายไฟล์"),
    recreate: bool = False,
):
    # 1) สร้าง/ซ่อม schema ให้พร้อมสำหรับ nearText
    ensure_schema(CLASS_UPLOAD, force_recreate=recreate)

    # 2) รวม items จากทุกไฟล์
    all_items = []
    for f in files:
        if f.content_type not in ("application/json", "text/json", "application/octet-stream"):
            raise HTTPException(status_code=400, detail=f"'{f.filename}' ไม่ใช่ไฟล์ JSON")
        raw = await f.read()
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"อ่าน JSON จาก '{f.filename}' ไม่ได้: {e}")

        if isinstance(obj, list):
            items = obj
        elif isinstance(obj, dict) and isinstance(obj.get("data"), list):
            items = obj["data"]
        elif isinstance(obj, dict):
            items = [obj]
        else:
            raise HTTPException(status_code=400, detail=f"โครงสร้าง JSON ของ '{f.filename}' ไม่ถูกต้อง")

        all_items.extend(items)

    if not all_items:
        raise HTTPException(status_code=400, detail="ไม่พบรายการข้อมูลใด ๆ ในไฟล์ที่อัปโหลด")

    # 3) Batch index (ปล่อยให้ Weaviate vectorize เอง — ไม่ส่ง vector=)
    client.batch.configure(batch_size=100, dynamic=True, timeout_retries=3)
    print(f"[upload-json] start batch indexing, total items={len(all_items)}")

    inserted = 0
    skipped = 0

    with client.batch as batch:
        for i, item in enumerate(all_items, 1):
            metadata = item.get("metadata", {}) or {}
            content_val = (item.get("content") or "").strip()
            if not content_val:
                skipped += 1
                continue

            properties = {
                "content": content_val,
                "chapter": metadata.get("chapter"),
                "section": metadata.get("section"),
                "sub_section": metadata.get("sub_section"),
                "sub_sub_section": metadata.get("sub_sub_section"),
                "img": metadata.get("img"),
                "img2": metadata.get("img2"),
                "seq": str(metadata.get("seq")) if metadata.get("seq") is not None else None,
            }

            batch.add_data_object(
                data_object=properties,
                class_name=CLASS_UPLOAD,
            )
            inserted += 1

            # แสดง progress ทุก 50 รายการ
            if i % 50 == 0 or i == len(all_items):
                print(f"[upload-json] processed {i}/{len(all_items)} items, inserted={inserted}, skipped={skipped}")

    return {
        "files_received": len(files),
        "items_indexed": inserted,
        "items_skipped": skipped,
        "class_name": CLASS_UPLOAD
    }
    
@app.post("/toc")
async def get_toc(file: UploadFile = File(...)):
    # อ่านไฟล์ JSON จาก input
    contents = await file.read()
    data = json.loads(contents.decode("utf-8"))
    # สร้างสารบัญ
    toc = build_toc(data)
    return toc

@app.post("/test_intent")
async def get_intent(query: str):
    return makeIntentPrompt(query)
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)
