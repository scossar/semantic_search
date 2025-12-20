from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from pydantic import BaseModel
import os

app = FastAPI()

collection_name = "zalgorithm"

chroma_host = os.getenv("CHROMA_HOST", "localhost")
chroma_port = os.getenv("CHROMA_PORT", "8000")
# chroma_client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
# chroma_client = chromadb.AsyncHttpClient(host=chroma_host, port=int(chroma_port))

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


@app.post("/query", response_model=QueryResponse)
async def query_collection(request: QueryRequest):
    try:
        chroma_client = await chromadb.AsyncHttpClient(
            host=chroma_host, port=int(chroma_port)
        )
        collection = await chroma_client.get_collection(name=collection_name)
        results = await collection.query(
            query_texts=[request.query], n_results=request.n_results
        )

        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i]
                    if results["documents"]
                    else None,
                    "metadata": results["metadatas"][0][i]
                    if results["metadatas"]
                    else None,
                    "distance": results["distances"][0][i]
                    if results["distances"]
                    else None,
                }
            )

        return {"results": formatted_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
