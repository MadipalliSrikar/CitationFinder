import requests
import xml.etree.ElementTree as ET
import html
import re
from typing import List, Dict, Optional
from ..utils.logger import setup_logger
from .config import get_settings
import httpx
from datetime import datetime

logger = setup_logger(__name__)
settings = get_settings()

class PubMedService:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = api_key or settings.pubmed_api_key

    async def search_papers(self, query: str, max_results: int = 10) -> List[str]:
        """Search PubMed Central for papers"""
        try:
            logger.info(f"Searching PMC for: {query}")
            search_url = f"{self.base_url}esearch.fcgi"
            params = {
                'db': 'pmc',
                'term': f"{query} AND open access[filter]",
                'retmax': max_results,
                'usehistory': 'y',
                'api_key': self.api_key
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            id_list = root.findall(".//Id")
            pmids = [id_elem.text for id_elem in id_list]
            
            logger.info(f"Found {len(pmids)} papers")
            return pmids
            
        except Exception as e:
            logger.error(f"Error searching papers: {str(e)}")
            raise

    def _extract_text(self, element) -> str:
        """Extract clean text from XML element"""
        if element is None:
            return ""
        text = ' '.join(element.itertext()).strip()
        text = re.sub(r'\s+', ' ', text)
        return html.unescape(text)

    async def fetch_paper_details(self, pmid: str) -> Dict:
        """Fetch detailed paper information"""
        try:
            logger.info(f"Fetching details for PMID: {pmid}")
            fetch_url = f"{self.base_url}efetch.fcgi"
            params = {
                'db': 'pmc',
                'id': pmid,
                'retmode': 'xml',
                'api_key': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(fetch_url, params=params)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                article = root.find(".//article")
                
                if article is None:
                    raise ValueError(f"No article found for PMID {pmid}")
                
                # Extract article components
                title = self._extract_text(article.find(".//article-title"))
                abstract = self._extract_text(article.find(".//abstract"))
                
                # Extract authors
                authors = []
                author_list = article.findall(".//contrib[@contrib-type='author']")
                for author_elem in author_list:
                    surname = self._extract_text(author_elem.find(".//surname"))
                    given_names = self._extract_text(author_elem.find(".//given-names"))
                    if surname or given_names:
                        full_name = f"{given_names} {surname}".strip()
                        if full_name:
                            authors.append({"name": full_name})
                
                return {
                    "pmid": pmid,
                    "title": title or "No title available",
                    "abstract": abstract,
                    "journal": self._extract_text(article.find(".//journal-title")),
                    "publication_date": self._parse_publication_date(article),
                    "authors": authors  # Now returning list of author objects
                }
        except Exception as e:
            logger.error(f"Error fetching paper {pmid}: {str(e)}")
            raise   

    def _parse_publication_date(self, article) -> Optional[datetime]:
        try:
            pub_date = article.find(".//pub-date")
            if pub_date is not None:
                year = int(self._extract_text(pub_date.find("year")) or "1900")
                month = int(self._extract_text(pub_date.find("month")) or "1")
                day = int(self._extract_text(pub_date.find("day")) or "1")
                return datetime(year, month, day)
            return None
        except Exception:
            return None
