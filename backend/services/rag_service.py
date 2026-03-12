import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.config import settings
import httpx

class RAGService:
    def __init__(self):
        # Configurar custom client para ignorar erro de proxy SSL
        import httpx
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        import requests
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        
        # Desabilitar SSL no httpx caso necessário para embeddings (apesar de google ser mais estável)
        custom_client = httpx.Client(verify=False)
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
            client=custom_client
        )
        
        # Local Qdrant Instance
        self.client = QdrantClient(path="./qdrant_local_db")
        self.collection_name = "diabetes_research"
        
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
            
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
        
        # LLM para responder às perguntas
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=settings.GEMINI_API_KEY
        )

    def ingest_document(self, text: str, metadata: dict = None):
        """Processa e armazena um texto/artigo acadêmico no banco vetorial."""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        # Cria documentos
        metadatas = [metadata or {} for _ in chunks]
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        return {"status": "success", "chunks_added": len(chunks)}

    def ask(self, question: str):
        """Consulta o banco vetorial para responder baseando-se nos artigos."""
        docs = self.vectorstore.similarity_search(question, k=4)
        context = "\n\n".join([d.page_content for d in docs])
        
        prompt = f'''Você é o Assistente Pesquisador do Leo, especialista em Diabetes Tipo 1 e 2.
Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE nos contextos fornecidos.
Se a resposta não estiver no contexto, diga que não encontrou informações na base científica.

Contextos Acadêmicos Encontrados:
{context}

Pergunta: {question}'''
        
        response = self.llm.invoke(prompt)
        return {
            "answer": response.content,
            "sources": [doc.metadata for doc in docs]
        }
