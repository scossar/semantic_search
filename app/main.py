from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import chromadb
import asyncio
from pydantic import BaseModel
import os

app = FastAPI()

collection_name = "zalgorithm"

chroma_host = os.getenv("CHROMA_HOST", "localhost")
chroma_port = os.getenv("CHROMA_PORT", "8000")
chroma_client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
collection = chroma_client.get_collection(name=collection_name)

collection.add(
    ids=["id1", "id2"],
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges",
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1313", "https://zalgorithm.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchQuery(BaseModel):
    query: str
    n_results: int = 5


@app.get("/")
def read_root():
    print("in the get method")
    try:
        collections = chroma_client.list_collections()
        return {"collections": [col.name for col in collections]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
