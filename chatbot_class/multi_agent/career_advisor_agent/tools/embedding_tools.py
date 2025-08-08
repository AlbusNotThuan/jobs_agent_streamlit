import numpy as np
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
import os
import re
import json
from datetime import datetime
from .psycopg_query import query_database

API_KEY = os.getenv("GEMINI_API_KEY")

def get_message_embedding(message: str) -> np.ndarray:
    """
    Generate an embedding vector for the given message using Gemini API.
    Args:
        message: The input message to embed.
    Returns:
        The embedding vector as numpy array.
    """
    try:
        client = genai.Client(api_key=API_KEY)
        result = client.models.embed_content(
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
        print(f"❌ Error generating embedding: {e}")
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
