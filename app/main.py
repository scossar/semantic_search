from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from pydantic import BaseModel
import os

app = FastAPI()

collection_name = "zalgorithm"

chroma_host = os.getenv("CHROMA_HOST", "localhost")
chroma_port = os.getenv("CHROMA_PORT", "8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1313", "https://zalgorithm.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    n_results: int = 5


class QueryResponse(BaseModel):
    results: list[dict]


@app.get("/")
async def read_root():
    return {"status": "It works."}


@app.get("/collections")
async def list_collections():
    try:
        chroma_client = await chromadb.AsyncHttpClient(
            host=chroma_host, port=int(chroma_port)
        )
        collections = await chroma_client.list_collections()
        return {"collections": [col.name for col in collections]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_class=HTMLResponse)
async def query_collection(query: Annotated[str, Form()]):
    print("request received")
    print(query)
    try:
        chroma_client = await chromadb.AsyncHttpClient(
            host=chroma_host, port=int(chroma_port)
        )
        collection = await chroma_client.get_collection(name=collection_name)
        results = await collection.query(query_texts=[query], n_results=5)

        # formatted_results = []
        # for i in range(len(results["ids"][0])):
        #     formatted_results.append(
        #         {
        #             "id": results["ids"][0][i],
        #             "document": results["documents"][0][i]
        #             if results["documents"]
        #             else None,
        #             "metadata": results["metadatas"][0][i]
        #             if results["metadatas"]
        #             else None,
        #             "distance": results["distances"][0][i]
        #             if results["distances"]
        #             else None,
        #         }
        #     )

        html = ""
        for i in range(len(results["ids"][0])):
            heading = (
                results["metadatas"][0][i]["html_heading"]
                if results["metadatas"]
                else ""
            )
            fragment = (
                results["metadatas"][0][i]["html_fragment"]
                if results["metadatas"]
                else ""
            )
            html += heading
            html += fragment

        return html

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
