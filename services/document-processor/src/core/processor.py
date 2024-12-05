import spacy
import networkx as nx
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with spaCy model and citation graph"""
        self.nlp = spacy.load("en_core_web_sm")
        self.citation_graph = nx.DiGraph()
        
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
        """Process a single document and update citation graph"""
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
            
            # Extract methods (looking for words ending in 'sis', 'ing', etc.)
            method_patterns = r'\b\w+(?:sis|ing|tion|graphy|scopy|metry)\b'
            entities['methods'] = list(set(re.findall(method_patterns, full_text)))

            # Process citations and update graph
            citations = paper.get('citations', [])
            if citations:
                pmid = paper['pmid']
                for citation in citations:
                    self.citation_graph.add_edge(pmid, citation)
                    logger.info(f"Added citation: {pmid} -> {citation}")

            # Remove duplicates and empty values
            for category in entities:
                entities[category] = list(set(filter(None, entities[category])))
            
            return {
                'pmid': paper['pmid'],
                'processed_entities': entities,
                'citation_count': len(citations),
                'text_length': len(doc)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {paper.get('pmid')}: {str(e)}")
            raise

    def get_citation_network(self) -> Dict[str, Any]:
        """Get network statistics and citations analysis"""
        try:
            if not self.citation_graph.number_of_nodes():
                return {
                    'total_nodes': 0,
                    'total_edges': 0,
                    'top_cited': [],
                    'network_density': 0,
                    'average_citations': 0
                }
            
            in_degrees = dict(self.citation_graph.in_degree())
            top_cited = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_nodes': self.citation_graph.number_of_nodes(),
                'total_edges': self.citation_graph.number_of_edges(),
                'top_cited': top_cited,
                'network_density': nx.density(self.citation_graph),
                'average_citations': sum(in_degrees.values()) / len(in_degrees)
            }
        except Exception as e:
            logger.error(f"Error analyzing citation network: {str(e)}")
            raise

    async def analyze_citations(self, pmid: str) -> Dict[str, Any]:
        """Detailed citation analysis for a specific paper"""
        try:
            if not self.citation_graph.has_node(pmid):
                return {
                    'pmid': pmid,
                    'outgoing_citations': [],
                    'cited_by': [],
                    'citation_count': 0,
                    'cited_by_count': 0,
                    'citation_depth': 0
                }
            
            outgoing = list(self.citation_graph.successors(pmid))
            incoming = list(self.citation_graph.predecessors(pmid))
            
            # Calculate citation depth (longest path from this node)
            try:
                citation_depth = max(nx.single_source_shortest_path_length(self.citation_graph, pmid).values())
            except:
                citation_depth = 0
            
            return {
                'pmid': pmid,
                'outgoing_citations': outgoing,
                'cited_by': incoming,
                'citation_count': len(outgoing),
                'cited_by_count': len(incoming),
                'citation_depth': citation_depth
            }
        except Exception as e:
            logger.error(f"Error analyzing citations for {pmid}: {str(e)}")
            raise