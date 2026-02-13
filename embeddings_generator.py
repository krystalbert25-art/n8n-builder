#!/usr/bin/env python3
"""
Local Embeddings Generator using sentence-transformers and Chroma
Zero-cost RAG system for n8n automation
"""

import json
import sys
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Initialize embedding model (auto-downloads ~400MB first run)
# all-MiniLM-L6-v2: 384-dim, fast, good quality (recommended)
# all-mpnet-base-v2: 768-dim, slower, better quality
# paraphrase-MiniLM-L6-v2: 384-dim, good for paraphrasing

print("[Init] Loading embedding model...", file=sys.stderr)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Chroma with persistent storage
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
os.makedirs(db_path, exist_ok=True)

print(f"[Init] Initializing Chroma at: {db_path}", file=sys.stderr)
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=db_path,
    anonymized_telemetry=False
))

collection = client.get_or_create_collection(
    name="content_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

def embed_and_store(texts, metadata_list=None, ids=None):
    """
    Generate embeddings and store in Chroma
    Args:
        texts: list of strings to embed
        metadata_list: list of metadata dicts
        ids: list of unique IDs (auto-generated if None)
    """
    print(f"[Embed] Processing {len(texts)} documents...", file=sys.stderr)
    
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    
    # Generate IDs if not provided
    if ids is None:
        ids = [f"doc_{collection.count()}_{i}" for i in range(len(texts))]
    
    # Prepare data for upsert
    upsert_data = {
        "ids": ids,
        "embeddings": embeddings.tolist(),
        "documents": texts,
        "metadatas": metadata_list if metadata_list else [{"source": "unknown"} for _ in texts]
    }
    
    collection.upsert(**upsert_data)
    
    result = {
        "status": "success",
        "stored": len(texts),
        "total_in_collection": collection.count(),
        "ids": ids
    }
    
    print(f"[Embed] Stored {len(texts)} documents. Total: {collection.count()}", file=sys.stderr)
    return result

def search(query_text, top_k=5, metadata_filter=None):
    """
    Search vector DB for similar content
    Args:
        query_text: string to search for
        top_k: number of results
        metadata_filter: dict to filter by metadata
    """
    print(f"[Search] Query: '{query_text[:50]}...' (top_k={top_k})", file=sys.stderr)
    
    if collection.count() == 0:
        print("[Search] Collection is empty! Seed with documents first.", file=sys.stderr)
        return {
            "query": query_text,
            "results": [],
            "message": "Knowledge base is empty. Please embed documents first."
        }
    
    query_embedding = model.encode([query_text], convert_to_numpy=True)[0]
    
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        where=metadata_filter if metadata_filter else None
    )
    
    # Convert distance to similarity (1 - distance)
    formatted_results = []
    if results['documents'] and len(results['documents']) > 0:
        for doc, dist, meta in zip(
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        ):
            formatted_results.append({
                "content": doc,
                "similarity": float(1 - dist),
                "distance": float(dist),
                "metadata": meta
            })
    
    result = {
        "query": query_text,
        "results_count": len(formatted_results),
        "results": formatted_results
    }
    
    print(f"[Search] Found {len(formatted_results)} results", file=sys.stderr)
    return result

def delete_all():
    """Delete all documents from collection"""
    print(f"[Delete] Clearing collection...", file=sys.stderr)
    client.delete_collection(name="content_knowledge_base")
    return {"status": "deleted", "collection_cleared": True}

def get_stats():
    """Get collection statistics"""
    count = collection.count()
    return {
        "total_documents": count,
        "collection_name": "content_knowledge_base",
        "model": "all-MiniLM-L6-v2",
        "embedding_dimension": 384
    }

# CLI Interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage:
  python embeddings_generator.py search <query>
  python embeddings_generator.py embed <json_input>
  python embeddings_generator.py stats
  python embeddings_generator.py clear

Examples:
  echo '{"query": "machine learning"}' | python embeddings_generator.py search
  echo '[{"text": "AI is great", "source": "blog"}]' | python embeddings_generator.py embed
        """)
        sys.exit(1)
    
    action = sys.argv[1]
    
    try:
        if action == "search":
            # Read from stdin: {"query": "..."}
            input_data = json.loads(sys.stdin.read())
            result = search(input_data['query'], top_k=input_data.get('top_k', 5))
            print(json.dumps(result))
        
        elif action == "embed":
            # Read from stdin: [{"text": "...", "source": "..."}, ...]
            input_data = json.loads(sys.stdin.read())
            if not isinstance(input_data, list):
                input_data = [input_data]
            
            texts = [item.get('text', '') for item in input_data]
            metadata_list = [
                {
                    "source": item.get('source', 'unknown'),
                    "url": item.get('url', ''),
                    "title": item.get('title', '')
                }
                for item in input_data
            ]
            
            result = embed_and_store(texts, metadata_list)
            print(json.dumps(result))
        
        elif action == "stats":
            result = get_stats()
            print(json.dumps(result))
        
        elif action == "clear":
            result = delete_all()
            print(json.dumps(result))
        
        else:
            print(json.dumps({"error": f"Unknown action: {action}"}))
            sys.exit(1)
    
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON decode error: {str(e)}"}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
