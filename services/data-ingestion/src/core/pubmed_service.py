import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class PubMedService:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = os.getenv('PUBMED_API_KEY', '')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def search_papers(self, query: str, max_results: int = 10) -> List[str]:
        try:
            logger.info(f"Searching PubMed for: {query}")
            search_url = f"{self.base_url}esearch.fcgi"
            params = {
                'db': 'pmc',
                'term': f"{query} AND open access[filter]",
                'retmax': max_results,
                'usehistory': 'y',
                'api_key': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(search_url, params=params)
                except httpx.RequestError as e:
                    logger.error(f"An error occurred while requesting PubMed: {e}")
                    return []
                
                if response.status_code != 200:
                    logger.error(f"PubMed API returned an error: {response.status_code}")
                    return []
                
                if "xml" not in response.headers.get("Content-Type", ""):
                    logger.error("Response is not XML.")
                    return []
                
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    logger.error(f"Failed to parse PubMed XML response: {e}")
                    return []

                id_list = root.findall(".//Id")
                pmids = [id_elem.text for id_elem in id_list]
                
                if not pmids:
                    logger.info("No papers found for the query.")
                else:
                    logger.info(f"Found {len(pmids)} papers: {pmids}")
                
                return pmids
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []

    async def fetch_paper_details(self, pmid: str) -> Dict:
        """Fetch detailed paper information"""
        try:
            fetch_url = f"{self.base_url}efetch.fcgi"
            params = {
                'db': 'pmc',
                'id': pmid,
                'retmode': 'xml',
                'api_key': self.api_key
            }
            
            response = await self.client.get(fetch_url, params=params)
            response.raise_for_status()
            return self._parse_paper_xml(response.content)
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching paper {pmid}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching paper {pmid}: {str(e)}")
            raise

    def _parse_paper_xml(self, xml_content: bytes) -> Dict:
        """Parse paper XML and extract relevant information"""
        root = ET.fromstring(xml_content)
        article = root.find(".//article")
        
        if article is None:
            return {}
            
        # Extract basic metadata
        paper_data = {
            "pmid": self._get_pmid(root),
            "title": self._get_title(article),
            "abstract": self._get_abstract(article),
            "publication_date": self._get_publication_date(article),
            "journal": self._get_journal(article),
            "authors": self._get_authors(article),
            "citations": self._get_citations(article),
            "full_text": self._get_full_text(article)
        }
        
        return paper_data

    def _get_pmid(self, root) -> str:
        pmid = root.find(".//article-id[@pub-id-type='pmc']")
        return pmid.text if pmid is not None else "Unknown"

    def _get_title(self, article) -> str:
        title_elem = article.find(".//article-title")
        return self._extract_text(title_elem) if title_elem is not None else "No title"

    def _get_abstract(self, article) -> str:
        abstract_elem = article.find(".//abstract")
        return self._extract_text(abstract_elem) if abstract_elem is not None else ""

    def _get_publication_date(self, article) -> Optional[datetime]:
        try:
            pub_date = article.find(".//pub-date")
            if pub_date is not None:
                year = pub_date.find("year")
                month = pub_date.find("month")
                day = pub_date.find("day")
                
                year = int(year.text) if year is not None else 1900
                month = int(month.text) if month is not None else 1
                day = int(day.text) if day is not None else 1
                
                return datetime(year, month, day)
        except Exception as e:
            logger.warning(f"Error parsing publication date: {str(e)}")
        return None

    def _get_journal(self, article) -> str:
        journal_elem = article.find(".//journal-title")
        return self._extract_text(journal_elem) if journal_elem is not None else ""

    def _get_authors(self, article) -> List[str]:
        authors = []
        author_list = article.findall(".//contrib[@contrib-type='author']")
        
        for author_elem in author_list:
            name_elem = author_elem.find(".//surname")
            if name_elem is not None:
                given_names = author_elem.find(".//given-names")
                full_name = f"{self._extract_text(name_elem)}"
                if given_names is not None:
                    full_name = f"{self._extract_text(given_names)} {full_name}"
                authors.append(full_name)
                
        return authors

    def _get_citations(self, article) -> List[str]:
        citations = []
        ref_list = article.findall(".//ref")
        
        for ref in ref_list:
            pub_id = ref.find(".//pub-id[@pub-id-type='pmid']")
            if pub_id is not None:
                citations.append(pub_id.text)
                
        return citations

    def _get_full_text(self, article) -> str:
        body_elem = article.find(".//body")
        return self._extract_text(body_elem) if body_elem is not None else ""

    def _extract_text(self, element) -> str:
        if element is None:
            return ""
        return ' '.join(element.itertext()).strip()