from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from pydantic import BaseModel

app = FastAPI()

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
    return {"status": "Semantic search API is running"}
