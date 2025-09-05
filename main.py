# main.py

# นำเข้า library ที่จำเป็นสำหรับการสร้าง API และการเชื่อมต่อ
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Any, Optional, List
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import weaviate
import json

# สร้าง instance ของ FastAPI
app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')


# --- 1. Weaviate Connection ---
WEAVIATE_URL = "http://34.63.29.212:8080"
client = weaviate.Client(url=WEAVIATE_URL)

# --- 2.Config Weaviate Schema ---

# Config Class (เปรียบเสมือนชื่อ Table ใน SQL)
CLASS_NAME = "UploadManual2"
# client.schema.delete_class(CLASS_NAME)
print(f"คลาส {CLASS_NAME}'")



#-----START TEST WEAVIATE -----# --ignore

# # ตรวจสอบก่อนว่า Class นี้มีอยู่แล้วใน Weaviate หรือยัง
# client.schema.delete_class("Manual4")
# if not client.schema.exists(CLASS_NAME):
#     # หากยังไม่มี, ให้กำหนดโครงสร้างของ Class (Schema)
#     class_obj = {
#         "class": CLASS_NAME,
#         # ระบุให้ Weaviate ใช้ตัวสร้าง vector จากข้อความที่ติดตั้งไว้ใน Docker
#         "vectorizer": "text2vec-transformers",
#         # ตั้งค่าเพิ่มเติมสำหรับโมดูล vectorizer
#         "moduleConfig": {
#             "text2vec-transformers": {
#                 "poolingStrategy": "masked_mean",
#                 "vectorizeClassName": False
#             }
#         },
#         # กำหนด Properties (เปรียบเสมือน Columns) ของข้อมูลที่จะเก็บ
#         "properties": [
#         {
#             "name": "content",
#             "dataType": ["text"],
#             "description": "Main instruction content"
            
#         },
#         {
#             "name": "chapter",
#             "dataType": ["text"],
#             "description": "Chapter number and title",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "section",
#             "dataType": ["text"],
#             "description": "Section title",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "sub_section",
#             "dataType": ["text"],
#             "description": "Sub-section title",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "sub_sub_section",
#             "dataType": ["text"],
#             "description": "Sub-sub-section title",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "img",
#             "dataType": ["text"],
#             "description": "Image path 1",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "img2",
#             "dataType": ["text"],
#             "description": "Image path 2",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         },
#         {
#             "name": "seq",
#             "dataType": ["text"],
#             "description": "Sequence number",
#             "moduleConfig": { "text2vec-transformers": { "skip": True } }
#         }
#     ]
#     }
#     # สั่งให้ client สร้าง Class ตาม Schema ที่กำหนดไว้
#     client.schema.create_class(class_obj)
#     print(f"Class '{CLASS_NAME}' ถูกสร้างขึ้นใน Weaviate แล้ว")

#     # --- 3. นำเข้าข้อมูล (Data Indexing) ---
#     # ส่วนนี้จะทำงานก็ต่อเมื่อ Class ถูกสร้างขึ้นใหม่เท่านั้น
#     print("กำลังนำเข้าข้อมูล... Weaviate จะทำการสร้าง Vector ให้อัตโนมัติ")
#     # เปิดไฟล์ data.json เพื่ออ่านข้อมูล
#     with open("metadata_chunck.json", 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     # ใช้ batch process เพื่อเพิ่มข้อมูลจำนวนมากได้อย่างมีประสิทธิภาพ

#     client.batch.configure(batch_size=100, dynamic=True, timeout_retries=3)

#     with client.batch as batch:
#      for item in data:

#         metadata = item["metadata"]

#         # รวมข้อความเพื่อสร้าง vector
#         obj_text = f"""{item['content']}
#         Chapter: {metadata.get('chapter')}
#         Section: {metadata.get('section')}
#         Sub-section: {metadata.get('sub_section')}
#         Sub-sub-section: {metadata.get('sub_sub_section')}"""

#         vector = model.encode(obj_text).tolist()
        
