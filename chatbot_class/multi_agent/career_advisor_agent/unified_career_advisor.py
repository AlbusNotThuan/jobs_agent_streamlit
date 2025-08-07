# -*- coding: utf-8 -*-
"""
Unified Career Advisor Agent
Comprehensive career counseling system that integrates all functionalities
"""

import os
import sys
import numpy as np
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.psycopg_query import query_database
from chatbot_class.multi_agent.career_advisor_agent.agent_recommender.task_handler import TaskHandler

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


class UnifiedCareerAdvisor:
    """
    Unified Career Advisor Agent - comprehensive career counseling system
    
    This agent combines chatbot functionality with structured task processing
    for both interactive use and external agent integration.
    """
    
    def __init__(self, conversations_dir: str = "conversations"):
        """Initialize the unified career advisor agent."""
        try:
            # Initialize agent
            self.client = genai.Client(api_key=API_KEY)
            
            # Initialize task handler for structured processing
            self.task_handler = TaskHandler(conversations_dir)
            
            # Session management
            self.current_session_id = None
            self.conversation_history = []
            
            # Generation configuration
            self.generation_config = {
                'temperature': 0.1,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 4096,
                'response_mime_type': 'text/plain'
            }
            
            # Thinking configuration
            self.thinking_budget = 4096
            
            # Load system instruction
            self.system_instruction = self._load_system_instruction()
            
            # Setup tools
            self._setup_tools()
            
        except Exception as e:
            raise ValueError(f"Failed to initialize UnifiedCareerAdvisor: {e}")
    
    def _load_system_instruction(self) -> str:
        """Load career counseling system instruction."""
        instruction_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "system_instruction.md"
        )
        
        try:
            with open(instruction_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Could not read system_instruction.md: {e}")
            return """You are a backend career advisory service designed for programmatic integration. 
            Return structured JSON responses based on database analysis and AI reasoning."""
    
    def _setup_tools(self) -> None:
        """Setup available tools for career analysis."""
        try:
            self.available_tools = [
                query_database,
                self.get_similar_jobs_by_embedding,
                self.analyze_context_with_embeddings
            ]
            
            self.tool_functions = {
                'query_database': query_database,
                'get_similar_jobs_by_embedding': self.get_similar_jobs_by_embedding,
                'analyze_context_with_embeddings': self.analyze_context_with_embeddings
            }
            
        except Exception as e:
            print(f"⚠️ Warning: Could not setup all tools: {e}")
            self.available_tools = [query_database]
            self.tool_functions = {'query_database': query_database}
    
    def get_message_embedding(self, message: str) -> np.ndarray:
        """
        Generate an embedding vector for the given message using Gemini API.
        
        Args:
            message: The input message to embed.
            
        Returns:
            The embedding vector as numpy array.
        """
        try:
            result = self.client.models.embed_content(
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

    def get_similar_jobs_by_embedding(self, user_description: str, n: Optional[int] = None, threshold: float = 0.7) -> List[Dict[str, Any]]:
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
            # Generate embedding for user description
            embedding_vector = self.get_message_embedding(user_description)
            
            if len(embedding_vector) == 0:
                return []
            
            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, embedding_vector)) + ']'
            
            # Dynamic query based on whether n is specified
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
    
    def analyze_context_with_embeddings(self, context_text: str) -> List[Dict[str, Any]]:
        """
        Analyze user context using embedding similarity to find relevant jobs/skills.
        
        Args:
            context_text: Combined text from user messages and metadata
            
        Returns:
            List of relevant jobs and analysis
        """
        try:
            if not context_text.strip():
                return []
            
            # Find similar jobs using embeddings
            similar_jobs = self.get_similar_jobs_by_embedding(context_text)
            
            print(f"Found {len(similar_jobs)} contextually relevant jobs")
            return similar_jobs
            
        except Exception as e:
            print(f"❌ Error in context analysis: {e}")
            return []
    
    def process_career_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to process career counseling tasks.
        
        This is the unified entry point that handles the standardized input/output format.
        
        Args:
            task: Input task with sessionId, message, and metadata
            
        Returns:
            Standardized output task with career guidance
        """
        start_time = datetime.now()
        
        try:
            # Validate input
            validation = self.task_handler.validate_input_task(task)
            if not validation['valid']:
                return self.task_handler.create_failed_task(
                    start_time=start_time,
                    reason=f"Invalid input: {'; '.join(validation['errors'])}",
                    metadata={"validation_errors": validation['errors']}
                )
            
            # Extract components
            session_id = task.get('sessionId')
            messages = task['message']
            metadata = task.get('metadata', {})
            
            # Session management
            if session_id:
                if not self.task_handler.check_session_exists(session_id):
                    return self.task_handler.create_failed_task(
                        start_time=start_time,
                        reason=f"Session '{session_id}' not found",
                        session_id=session_id
                    )
                self.current_session_id = session_id
                # Load conversation history if needed
                self._load_session_history(session_id)
            else:
                # Create new session
                self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.conversation_history = []
            
            # Extract user query
            user_query = self.task_handler.extract_user_query(messages)
            if not user_query.strip():
                return self.task_handler.create_failed_task(
                    start_time=start_time,
                    reason="No user query found",
                    session_id=self.current_session_id
                )
            
            # Enhanced processing with context analysis
            enhanced_query = self._enhance_query_with_context(user_query, messages, metadata)
            
            # Process with career counseling
            result = self._process_with_ai(enhanced_query, messages)
            
            # Save conversation
            self._save_conversation_history(messages, result.get('final_response', ''))
            
            # Create output - determine state based on AI result
            end_time = datetime.now()
            
            if result.get('success', False):
                state = result.get('state', 'completed')  # Use state from AI processing
            else:
                state = "failed"
            
            return self.task_handler.create_output_task(
                start_time=start_time,
                end_time=end_time,
                session_id=self.current_session_id,
                state=state,
                process_sequence=result.get('process_sequence', []),
                final_response=result.get('final_response', 'No response generated'),
                metadata={
                    **metadata,
                    "agent_type": "unified_career_advisor",
                    "enhanced_processing": True,
                    "session_id": self.current_session_id,
                    "asks_for_info": result.get('process_sequence', [{}])[0].get('asks_for_info', False)
                }
            )
            
        except Exception as e:
            return self.task_handler.create_failed_task(
                start_time=start_time,
                reason=f"Processing error: {str(e)}",
                session_id=getattr(self, 'current_session_id', None),
                metadata={"error_details": str(e)}
            )
    
    def _enhance_query_with_context(self, query: str, messages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        """Enhance user query with contextual analysis using embeddings."""
        enhanced_parts = [query]
        
        try:
            # Combine all context into a single text for embedding analysis
            context_parts = [query]
            
            # Add previous messages context
            for msg in messages:
                if msg.get('content'):
                    context_parts.append(msg['content'])
            
            # Add metadata context
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    context_parts.append(f"{key}: {value}")
                elif isinstance(value, (list, tuple)):
                    context_parts.append(f"{key}: {', '.join(map(str, value))}")
            
            # Create comprehensive context text
            context_text = ". ".join(context_parts)
            
            if context_text.strip():
                # Analyze context with embeddings
                relevant_jobs = self.analyze_context_with_embeddings(context_text)
                
                if relevant_jobs:
                    enhanced_parts.append("\n\n--- Market Context Analysis ---")
                    enhanced_parts.append("Relevant Job Opportunities Found:")
                    
                    # Let AI decide how many jobs to include based on relevance
                    for job in relevant_jobs:
                        enhanced_parts.append(
                            f"- {job['job_expertise']} at {job['company_name']} "
                            f"(Relevance: {job['similarity_score']:.2f}, "
                            f"Experience: {job['years_experience']} years, "
                            f"Location: {job['location']})"
                        )
                    
                    enhanced_parts.append("--- End Context Analysis ---\n")
            
            # Add updated system instruction reference
            enhanced_parts.append("""
