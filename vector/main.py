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


# --- 1. ตั้งค่าการเชื่อมต่อกับ Weaviate ---
# ระบุ URL ของ Weaviate server ที่คุณติดตั้งไว้ (จากข้อมูลที่ให้มา)
WEAVIATE_URL = "http://34.63.29.212:8080"
# สร้าง client เพื่อใช้สื่อสารกับ Weaviate
client = weaviate.Client(url=WEAVIATE_URL)

# --- 2. กำหนดและสร้าง Schema ใน Weaviate ---

# กำหนดชื่อ Class (เปรียบเสมือนชื่อ Table ใน SQL) ที่จะใช้เก็บข้อมูล
CLASS_NAME = "UploadManual"
# print(f" ลบ Class '{CLASS_NAME} แล้ว'")
# client.schema.delete_class(CLASS_NAME)



#-----START TEST WEAVIATE -----# 

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
    target_class: Optional[str] = None,  # ถ้าไม่ส่งมา จะใช้ CLASS_NAME
    page_size: int = 500,                # ปรับได้ตามปริมาณข้อมูล
    max_pages: int = 200,                # กันลูปยาวเกินไปในเคสข้อมูลมหาศาล
    q: Optional[str] = None              # (ทางเลือก) ถ้าส่ง q มา จะกรองฝั่งเซิร์ฟเวอร์อีกชั้น
):
    cls = target_class or CLASS_NAME
    uniq = set()
    offset = 0

    while True:
        res = (
            client.query
                  .get(cls, ["chapter"])   # ดึงเฉพาะ field ที่ต้องใช้ เพื่อให้เร็ว
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

        # จบเมื่อหน้าเล็กกว่าขนาด หรือครบ max_pages
        if len(rows) < page_size or (offset // page_size) + 1 >= max_pages:
            break
        offset += page_size

    chapters = sorted(uniq, key=lambda x: x.lower())

    # กรองเพิ่มด้วยพารามิเตอร์ q (เช่น typeahead)
    if q:
        ql = q.lower()
        chapters = [c for c in chapters if ql in c.lower()]

    return {
        "class": cls,
        "count": len(chapters),
        "chapters": chapters
    }

# ========= Helper: สร้างสคีมาสำหรับคลาสอัปโหลด (ใช้ nearText) =========
def make_upload_schema(class_name: str):
    return {
        "class": class_name,
        "vectorizer": "text2vec-transformers",  # เปลี่ยนจาก text2vec-huggingface
        "moduleConfig": {
            "text2vec-transformers": {           # เปลี่ยน key เป็น text2vec-transformers
                "model": "sentence-transformers/sentence-transformers-all-MiniLM-L6-v2",
                "skip": False,
                "useCache": True,
                "useGPU": False
            }
        },
        "properties": [
            {"name": "content", "dataType": ["text"]},
            {"name": "chapter", "dataType": ["text"]},
            {"name": "section", "dataType": ["text"]},
            {"name": "sub_section", "dataType": ["text"]},
            {"name": "sub_sub_section", "dataType": ["text"]},
            {"name": "img", "dataType": ["text"]},
            {"name": "img2", "dataType": ["text"]},
            {"name": "seq", "dataType": ["text"]}
        ]
    }

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

    # 3) Batch index (ปล่อยให้ Weaviate vectorize เอง — ไม่ส่ง vector=)
    client.batch.configure(batch_size=100, dynamic=True, timeout_retries=3)
    print(f"[upload-json] start batch indexing, total items={len(all_items)}")

    inserted = 0
    skipped = 0

    with client.batch as batch:
        for item in all_items:
            metadata = item.get("metadata", {}) or {}

            # กัน content ว่าง (ถ้าว่าง เรคคอร์ดนี้จะไม่มีเวกเตอร์ → ข้าม)
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


# สร้าง Pydantic model เพื่อกำหนดรูปแบบของ request body ที่จะรับเข้ามา
class QueryInput(BaseModel):
    query: str
    machine: str
    chapters: str
    
class Matches(BaseModel):
    query: str
    top_matches: list[Any]

def search(input: QueryInput):
    # Top N
    k = 10

    # Change from input.query to input['query']
    if not input['query'] or not input['query'].strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    if not client.schema.exists(CLASS_NAME):
        raise HTTPException(status_code=404, detail=f"Class '{CLASS_NAME}' not found. Upload data first.")

    # semantic search
    # ส่งข้อความคำค้น (query)
    nearText = {
        # Change from input.query to input['query']
        "concepts": [input['query']]
    }

    # สร้างคำสั่ง Query ไปยัง Weaviate
    result = (
        client.query
        .get(CLASS_NAME, ["content", "chapter", "section", "sub_section", "sub_sub_section", "img", "img2", "seq"])
        .with_hybrid(query=input['query'], alpha=0.7)  # รวม semantic + BM25
        .with_limit(k)
    )

    result = result.do()
    print("Weaviate response keys:", list(result.keys()))

    if 'errors' in result:
        print("Weaviate errors:", json.dumps(result['errors'], ensure_ascii=False, indent=2))
        msgs = [str(er.get('message') or er) for er in result.get('errors', [])]
        raise HTTPException(status_code=400, detail="; ".join(msgs))

    # ผลลัพธ์ที่ได้จะอยู่ในรูปแบบ JSON, เราต้องดึงส่วนที่ต้องการออกมา
    top_matches = result['data']['Get'][CLASS_NAME]

    # ส่งคืนผลลัพธ์ในรูปแบบ JSON
    # This line already uses the get() method, which works for dictionaries
    return Matches(query=input.get("query"), top_matches=top_matches)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)