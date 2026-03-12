import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict
from backend.services.rag_service import RAGService
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ResearchService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
    async def search_pubmed(self, query: str, max_results: int = 5) -> List[str]:
        """Busca IDs de artigos no PubMed baseados em uma query."""
        search_url = f"{self.pubmed_base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "api_key": getattr(settings, "PUBMED_API_KEY", None) # Opcional
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("esearchresult", {}).get("idlist", [])
            else:
                logger.error(f"Erro ao buscar no PubMed: {response.status_code}")
                return []

    async def fetch_pubmed_details(self, id_list: List[str]) -> List[Dict]:
        """Busca os detalhes (título e abstract) dos artigos do PubMed."""
        if not id_list:
            return []
            
        fetch_url = f"{self.pubmed_base_url}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        
        articles = []
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(fetch_url, params=params)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                for article in root.findall(".//PubmedArticle"):
                    title = article.find(".//ArticleTitle")
                    abstract = article.find(".//AbstractText")
                    
                    title_text = title.text if title is not None else "Sem título"
                    abstract_text = abstract.text if abstract is not None else "Sem resumo disponível"
                    
                    articles.append({
                        "title": title_text,
                        "content": abstract_text,
                        "source": "PubMed",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.find('.//PMID').text}/"
                    })
            else:
                logger.error(f"Erro ao buscar detalhes no PubMed: {response.status_code}")
        
        return articles

    async def scrape_diabetes_org_br(self) -> List[Dict]:
        """
        Scraper básico para diabetes.org.br. 
        Nota: Em um sistema real, usaríamos RSS ou um crawler robusto.
        Aqui simularemos a busca de notícias principais.
        """
        articles = []
        url = "https://diabetes.org.br/category/noticias/"
        
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    # Implementação simplificada: Pegaríamos títulos e links via BeautifulSoup
                    # Por agora, para o MVP, vamos focar no PubMed que é estruturado.
                    pass
        except Exception as e:
            logger.error(f"Erro ao fazer scrape no diabetes.org.br: {e}")
            
        return articles

    async def run_autonomous_research(self, topic: str = "Type 1 Diabetes breakthrough"):
        """Executa a rotina completa de busca e ingestão."""
        logger.info(f"Iniciando pesquisa autônoma sobre: {topic}")
        
        # 1. Buscar no PubMed
        pubmed_ids = await self.search_pubmed(topic)
        pubmed_articles = await self.fetch_pubmed_details(pubmed_ids)
        
        # 2. Ingestão no RAG
        for art in pubmed_articles:
            full_text = f"Título: {art['title']}\n\nResumo: {art['content']}"
            metadata = {
                "title": art["title"],
                "source": art["source"],
                "url": art["url"],
                "topic": topic
            }
            self.rag_service.ingest_document(full_text, metadata)
            
        return {
            "status": "completed",
            "articles_found": len(pubmed_articles),
            "topic": topic
        }
