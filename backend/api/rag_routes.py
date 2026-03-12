from fastapi import APIRouter, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import List
import shutil
import os
import pdfplumber

from backend.services.rag_service import RAGService
from backend.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["RAG - Assistente Pesquisador"])

# Lazy initialization para evitar erros durante import quando API keys não estão configuradas
_rag_service = None
_research_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

def get_research_service() -> ResearchService:
    global _research_service
    if _research_service is None:
        _research_service = ResearchService(get_rag_service())
    return _research_service

class QueryRequest(BaseModel):
    query: str  # Changed from 'question' to 'query' to match Flutter

class QueryResponse(BaseModel):
    response: str  # Changed from 'answer' to 'response' to match Flutter
    sources: List[dict]

@router.post("/chat", response_model=QueryResponse)
def chat_with_researcher(request: QueryRequest):
    """
    Interface de chat para o pesquisador (usada pelo app mobile).
    """
    rag_service = get_rag_service()
    result = rag_service.ask(request.query)
    return {
        "response": result["answer"],
        "sources": result["sources"]
    }

@router.post("/query", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """
    Legacy/Web endpoint.
    """
    rag_service = get_rag_service()
    result = rag_service.ask(request.query)
    return {
        "response": result["answer"],
        "sources": result["sources"]
    }

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    year: int = Form(2025)
):
    """
    Faz o upload de um artigo científico em PDF, extrai o texto e salva no Vector Store.
    """
    if not file.filename.endswith(".pdf"):
        return {"error": "Apenas arquivos PDF são aceitos no momento."}
    rag_service = get_rag_service()
    # Salvar temporariamente
    os.makedirs("./temp", exist_ok=True)
    temp_path = f"./temp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        # Extrair texto do PDF
        full_text = ""
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        # Ingerir no RAG
        metadata = {"source": file.filename, "title": title, "year": year}
        res = rag_service.ingest_document(full_text, metadata)
        return {"message": "Documento ingerido com sucesso!", "chunks": res["chunks_added"]}
    finally:
        os.remove(temp_path)

@router.post("/autonomous-research")
async def trigger_autonomous_research(topic: str = "Type 1 Diabetes breakthrough"):
    """
    Aciona o agente pesquisador para buscar artigos científicos na web e PubMed.
    """
    research_service = get_research_service()
    result = await research_service.run_autonomous_research(topic)
    return result

@router.delete("/clear-knowledge")
async def clear_knowledge():
    """
    Limpa a base de conhecimento (Vector Store) para recomeçar.
    """
    rag_service = get_rag_service()
    if rag_service.client.collection_exists(rag_service.collection_name):
        rag_service.client.delete_collection(rag_service.collection_name)
        rag_service.client.create_collection(
            collection_name=rag_service.collection_name,
            vectors_config={"size": 3072, "distance": "Cosine"},
        )
    return {"message": "Base de conhecimento resetada com sucesso."}
