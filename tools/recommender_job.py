import os
import sys
import psycopg
from typing import Optional
from dotenv import load_dotenv
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import numpy as np
from google import genai
from google.genai import types
from .psycopg_query import query_database
from utils.api_key_manager import get_api_key_manager
root_dir = os.path.abspath(os.path.dirname(__file__) + '/../')
if root_dir not in sys.path:
    sys.path.append(root_dir)

load_dotenv()
DB_CONNECTION = os.getenv('DB_CONNECTION')

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
        print(f"[RECOMMENDER_INIT] Initialized with API key ending in: ...{current_key[-6:]}")
    
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
    print(f"[RECOMMENDER_API_ERROR] {operation_name} failed: {error}")
    
    # Check for retryable errors
    retryable_indicators = [
        '400', 'bad request','500', 'internal', 'timeout', 'rate limit', 'quota', 
        'unavailable', '503', '429', 'server error'
    ]
    
    if any(indicator in error_str for indicator in retryable_indicators):
        try:
            next_key = _api_key_manager.next_key()
            _client = genai.Client(api_key=next_key)
            print(f"[RECOMMENDER_API_SWITCH] Switched to API key ending in: ...{next_key[-6:]}")
            return True
        except Exception as switch_error:
            print(f"[RECOMMENDER_API_ERROR] Failed to switch API key: {switch_error}")
    
    print(f"[RECOMMENDER_API_ERROR] Non-retryable error: {error}")
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
        message (str): The input message to embed.

    Returns:
        np.ndarray: The embedding vector.
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
        print(f"Embedding length: {embedding_length}")
        
        if hasattr(emb, 'values'):
            return np.array(emb.values)
        else:
            return np.array(emb)
            
    except Exception as e:
        print(f"❌ Error generating embedding after all retries: {e}")
        raise ValueError(f"Error generating embedding: {str(e)}")


def recommend_jobs(job_requirements: Dict[str, Optional[str]], n: int = 5) -> List[Dict[str, Any]]:
    """
    Recommend jobs based on user input using semantic similarity.

    Args:
        job_requirements (Dict[str, Optional[str]]): Dictionary containing:
            - industry: Industry/field (required)
            - position: Position/role (required)
            - skills: Skills (required)
            - interests: Interests (optional)
            - job_description: Job description (optional)
            - other_requirements: Other requirements (optional)
        n (int): Number of recommendations to return (default: 5)

    Returns:
        List[Dict[str, Any]]: List of recommended jobs with company_name, job_title, job_expertise, yoe, salary

    Raises:
        ValueError: If required fields are missing or empty
    """
    # Validate required fields
    required_fields = ['industry', 'position', 'skills']
    missing_fields = [field for field in required_fields if field not in job_requirements or not job_requirements[field] or job_requirements[field].strip() == '']
    if missing_fields:
        raise ValueError(
            f"The following required fields are missing or empty: {', '.join(missing_fields)}. "
            "Please provide all required information and try again. Do not auto-fill or guess missing content."
        )
    # Build input text from non-empty fields
    input_parts = []
    field_mapping = {
        'industry': 'Industry',
        'position': 'Position',
        'skills': 'Skills',
        'interests': 'Interests',
        'job_description': 'Job Description',
        'other_requirements': 'Other Requirements'
    }
    for field, label in field_mapping.items():
        if field in job_requirements and job_requirements[field] and job_requirements[field].strip():
            input_parts.append(f"{label}: {job_requirements[field].strip()}")
    # Combine all input parts
    input_text = ". ".join(input_parts)
    print(f"Input text for embedding: {input_text}")
    # Get embedding for the input
    try:
        embedding_vector = get_message_embedding(input_text)
        embedding_list = embedding_vector.tolist()
        print(f"Generated embedding with length: {len(embedding_list)}")
    except Exception as e:
        raise ValueError(f"Error generating embedding: {str(e)}")
    # Query database for similar jobs
    return query_similar_jobs(embedding_list, n)


def query_similar_jobs(embedding_vector: List[float], n: int) -> List[Dict[str, Any]]:
    """
    Query database for jobs similar to the embedding vector.

    Args:
        embedding_vector (List[float]): The embedding vector to compare against
        n (int): Number of results to return

    Returns:
        List[Dict[str, Any]]: List of similar jobs with similarity scores
    """
    # Convert embedding vector to PostgreSQL array format
    embedding_str = '[' + ','.join(map(str, embedding_vector)) + ']'
    sql_query = """
    SELECT
        j.job_title,
        j.job_expertise,
        j.yoe,
        j.salary,
        c.company_name,
        1 - (j.description_embedding <=> %s) AS similarity
    FROM
        public.job AS j
    JOIN
        public.company AS c ON j.company_id = c.company_id
    WHERE 
        j.description_embedding IS NOT NULL
    ORDER BY
        j.description_embedding <=> %s ASC
    LIMIT %s;
    """
    try:
        
        results = query_database(sql_query, [embedding_str, embedding_str, str(n)])
        if not results:
            return []
        recommendations = []
        for row in results:
            job_dict = {
                'job_title': row[0],
                'job_expertise': row[1],
                'yoe': row[2],
                'salary': row[3],
                'company_name': row[4]
            }
            recommendations.append(job_dict)
        print(f"Found {len(recommendations)} job recommendations")
        return recommendations
    except Exception as e:
        print(f"Database query error: {str(e)}")
        return []

