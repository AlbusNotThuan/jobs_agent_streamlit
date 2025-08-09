import numpy as np
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
import os
import re
import json
from datetime import datetime
from .psycopg_query import query_database
from ..utils.api_key_manager import get_api_key_manager

# Initialize API key manager globally
_api_key_manager = None
_client = None

def _get_api_client():
    """Get or initialize API client with key management."""
    global _api_key_manager, _client
    
    if _api_key_manager is None:
        _api_key_manager = get_api_key_manager()
        
    if _client is None:
        current_key = _api_key_manager.get_current_key()
        _client = genai.Client(api_key=current_key)
        print(f"[EMBEDDING_INIT] Initialized with API key ending in: ...{current_key[-6:]}")
    
    return _client

def _handle_api_error_and_retry(error, operation_name: str = "API call"):
    """
    Handle API errors and retry with next key if appropriate.
    
    Args:
        error: The exception that occurred
        operation_name: Name of the operation for logging
        
    Returns:
        bool: True if should retry with new key, False if error is non-retryable
    """
    global _client, _api_key_manager
    
    error_str = str(error).lower()
    print(f"[EMBEDDING_API_ERROR] {operation_name} failed: {error}")
    
    # Check for retryable errors
    retryable_indicators = [
        '400', 'bad request','500', 'internal', 'timeout', 'rate limit', 'quota', 
        'unavailable', '503', '429', 'server error'
    ]
    
    if any(indicator in error_str for indicator in retryable_indicators):
        try:
            next_key = _api_key_manager.next_key()
            _client = genai.Client(api_key=next_key)
            print(f"[EMBEDDING_API_SWITCH] Switched to API key ending in: ...{next_key[-6:]}")
            return True
        except Exception as switch_error:
            print(f"[EMBEDDING_API_ERROR] Failed to switch API key: {switch_error}")
    
    print(f"[EMBEDDING_API_ERROR] Non-retryable error: {error}")
    return False

def _safe_api_call(api_function, *args, **kwargs):
    """
    Execute API call with automatic key rotation on retryable errors.
    Will rotate through all API keys up to 100 attempts, looping if needed.
    """
    last_exception = None
    max_attempts = 100
    for attempt in range(max_attempts):
        try:
            return api_function(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if not _handle_api_error_and_retry(e, f"API call attempt {attempt + 1}"):
                break
    raise last_exception

def get_message_embedding(message: str) -> np.ndarray:
    """
    Generate an embedding vector for the given message using Gemini API.
    Args:
        message: The input message to embed.
    Returns:
        The embedding vector as numpy array.
    """
    try:
        client = _get_api_client()
        
        # Use safe API call with automatic key rotation
        result = _safe_api_call(
            client.models.embed_content,
            model="gemini-embedding-001",
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            contents=[message]
        )
        
        emb = result.embeddings[0]
        embedding_length = len(emb.values) if hasattr(emb, 'values') else len(emb)
        print(f"Generated embedding with length: {embedding_length}")
        
        if hasattr(emb, 'values'):
            return np.array(emb.values)
        else:
            return np.array(emb)
            
    except Exception as e:
        print(f"❌ Error generating embedding after all retries: {e}")
        return np.array([])

def get_similar_jobs_by_embedding(user_description: str, n: Optional[int] = None, threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Find jobs similar to user description using embedding similarity.
    Args:
        user_description: Description of user's career interests/goals
        n: Number of results to return (if None, returns all relevant jobs above threshold)
        threshold: Minimum similarity threshold (default 0.7)
    Returns:
        List of similar jobs with similarity scores
    """
    try:
        embedding_vector = get_message_embedding(user_description)
        if len(embedding_vector) == 0:
            return []
        embedding_str = '[' + ','.join(map(str, embedding_vector)) + ']'
        if n is not None:
            sql_query = """
            SELECT
                j.job_title,
                j.job_expertise,
                j.yoe,
                j.salary,
                c.company_name,
                j.location,
                1 - (j.description_embedding <=> %s) AS similarity
            FROM
                public.job AS j
            JOIN
                public.company AS c ON j.company_id = c.company_id
            WHERE 
                j.description_embedding IS NOT NULL
                AND (1 - (j.description_embedding <=> %s)) > %s
            ORDER BY
                j.description_embedding <=> %s ASC
            LIMIT %s;
            """
            results = query_database(sql_query, [embedding_str, embedding_str, str(threshold), embedding_str, str(n)])
        else:
            sql_query = """
            SELECT
                j.job_title,
                j.job_expertise,
                j.yoe,
                j.salary,
                c.company_name,
                j.location,
                1 - (j.description_embedding <=> %s) AS similarity
            FROM
                public.job AS j
            JOIN
                public.company AS c ON j.company_id = c.company_id
            WHERE 
                j.description_embedding IS NOT NULL
                AND (1 - (j.description_embedding <=> %s)) > %s
            ORDER BY
                j.description_embedding <=> %s ASC;
            """
            results = query_database(sql_query, [embedding_str, embedding_str, str(threshold), embedding_str])
        if not results:
            return []
        recommendations = []
        for row in results:
            job_dict = {
                'job_title': row[0],
                'job_expertise': row[1],
                'years_experience': row[2],
                'salary': row[3],
                'company_name': row[4],
                'location': row[5],
                'similarity_score': float(row[6]) if row[6] else 0.0
            }
            recommendations.append(job_dict)
        print(f"Found {len(recommendations)} similar jobs using embeddings")
        return recommendations
    except Exception as e:
        print(f"❌ Error in embedding-based job search: {e}")
        return []
