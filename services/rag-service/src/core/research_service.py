from transformers import T5Tokenizer, T5ForConditionalGeneration
from llama_index import VectorStoreIndex, Document, ServiceContext
from llama_index.llms import HuggingFaceLLM
from llama_index.embeddings import HuggingFaceEmbedding
import torch
import time
from typing import Dict, List, Any
from ..utils.logger import setup_logger
from .config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class ResearchService:
    def __init__(self):
        logger.info("Initializing Research Service...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize T5
        self.tokenizer = T5Tokenizer.from_pretrained(settings.t5_model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(settings.t5_model_name)
        self.model.to(self.device)
        
        # Initialize LLM
        self.llm = HuggingFaceLLM(
            tokenizer=self.tokenizer,
            model=self.model,
            context_window=512,
            max_new_tokens=settings.max_summary_length,
            model_kwargs={"temperature": 0.7}
        )
        
        # Initialize local embeddings
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Create service context with local embeddings
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model=self.embed_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        self.index = None
        logger.info("Research Service initialized")

    async def process_with_t5(self, text: str, task: str = "summarize") -> Dict[str, Any]:
        """Process text with T5 using specific tasks"""
        try:
            start_time = time.time()
            logger.info(f"Processing with T5 - Task: {task}")
            
            task_prefixes = {
                "summarize": "summarize: ",
                "analyze": "analyze the methodology: ",
                "extract_methods": "extract research methods: ",
                "find_conclusions": "what are the main conclusions: "
            }
            
            prefix = task_prefixes.get(task, "summarize: ")
            input_text = prefix + text
            
            inputs = self.tokenizer.encode(
                input_text,
                return_tensors="pt",
                max_length=settings.max_input_length,
                truncation=True
            ).to(self.device)
            
            outputs = self.model.generate(
                inputs,
                max_length=settings.max_summary_length,
                min_length=settings.min_summary_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            processing_time = time.time() - start_time
            
            return {
                "result": result,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in T5 processing: {str(e)}")
            raise

    async def create_index_from_papers(self, papers: List[Dict]) -> str:
        """Create RAG index from papers"""
        try:
            logger.info(f"Creating index from {len(papers)} papers")
            
            # Convert papers to Documents
            documents = []
            for paper in papers:
                # Combine paper information into a single text
                text = (
                    f"Title: {paper['title']}\n"
                    f"Authors: {', '.join([a['name'] for a in paper['authors']])}\n"
                    f"Abstract: {paper['abstract']}\n"
                    f"Journal: {paper['journal']}\n"
                    f"PMID: {paper['pmid']}"
                )
                
                # Create Document with metadata
                doc = Document(
                    text=text,
                    metadata={
                        "pmid": paper["pmid"],
                        "title": paper["title"],
                        "source": "PubMed"
                    }
                )
                documents.append(doc)
            
            # Create the index
            self.index = VectorStoreIndex.from_documents(
                documents,
                service_context=self.service_context
            )
            
            logger.info("Index created successfully")
            return "Index created successfully"
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise

    async def query_papers(self, query: str, query_type: str = "research") -> Dict[str, Any]:
        """Query indexed papers with different types of queries"""
        if not self.index:
            raise ValueError("No papers have been indexed yet. Please create an index first.")
        
        try:
            logger.info(f"Processing query: {query} (type: {query_type})")
            start_time = time.time()
            
            # Define query templates for different types of queries
            query_templates = {
                "research": "Based on the research papers, {query}",
                "methodology": "What research methods were used to study {query}?",
                "findings": "What are the key findings about {query}?",
                "comparison": "Compare different approaches or findings regarding {query}",
                "implications": "What are the implications or future directions for {query}?",
                "basic": "{query}"
            }
            
            # Format query based on type
            template = query_templates.get(query_type, query_templates["basic"])
            formatted_query = template.format(query=query)
            
            # Create query engine with response synthesis
            query_engine = self.index.as_query_engine(
                similarity_top_k=3,  # Number of relevant chunks to consider
                response_mode="tree_summarize"  # Synthesize information from multiple chunks
            )
            
            # Execute query
            response = query_engine.query(formatted_query)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_info = {
                        "pmid": node.node.metadata.get("pmid"),
                        "title": node.node.metadata.get("title"),
                        "relevance_score": float(node.score) if node.score else 0.0,
                        "excerpt": node.node.text[:200] + "..."  # Preview of source text
                    }
                    sources.append(source_info)
            
            processing_time = time.time() - start_time
            
            return {
                "response": str(response),
                "sources": sources,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error querying papers: {str(e)}")
            raise