#         properties = {
#             "content": item.get("content"),
#             "chapter": item["metadata"].get("chapter"),
#             "section": item["metadata"].get("section"),
#             "sub_section": item["metadata"].get("sub_section"),
#             "sub_sub_section": item["metadata"].get("sub_sub_section"),
#             "img": item["metadata"].get("img"),
#             "img2": item["metadata"].get("img2"),
#             "seq": str(item["metadata"].get("seq")) if item["metadata"].get("seq") else None,
#         }
#         batch.add_data_object(
#             data_object=properties,
#             class_name=CLASS_NAME,
#             vector=vector
#         )
#     print("ข้อมูลถูกนำเข้าไปยัง Weaviate เรียบร้อยแล้ว")
# else:
#     # หาก Class มีอยู่แล้ว ก็จะข้ามขั้นตอนการสร้างและนำเข้าข้อมูลไป
#     print(f"Class '{CLASS_NAME}' มีอยู่แล้ว ข้ามขั้นตอนการสร้าง Schema และ Indexing")



#-----END TEST WEAVIATE -----# 

# --- สร้าง API Endpoint ---

#List Filter
@app.get("/chapters")
def list_chapters(
    target_class: Optional[str] = None,
    page_size: int = 500,
    max_pages: int = 200,
    q: Optional[str] = None
):
    cls = target_class or CLASS_NAME
    uniq = set()
    offset = 0

    while True:
        res = (
            client.query
                  .get(cls, ["chapter"])
                  .with_limit(page_size)
                  .with_offset(offset)
                  .do()
        )
        rows = res.get("data", {}).get("Get", {}).get(cls, []) or []

        for r in rows:
            chap = r.get("chapter")
            if chap is not None:
                s = str(chap).strip()
                if s:
                    uniq.add(s)

        if len(rows) < page_size or (offset // page_size) + 1 >= max_pages:
            break
        offset += page_size

    chapters = sorted(uniq, key=lambda x: x.lower())

    if q:
        ql = q.lower()
        chapters = [c for c in chapters if ql in c.lower()]

    return {
        "class": cls,
        "count": len(chapters),
        "chapters": chapters
    }

@app.get("/section")
def list_section(
    target_class: Optional[str] = None,
    page_size: int = 500,
    max_pages: int = 200,
    q: Optional[str] = None
):
    cls = target_class or CLASS_NAME
    uniq = set()
    offset = 0

    while True:
        res = (
            client.query
                  .get(cls, ["section"])
                  .with_limit(page_size)
                  .with_offset(offset)
                  .do()
        )
        rows = res.get("data", {}).get("Get", {}).get(cls, []) or []

        for r in rows:
            sections = r.get("section")
            if sections is not None:
                s = str(sections).strip()
                if s:
                    uniq.add(s)

        if len(rows) < page_size or (offset // page_size) + 1 >= max_pages:
            break
        offset += page_size

    section = sorted(uniq, key=lambda x: x.lower())

    if q:
        ql = q.lower()
        section = [c for c in section if ql in c.lower()]

    return {
        "class": cls,
        "count": len(section),
        "chapters": section
    }

@app.get("/machine")
def list_section(
    target_class: Optional[str] = None,
    page_size: int = 500,
    max_pages: int = 200,
    q: Optional[str] = None
):
    cls = target_class or CLASS_NAME
    uniq = set()
    offset = 0

    while True:
        res = (
            client.query
                  .get(cls, ["machine"])
                  .with_limit(page_size)
                  .with_offset(offset)
                  .do()
        )
        rows = res.get("data", {}).get("Get", {}).get(cls, []) or []

        for r in rows:
            machines = r.get("machine")
            if machines is not None:
                s = str(machines).strip()
                if s:
                    uniq.add(s)

        if len(rows) < page_size or (offset // page_size) + 1 >= max_pages:
            break
        offset += page_size

    machine = sorted(uniq, key=lambda x: x.lower())

    if q:
        ql = q.lower()
        machine = [c for c in machine if ql in c.lower()]

    return {
        "class": cls,
        "count": len(machine),
        "chapters": machine
    }
    

# ========= Helper: สร้างสคีมาสำหรับคลาสอัปโหลด =========
def make_upload_schema(class_name: str):
    return {
        "class": class_name,
        "vectorizer": "text2vec-transformers",
        "moduleConfig": {
            "text2vec-transformers": {
                "poolingStrategy": "masked_mean",
                "vectorizeClassName": False
            }
        },
        "properties": [
            {"name": "content", "dataType": ["text"], "description": "Main instruction content"},
            {"name": "chapter", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "section", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "machine", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "sub_section", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "sub_sub_section", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "img", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "img2", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
            {"name": "seq", "dataType": ["text"], "moduleConfig": {"text2vec-transformers": {"skip": True}}},
        ]
    }

# ========= Helper: ให้แน่ใจว่า schema ถูกต้อง =========
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

# ========= Endpoint: Create Schema Helper=========


# Upload file metadata
@app.post("/upload-json")
async def upload_json(
    files: List[UploadFile] = File(..., description="อัปโหลดไฟล์ .json ได้หลายไฟล์"),
    recreate: bool = False,
):
    # 1) สร้าง/ซ่อม schema ให้พร้อมสำหรับ nearText
    ensure_schema(CLASS_NAME, force_recreate=recreate)

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

    # 3) Batch index ปล่อยให้ Weaviate vectorize เอง
    client.batch.configure(batch_size=100, dynamic=True, timeout_retries=3)
    print(f"[upload-json] start batch indexing, total items={len(all_items)}")

    inserted = 0
    skipped = 0

    with client.batch as batch:
        for item in all_items:
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
                "machine":metadata.get("machine"),
                "sub_sub_section": metadata.get("sub_sub_section"),
                "img": metadata.get("img"),
                "img2": metadata.get("img2"),
                "seq": str(metadata.get("seq")) if metadata.get("seq") is not None else None,
            }

            batch.add_data_object(
                data_object=properties,
                class_name=CLASS_NAME,
            )
            inserted += 1

    print(f"[upload-json] done. inserted={inserted}, skipped={skipped}")

    return {
        "files_received": len(files),
        "items_indexed": inserted,
        "items_skipped": skipped,
        "class_name": CLASS_NAME
    }


# request body
class QueryInput(BaseModel):
    query: str
    machine: Optional[str] = None
    
class Matches(BaseModel):
    query: str
    top_matches: list[Any]

# สร้าง endpoint
@app.post("/search")
def search(input: QueryInput):
    # Top N
    k = 10

    if not input.query or not input.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    if not client.schema.exists(CLASS_NAME):
        raise HTTPException(status_code=404, detail=f"Class '{CLASS_NAME}' not found. Upload data first.")

    # semantic search
    # ส่งข้อความคำค้น (query)
    nearText = {
        "concepts": [input.query]
    }

    # สร้างคำสั่ง Query ไปยัง Weaviate
    result = (
        client.query
        .get(CLASS_NAME, ["content", "chapter", "section", "sub_section", "machine", "sub_sub_section", "img", "img2", "seq"])
        .with_near_text(nearText)                 
        .with_limit(k)                             
        .with_additional(['certainty', 'distance']) 
    )

    ch = (input.machine or "").strip()
    if ch:
        result = result.with_where({
            "path": ["machine"],
            "operator": "Equal",
            "valueText": ch
        })

    result = result.do()
    print("Weaviate response keys:", list(result.keys()))
    
    if 'errors' in result:
        print("Weaviate errors:", json.dumps(result['errors'], ensure_ascii=False, indent=2))
        msgs = [str(er.get('message') or er) for er in result.get('errors', [])]
        raise HTTPException(status_code=400, detail="; ".join(msgs))

    # ผลลัพธ์ที่ได้จะอยู่ในรูปแบบ JSON, เราต้องดึงส่วนที่ต้องการออกมา
    top_matches = result['data']['Get'][CLASS_NAME]

    # ส่งคืนผลลัพธ์ในรูปแบบ JSON
    return Matches(query=input["query"], top_matches=top_matches)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)