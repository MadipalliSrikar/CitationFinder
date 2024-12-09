import spacy
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with spaCy model"""
        self.nlp = spacy.load("en_core_web_sm")
        
        # Scientific terms patterns
        self.scientific_patterns = [
            r"[A-Z]+\d+",  # Gene patterns like BRCA1
            r"\b[A-Z][A-Za-z]+ (syndrome|disease|disorder|cancer|therapy|treatment)\b",
            r"\b(in vitro|in vivo|ex vivo)\b",
            r"\b(p-value|confidence interval|statistical significance)\b",
            r"\b(DNA|RNA|mRNA|tRNA|miRNA|protein|enzyme|receptor)\b",
            r"\b(pathways?|signaling|mechanism)\b"
        ]

    def _extract_scientific_terms(self, text: str) -> List[str]:
        """Extract scientific terms using patterns and NER"""
        terms = set()
        
        # Pattern matching
        for pattern in self.scientific_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            terms.update(match.group() for match in matches)
        
        # NER based extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ['DISEASE', 'CHEMICAL', 'GENE', 'PROTEIN']:
                terms.add(ent.text)
        
        return list(terms)

    async def process_document(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document for entity extraction and analysis"""
        try:
            logger.info(f"Processing document {paper.get('pmid')}")
            abstract = paper.get('abstract', '')
            title = paper.get('title', '')
            full_text = f"{title}\n\n{abstract}"
            
            doc = self.nlp(full_text)
            
            # Extract entities
            entities = {
                'organizations': [],
                'scientific_terms': [],
                'chemicals': [],
                'diseases': [],
                'methods': []
            }
            
            # NER based extraction
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    entities['organizations'].append(ent.text)
                elif ent.label_ == 'CHEMICAL':
                    entities['chemicals'].append(ent.text)
                elif ent.label_ == 'DISEASE':
                    entities['diseases'].append(ent.text)
            
            # Add scientific terms
            entities['scientific_terms'] = self._extract_scientific_terms(full_text)
            
            # Extract methods
            method_patterns = r'\b\w+(?:sis|ing|tion|graphy|scopy|metry)\b'
            entities['methods'] = list(set(re.findall(method_patterns, full_text)))

            # Remove duplicates and empty values
            for category in entities:
                entities[category] = list(set(filter(None, entities[category])))
            
            return {
                'pmid': paper['pmid'],
                'title': title,
                'abstract': abstract,
                'processed_entities': entities,
                'text_length': len(doc)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {paper.get('pmid')}: {str(e)}")
            raise