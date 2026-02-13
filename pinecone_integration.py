#!/usr/bin/env python3
"""
Pinecone Integration for LinkedIn & Twitter Content Automation
Handles vector embeddings, knowledge base queries, and content storage
"""

import os
import json
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeIntegration:
    """Manages all Pinecone operations for the automation system"""
    
    def __init__(self, api_key: str = None, environment: str = "production"):
        """Initialize Pinecone client"""
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment
        self.base_url = f"https://api.pinecone.io/v1"
        self.index_name = "linkedin-knowledge-base"
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")
        
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def initialize_index(self, dimension: int = 768, metric: str = "cosine") -> Dict[str, Any]:
        """
        Initialize or verify Pinecone index exists
        
        Args:
            dimension: Vector dimension (768 for Gemini embeddings)
            metric: Similarity metric (cosine, euclidean, dotproduct)
        
        Returns:
            Index status information
        """
        try:
            # Check if index exists
            response = requests.get(
                f"{self.base_url}/indexes/{self.index_name}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                logger.info(f"Index '{self.index_name}' already exists")
                return response.json()
            
            # Create index if doesn't exist
            create_payload = {
                "name": self.index_name,
                "dimension": dimension,
                "metric": metric,
                "spec": {
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/indexes",
                headers=self.headers,
                json=create_payload
            )
            
            if response.status_code == 201:
                logger.info(f"Created index '{self.index_name}' successfully")
                return response.json()
            else:
                logger.error(f"Failed to create index: {response.text}")
                return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Index initialization error: {str(e)}")
            return {"error": str(e)}
    
    def upsert_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, str]]], 
                      namespace: str = "content") -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone (insert or update)
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
            namespace: Vector namespace/partition
        
        Returns:
            Upsert status
        
        Example:
            vectors = [
                ("post_001", [0.1, 0.2, ...], {"title": "AI News", "source": "twitter"}),
                ("post_002", [0.3, 0.4, ...], {"title": "ML Update", "source": "reddit"})
            ]
        """
        try:
            vectors_payload = {
                "namespace": namespace,
                "vectors": [
                    {
                        "id": vid,
                        "values": embedding,
                        "metadata": metadata
                    }
                    for vid, embedding, metadata in vectors
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/vectors/upsert",
                headers=self.headers,
                json=vectors_payload
            )
            
            if response.status_code == 200:
                logger.info(f"Upserted {len(vectors)} vectors successfully")
                return {"success": True, "upserted_count": len(vectors)}
            else:
                logger.error(f"Upsert failed: {response.text}")
                return {"success": False, "error": response.text}
        
        except Exception as e:
            logger.error(f"Upsert error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def query_vectors(self, query_embedding: List[float], 
                     top_k: int = 5, 
                     namespace: str = "content",
                     filter_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query similar vectors from Pinecone
        
        Args:
            query_embedding: Query vector (same dimension as index)
            top_k: Number of top results to return
            namespace: Vector namespace to query in
            filter_metadata: Optional metadata filters
        
        Returns:
            Query results with similar vectors and metadata
        
        Example:
            results = pc.query_vectors([0.1, 0.2, ...], top_k=5)
            # Returns similar content about AI/automation topics
        """
        try:
            payload = {
                "namespace": namespace,
                "vector": query_embedding,
                "topK": top_k,
                "includeMetadata": True
            }
            
            if filter_metadata:
                payload["filter"] = filter_metadata
            
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json().get("matches", [])
                logger.info(f"Query returned {len(results)} matches")
                return {
                    "success": True,
                    "matches": results,
                    "query_count": len(results)
                }
            else:
                logger.error(f"Query failed: {response.text}")
                return {"success": False, "error": response.text}
        
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_vectors(self, vector_ids: List[str], 
                      namespace: str = "content") -> Dict[str, Any]:
        """
        Delete vectors from Pinecone
        
        Args:
            vector_ids: List of vector IDs to delete
            namespace: Vector namespace
        
        Returns:
            Deletion status
        """
        try:
            payload = {
                "namespace": namespace,
                "ids": vector_ids
            }
            
            response = requests.post(
                f"{self.base_url}/vectors/delete",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Deleted {len(vector_ids)} vectors successfully")
                return {"success": True, "deleted_count": len(vector_ids)}
            else:
                logger.error(f"Deletion failed: {response.text}")
                return {"success": False, "error": response.text}
        
        except Exception as e:
            logger.error(f"Deletion error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/indexes/{self.index_name}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Stats retrieval error: {str(e)}")
            return {"error": str(e)}
    
    def seed_knowledge_base(self, knowledge_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Seed Pinecone with initial knowledge base (expertise/content examples)
        
        Args:
            knowledge_items: List of knowledge pieces with content and metadata
        
        Example:
            items = [
                {
                    "id": "expertise_001",
                    "content": "RAG systems improve LLM accuracy by providing context...",
                    "topic": "AI/ML",
                    "source": "internal",
                    "embedding_vector": [0.1, 0.2, ...]
                }
            ]
        """
        try:
            vectors = []
            for item in knowledge_items:
                vector = item.get("embedding_vector", [])
                metadata = {
                    "content": item.get("content", ""),
                    "topic": item.get("topic", ""),
                    "source": item.get("source", "")
                }
                vectors.append((item.get("id"), vector, metadata))
            
            return self.upsert_vectors(vectors, namespace="knowledge-base")
        
        except Exception as e:
            logger.error(f"Knowledge base seeding error: {str(e)}")
            return {"success": False, "error": str(e)}


def main():
    """Test Pinecone integration"""
    
    # Initialize
    pc = PineconeIntegration()
    
    # Create/verify index
    print("Initializing Pinecone index...")
    index_status = pc.initialize_index()
    print(f"Index Status: {json.dumps(index_status, indent=2)}")
    
    # Get stats
    print("\nFetching index statistics...")
    stats = pc.get_index_stats()
    print(f"Index Stats: {json.dumps(stats, indent=2)}")
    
    print("\n✅ Pinecone integration ready!")


if __name__ == "__main__":
    main()