\n--- Processing Context ---
Use the market context analysis above to inform your structured JSON response.
Follow the system instruction format for backend service responses.
--- End Context ---
""")
            
        except Exception as e:
            print(f"⚠️ Could not enhance query with context: {e}")
            return query + "\n\nYou are a backend career advisory service. Analyze market data and return structured JSON response."
        
        return '\n'.join(enhanced_parts)
    
    def _process_with_ai(self, enhanced_query: str, original_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process the enhanced query with AI career counseling."""
        print("\n🔍 AI Processing Details:")
        print(f"   Enhanced query length: {len(enhanced_query)} chars")
        print(f"   Available tools: {[tool.__name__ if callable(tool) else str(tool) for tool in self.available_tools]}")
        print(f"   Conversation history: {len(self.conversation_history)} messages")
        
        try:
            # Prepare conversation for AI
            conversation_history = []
            
            # Add conversation history
            for msg in self.conversation_history[-5:]:  # Last 5 messages for context
                if msg['role'] in ['user', 'assistant']:
                    role = 'model' if msg['role'] == 'assistant' else 'user'
                    conversation_history.append(
                        types.Content(role=role, parts=[types.Part(text=msg['content'])])
                    )
            
            # Add current enhanced query
            conversation_history.append(
                types.Content(role="user", parts=[types.Part(text=enhanced_query)])
            )
            
            print(f"   Conversation parts for AI: {len(conversation_history)} parts")
            
            # Configure AI generation - remove JSON mime type to allow function calling
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=self.available_tools,
                tool_config={'function_calling_config': {'mode': 'AUTO'}},
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.thinking_budget,
                    include_thoughts=True
                ),
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=4096,
                response_mime_type='text/plain'  # Use text/plain to allow function calling
            )
            
            print("   Sending request to Gemini AI...")
            start_time = datetime.now()
            
            # Generate response
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation_history,
                config=config
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            print(f"   AI response time: {processing_time:.2f} seconds")
            
            # Check for function calls and log details
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                parts = response.candidates[0].content.parts
                print(f"   Response parts: {len(parts)}")
                
                # Log function calls if any
                for i, part in enumerate(parts):
                    if hasattr(part, 'function_call') and part.function_call:
                        print(f"   Part {i}: Function call to {part.function_call.name}")
                        print(f"      Args: {dict(part.function_call.args) if part.function_call.args else 'None'}")
                    elif hasattr(part, 'function_response') and part.function_response:
                        print(f"   Part {i}: Function response from {part.function_response.name}")
                        response_content = part.function_response.response
                        if isinstance(response_content, dict):
                            print(f"      Response keys: {list(response_content.keys())}")
                        else:
                            print(f"      Response: {str(response_content)[:100]}...")
                    elif hasattr(part, 'text') and part.text:
                        print(f"   Part {i}: Text response ({len(part.text)} chars)")
                    else:
                        print(f"   Part {i}: Unknown part type: {type(part)}")
            else:
                print("   No response parts found")
            
            # Process response and determine state
            if response.candidates:
                candidate = response.candidates[0]
                final_text = response.text or "No response generated"
                
                # Try to parse JSON response from text
                try:
                    import json
                    import re
                    
                    # Try to extract JSON from text response
                    json_match = re.search(r'\{[\s\S]*\}', final_text)
                    if json_match:
                        json_text = json_match.group(0)
                        json_response = json.loads(json_text)
                        
                        # Extract state from JSON
                        status = json_response.get('status', 'completed')
                        
                        # Map JSON status to our state format
                        if status == 'input_required':
                            state = "input-required"
                            response_type = "information_request"
                            asks_for_info = True
                        elif status == 'completed':
                            state = "completed" 
                            response_type = "career_advice"
                            asks_for_info = False
                        elif status == 'failed':
                            state = "failed"
                            response_type = "error"
                            asks_for_info = False
                        else:
                            state = "completed"
                            response_type = "career_advice"
                            asks_for_info = False
                        
                        return {
                            "success": True,
                            "state": state,
                            "final_response": json_text,  # Return the JSON part
                            "process_sequence": [{
                                "type": response_type,
                                "content": json_text,
                                "timestamp": datetime.now().isoformat(),
                                "asks_for_info": asks_for_info,
                                "json_parsed": True
                            }]
                        }
                    
                except (json.JSONDecodeError, AttributeError):
                    # If JSON extraction/parsing fails, continue with fallback
                    pass
                
                # Fallback to text analysis - check if response contains JSON structure
                is_json_like = '{' in final_text and '}' in final_text
                contains_status = 'status' in final_text.lower()
                
                if is_json_like and contains_status:
                    # Try to determine state from JSON-like content
                    if 'input_required' in final_text.lower():
                        state = "input-required"
                        response_type = "information_request"
                        asks_for_info = True
                    elif 'failed' in final_text.lower():
                        state = "failed"
                        response_type = "error"
                        asks_for_info = False
                    else:
                        state = "completed"
                        response_type = "career_advice"
                        asks_for_info = False
                else:
                    # Default to completed for non-JSON responses
                    state = "completed"
                    response_type = "career_advice"
                    asks_for_info = False
                
                return {
                    "success": True,
                    "state": state,
                    "final_response": final_text,
                    "process_sequence": [{
                        "type": response_type,
                        "content": final_text,
                        "timestamp": datetime.now().isoformat(),
                        "asks_for_info": asks_for_info,
                        "json_parsed": False
                    }]
                }
            else:
                return {
                    "success": False,
                    "final_response": "No response generated from AI",
                    "process_sequence": []
                }
                
        except Exception as e:
            print(f"❌ AI processing error: {e}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error details: {str(e)}")
            
            # Check if it's a tool-related error
            if "tool" in str(e).lower() or "function" in str(e).lower():
                print("   This appears to be a tool execution error")
                error_code = "TOOL_EXECUTION_ERROR"
            else:
                error_code = "AI_PROCESSING_ERROR"
                
            return {
                "success": False,
                "final_response": f"Error in career counseling: {str(e)}",
                "process_sequence": [{
                    "type": "error",
                    "content": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "error_code": error_code
                }]
            }
    
    def _load_session_history(self, session_id: str) -> None:
        """Load conversation history for session."""
        try:
            filepath = os.path.join(self.task_handler.conversations_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('messages', [])
        except Exception as e:
            print(f"⚠️ Could not load session history: {e}")
            self.conversation_history = []
    
    def _save_conversation_history(self, messages: List[Dict[str, Any]], response: str) -> None:
        """Save conversation history to file."""
        try:
            # Add messages to history
            for msg in messages:
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add assistant response
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response
            })
            
            # Save to file
            filepath = os.path.join(self.task_handler.conversations_dir, f"{self.current_session_id}.json")
            conversation_data = {
                "session_id": self.current_session_id,
                "created_at": datetime.now().isoformat(),
                "message_count": len(self.conversation_history),
                "messages": self.conversation_history
            }
            
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save conversation: {e}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this career advisor agent."""
        return {
            "agent_name": "Unified Career Advisor",
            "version": "2.0.0",
            "description": "Comprehensive AI career counseling system with embedding-based job matching",
            "capabilities": [
                "Personalized career guidance",
                "Skills gap analysis with embeddings",
                "Job market trend analysis",
                "Career transition planning", 
                "Learning path recommendations",
                "Embedding-based job matching",
                "Profile-driven career suggestions",
                "Data-driven market insights"
            ],
            "input_format": "Standardized task format with sessionId, message, metadata",
            "output_format": "Standardized task response with career guidance",
            "tools": ["database queries", "embedding similarity", "profile analysis"]
        }


# Main function for external integration with exact format specification
def get_career_advice(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function for external agents to get career counseling advice.

    IMPORTANT:
    - For best results, ALWAYS provide the full conversation history in the "message" field (not just the latest user query).
    - This allows the agent to understand context, user background, and previous clarifications.
    - If only the latest message is provided, the agent may ask for more information.

    Input Task Format:
    {
        "sessionId": str | None,        # Optional session ID for conversation continuity
        "message": List[Dict],          # List of message dicts with role/content. SHOULD include all previous turns for best context.
        "metadata": Dict                # Additional options like images (base64), urls, etc.
    }

    Output Task Format:
    {
        "start_time": str,              # ISO format timestamp
        "end_time": str,                # ISO format timestamp
        "sessionId": str,               # Session ID (existing or newly created)
        "state": str,                   # "completed", "failed", "input-required"
        "process_sequence": List,       # List of processing steps
        "final_response": str,          # Career advice or error/requirement message
        "metadata": Dict                # Additional processing information
    }

    Args:
        task: Input task dictionary with sessionId, message, metadata

    Returns:
        Standardized task output with career guidance
    """
    try:
        # Initialize agent
        agent = UnifiedCareerAdvisor()
        
        # Process with unified agent using exact format
        result = agent.process_career_task(task)
        
        return result
        
    except Exception as e:
        # Return standardized error format
        start_time = datetime.now()
        return {
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "sessionId": task.get("sessionId") or "error_session",
            "state": "failed",
            "process_sequence": [{
                "type": "error",
                "content": f"Career advice error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }],
            "final_response": f"Không thể xử lý yêu cầu tư vấn nghề nghiệp: {str(e)}",
            "metadata": {"error": str(e), "agent_type": "unified_career_advisor"}
        }
