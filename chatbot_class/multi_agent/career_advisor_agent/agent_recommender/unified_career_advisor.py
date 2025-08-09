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

from .tools.psycopg_query import query_database
from .tools.embedding_tools import get_similar_jobs_by_embedding
from .task_handler import TaskHandler
from .utils.api_key_manager import get_api_key_manager

# Load environment variables
load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")  # Replaced with API key manager


class UnifiedCareerAdvisor:
    """
    Unified Career Advisor Agent - comprehensive career counseling system
    
    This agent combines chatbot functionality with structured task processing
    for both interactive use and external agent integration.
    """
    
    def __init__(self, conversations_dir: str = None):
        """Initialize the unified career advisor agent."""
        try:
            # Initialize API key manager
            self.api_key_manager = get_api_key_manager()
            
            # Initialize agent with first available API key
            current_key = self.api_key_manager.get_current_key()
            self.client = genai.Client(api_key=current_key)
            print(f"[API_INIT] Initialized with API key ending in: ...{current_key[-6:]}")

            # Initialize task handler for structured processing
            self.task_handler = TaskHandler(conversations_dir)

            # Session management
            self.current_session_id = None
            self.conversation_history = []
            self._current_tool_history = []  # Track tool usage history

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

            # Load system and db schema instructions
            self.system_instruction = self._load_system_instruction()
            self.db_schema_instruction = self._load_db_schema_instruction()

            # Combine both instructions for use in AI config
            self.full_instruction = self.system_instruction + "\n\n" + self.db_schema_instruction

            # Setup tools
            self._setup_tools()

        except Exception as e:
            raise ValueError(f"Failed to initialize UnifiedCareerAdvisor: {e}")
    
    def _handle_api_error_and_retry(self, error, operation_name: str = "API call"):
        """
        Handle API errors and retry with next key if appropriate.
        
        Args:
            error: The exception that occurred
            operation_name: Name of the operation for logging
            
        Returns:
            bool: True if should retry with new key, False if error is non-retryable
        """
        error_str = str(error).lower()
        print(f"[API_ERROR] {operation_name} failed: {error}")
        
        # # Check if it's a 400 error (don't retry)
        # if '400' in error_str or 'bad request' in error_str:
        #     print(f"[API_ERROR] 400 error detected - not switching key")
        #     return False
            
        # Check for other retryable errors
        retryable_indicators = [
            '400', 'bad request','500', 'internal', 'timeout', 'rate limit', 'quota', 
            'unavailable', '503', '429', 'server error'
        ]
        
        if any(indicator in error_str for indicator in retryable_indicators):
            try:
                # Switch to next API key
                old_key = self.api_key_manager.get_current_key()
                new_key = self.api_key_manager.next_key()
                print(new_key)
                # Reinitialize client with new key
                self.client = genai.Client(api_key=new_key)
                
                print(f"[API_SWITCH] Switched from ...{old_key[-6:]} to ...{new_key[-6:]}")
                print(f"[API_SWITCH] Ready to retry {operation_name}")
                return True
                
            except Exception as switch_error:
                print(f"[API_SWITCH_ERROR] Failed to switch API key: {switch_error}")
                return False
        
        print(f"[API_ERROR] Non-retryable error: {error}")
        return False
    
    def _safe_api_call(self, api_function, *args, **kwargs):
        """
        Execute API call with automatic key rotation on retryable errors.
        Will rotate through all API keys up to 100 attempts, looping if needed.
        """
        last_exception = None
        max_attempts = 100
        for attempt in range(max_attempts):
            try:
                print(f"[API_CALL] Attempt {attempt + 1}/{max_attempts} - {api_function.__name__}")
                return api_function(*args, **kwargs)
            except Exception as e:
                last_exception = e
                should_retry = self._handle_api_error_and_retry(e, api_function.__name__)
                if should_retry:
                    print(f"[API_RETRY] Retrying with next key (attempt {attempt + 2})")
                    continue
                print(f"[API_FINAL_ERROR] Final error after {attempt + 1} attempts: {e}")
                break
        raise last_exception
    
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
            print(f"[WARNING] Could not read system_instruction.md: {e}")
            return "You are a backend career advisory service designed for programmatic integration. Return structured JSON responses based on database analysis and AI reasoning."

    def _load_db_schema_instruction(self) -> str:
        """Load database schema instruction."""
        schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "db_schema_instruction.md"
        )
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[WARNING] Could not read db_schema_instruction.md: {e}")
            return ""
    
    def _setup_tools(self) -> None:
        """Setup available tools for career analysis."""
        try:            
            # Define the response_to_agent tool
            def response_to_agent(
                status: str,
                data: Dict[str, Any],
                analysis: Dict[str, Any],
                sessionId: Optional[str] = None,
                process_sequence: Optional[List[Dict[str, Any]]] = None,
                metadata: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]:
                """
                Tool to send response back to calling agent when analysis is complete.
                
                Only use this tool when you have determined the final state of the request:
                - "completed": Analysis finished successfully with career advice
                - "failed": Processing failed with error information  
                - "input_required": Need more information from user
                
                Do NOT use this tool if you need more time to analyze, use other tools, 
                or enhance reasoning. Only call when ready to provide final response.
                
                Args:
                    status: Must be "completed", "failed", or "input_required"
                    data: The data section following the unified format structure
                    analysis: The analysis section with reasoning, confidence_score, criteria_used, strengths, weaknesses, market_context
                    sessionId: Session ID for the conversation (optional)
                    process_sequence: List of processing steps taken (optional)
                    metadata: Additional metadata (optional)
                    
                Returns:
                    Unified response format with status, data, and analysis
                """
                print(f"[TOOL_CALL] response_to_agent invoked")
                print(f"[TOOL_INPUT] status: {status}")
                print(f"[TOOL_INPUT] data keys: {list(data.keys()) if data else 'None'}")
                print(f"[TOOL_INPUT] analysis keys: {list(analysis.keys()) if analysis else 'None'}")
                print(f"[TOOL_INPUT] sessionId: {sessionId}")
                print(f"[TOOL_INPUT] process_sequence: {len(process_sequence) if process_sequence else 0} steps")
                print(f"[TOOL_INPUT] metadata: {list(metadata.keys()) if metadata else 'None'}")
                
                if status not in ["completed", "failed", "input_required"]:
                    error_msg = f"Invalid status: {status}. Must be 'completed', 'failed', or 'input_required'"
                    print(f"[TOOL_ERROR] {error_msg}")
                    raise ValueError(error_msg)
                
                # Validate analysis structure
                required_analysis_fields = ["reasoning", "confidence_score", "criteria_used", "strengths", "weaknesses", "market_context"]
                for field in required_analysis_fields:
                    if field not in analysis:
                        error_msg = f"Missing required analysis field: {field}"
                        print(f"[TOOL_ERROR] {error_msg}")
                        raise ValueError(error_msg)
                
                # Build the unified response format
                result = {
                    "status": status,
                    "data": data,
                    "analysis": analysis
                }
                
                # Add optional metadata for tracking
                if sessionId or process_sequence or metadata:
                    result["_metadata"] = {
                        "sessionId": sessionId,
                        "process_sequence": process_sequence or [],
                        "additional_metadata": metadata or {},
                        "timestamp": datetime.now().isoformat()
                    }
                
                print(f"[TOOL_OUTPUT] response_to_agent result with status: {result['status']}")
                print(f"[TOOL_SUCCESS] response_to_agent executed successfully")
                return result
            
            
            # Make response_to_agent available to the AI
            self.response_to_agent_tool = response_to_agent
            
            self.available_tools = [
                query_database,
                get_similar_jobs_by_embedding,
                response_to_agent
            ]
            self.tool_functions = {
                'query_database': query_database,
                'get_similar_jobs_by_embedding': get_similar_jobs_by_embedding,
                'response_to_agent': response_to_agent
            }
        except Exception as e:
            print(f"[WARNING] Warning: Could not setup all tools: {e}")
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
            # Use safe API call with automatic key rotation
            result = self._safe_api_call(
                self.client.models.embed_content,
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
            print(f"[ERROR] Error generating embedding after retries: {e}")
            return np.array([])

    
    
    def process_career_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to process career counseling tasks.
        
        Args:
            task: Input task with sessionId, message, and metadata
            
        Returns:
            Unified format response: {status, data, analysis, _metadata}
        """
        start_time = datetime.now()
        self._task_start_time = start_time
        self._current_tool_history = []
        
        print(f"\n[PROCESS_CAREER_TASK] Starting at {start_time.isoformat()}")
        
        try:
            # Validate input
            validation = self.task_handler.validate_input_task(task)
            if not validation['valid']:
                return {
                    "status": "failed",
                    "data": {
                        "error_type": "VALIDATION_ERROR",
                        "error_message": f"Invalid input: {'; '.join(validation['errors'])}",
                        "fallback_guidance": "Please provide valid task format with message field",
                        "suggested_action": "Check input format and retry"
                    },
                    "analysis": {
                        "reasoning": "Input validation failed - required fields missing or invalid",
                        "confidence_score": 0.0,
                        "criteria_used": ["input_validation"],
                        "strengths": [],
                        "weaknesses": ["Invalid input format"],
                        "market_context": "Cannot process without valid input"
                    },
                    "_metadata": {
                        "sessionId": task.get('sessionId'),
                        "process_sequence": [],
                        "timestamp": start_time.isoformat(),
                        "processing_time": 0.0
                    }
                }
            
            # Extract components
            session_id = task.get('sessionId')
            messages = task['message']
            metadata = task.get('metadata', {})
            
            # Session management
            if session_id:
                if not self.task_handler.check_session_exists(session_id):
                    return {
                        "status": "failed",
                        "data": {
                            "error_type": "SESSION_ERROR",
                            "error_message": f"Session '{session_id}' not found",
                            "fallback_guidance": "Create new session or use valid session ID",
                            "suggested_action": "Start new conversation or check session ID"
                        },
                        "analysis": {
                            "reasoning": f"Requested session '{session_id}' does not exist",
                            "confidence_score": 0.0,
                            "criteria_used": ["session_validation"],
                            "strengths": [],
                            "weaknesses": ["Invalid session reference"],
                            "market_context": "Cannot continue without valid session"
                        },
                        "_metadata": {
                            "sessionId": session_id,
                            "process_sequence": [],
                            "timestamp": start_time.isoformat(),
                            "processing_time": 0.0
                        }
                    }
                self.current_session_id = session_id
                self._load_session_history(session_id)
                print(f"Loaded session history for session ID: {session_id}")
                print(f"Current conversation history: {self.conversation_history}")
            else:
                self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.conversation_history = []
                print(f"Created new session with ID: {self.current_session_id}")
                print(f"Current conversation history: {self.conversation_history}")

            # Extract user query
            user_query = self.task_handler.extract_user_query(messages)
            if not user_query.strip():
                return {
                    "status": "input_required",
                    "data": {
                        "specific_need": "User query is required to provide career guidance",
                        "suggested_context": "Please provide your career question or area of interest",
                        "why_needed": "Cannot analyze career needs without user input"
                    },
                    "analysis": {
                        "reasoning": "No user query found - career analysis requires user input",
                        "confidence_score": 0.0,
                        "criteria_used": ["query_validation"],
                        "strengths": [],
                        "weaknesses": ["Missing user query"],
                        "market_context": "Ready to analyze once query is provided"
                    },
                    "_metadata": {
                        "sessionId": self.current_session_id,
                        "process_sequence": [],
                        "timestamp": start_time.isoformat(),
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                }
            
            # Process with AI
            result = self._process_with_ai(user_query, messages, metadata)
            
            # Save conversation
            self._save_conversation_history(messages, result.get('final_response', ''))
            
            # Build simplified process_sequence (only tool calls, no outputs)
            process_sequence = []
            for history_item in self._current_tool_history:
                if history_item.get('type') == 'function_call':
                    process_sequence.append({
                        "tool": history_item['name'],
                        "args": history_item.get('args', {}),
                        "timestamp": history_item['timestamp']
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Return result based on whether response_to_agent was used
            if result.get('used_response_tool', False):
                tool_result = result.get('tool_response', {})
                # Add metadata to tool result
                tool_result['_metadata'] = {
                    "sessionId": self.current_session_id,
                    "process_sequence": process_sequence,
                    "timestamp": start_time.isoformat(),
                    "processing_time": processing_time
                }
                return tool_result
            else:
                # Convert fallback responses to unified format
                final_response = result.get('final_response', '')
                state = result.get('state', 'completed')
                
                # Try to parse JSON if available
                if final_response.strip().startswith('{'):
                    try:
                        json_data = json.loads(final_response)
                        if 'status' in json_data and 'data' in json_data and 'analysis' in json_data:
                            # Already in unified format
                            json_data['_metadata'] = {
                                "sessionId": self.current_session_id,
                                "process_sequence": process_sequence,
                                "timestamp": start_time.isoformat(),
                                "processing_time": processing_time
                            }
                            return json_data
                    except json.JSONDecodeError:
                        pass
                
                # Convert text response to unified format based on state
                if state == "input_required":
                    return {
                        "status": "input_required",
                        "data": {
                            "specific_need": "Additional information needed for analysis",
                            "suggested_context": "Please provide more details about your background",
                            "why_needed": "Insufficient context for meaningful guidance"
                        },
                        "analysis": {
                            "reasoning": "AI determined more user context is needed",
                            "confidence_score": 0.2,
                            "criteria_used": ["information_sufficiency"],
                            "strengths": ["User engagement"],
                            "weaknesses": ["Limited context provided"],
                            "market_context": "Ready to analyze with additional information"
                        },
                        "_metadata": {
                            "sessionId": self.current_session_id,
                            "process_sequence": process_sequence,
                            "timestamp": start_time.isoformat(),
                            "processing_time": processing_time
                        }
                    }
                elif state == "failed":
                    return {
                        "status": "failed",
                        "data": {
                            "error_type": "PROCESSING_ERROR",
                            "error_message": "Processing failed during career analysis",
                            "fallback_guidance": "Please try again or rephrase your question",
                            "suggested_action": "Retry with more specific career question"
                        },
                        "analysis": {
                            "reasoning": "AI processing encountered an error",
                            "confidence_score": 0.0,
                            "criteria_used": ["error_handling"],
                            "strengths": [],
                            "weaknesses": ["Processing failure"],
                            "market_context": "Unable to complete analysis"
                        },
                        "_metadata": {
                            "sessionId": self.current_session_id,
                            "process_sequence": process_sequence,
                            "timestamp": start_time.isoformat(),
                            "processing_time": processing_time
                        }
                    }
                else:
                    # Default completed - convert text to structured format
                    return {
                        "status": "completed",
                        "data": {
                            "profile_assessment": {
                                "inferred_background": "Based on query context",
                                "experience_level": "general",
                                "key_strengths": ["career inquiry"]
                            },
                            "career_recommendations": [{
                                "role": "General Career Guidance",
                                "match_confidence": 0.7,
                                "reasoning": "Provided guidance based on available context",
                                "growth_potential": "varies"
                            }],
                            "market_intelligence": {
                                "job_opportunities": "varies by field",
                                "salary_insights": {"range": "depends on specialization"},
                                "demand_trend": "stable",
                                "entry_barriers": "varies"
                            },
                            "skills_development": {
                                "current_strengths": ["career awareness"],
                                "priority_skills": [],
                                "learning_path": "Based on AI recommendations"
                            },
                            "next_steps": ["Follow AI recommendations", "Consider specific areas"]
                        },
                        "analysis": {
                            "reasoning": "Provided general career guidance based on available context",
                            "confidence_score": 0.7,
                            "criteria_used": ["general_guidance", "context_inference"],
                            "strengths": ["Career awareness", "Seeking guidance"],
                            "weaknesses": ["Limited specific context"],
                            "market_context": "General career market considerations"
                        },
                        "_metadata": {
                            "sessionId": self.current_session_id,
                            "process_sequence": process_sequence,
                            "timestamp": start_time.isoformat(),
                            "processing_time": processing_time,
                            "fallback_conversion": True,
                            "original_response": final_response[:500]  # Truncate for brevity
                        }
                    }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "status": "failed",
                "data": {
                    "error_type": "SYSTEM_ERROR",
                    "error_message": f"System error: {str(e)}",
                    "fallback_guidance": "Please try again or contact support",
                    "suggested_action": "Retry the request or report the issue"
                },
                "analysis": {
                    "reasoning": f"Unexpected system error: {str(e)}",
                    "confidence_score": 0.0,
                    "criteria_used": ["error_handling"],
                    "strengths": [],
                    "weaknesses": ["System error"],
                    "market_context": "Unable to access career analysis system"
                },
                "_metadata": {
                    "sessionId": getattr(self, 'current_session_id', None),
                    "process_sequence": [],
                    "timestamp": start_time.isoformat(),
                    "processing_time": processing_time,
                    "error_details": str(e)
                }
            }
    
    def _process_with_ai(self, user_query: str, original_messages: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process the user query with AI career counseling - AI decides what context it needs."""
        print("\n[AI_PROCESSING] Starting AI processing...")
        print(f"[AI_INPUT] User query length: {len(user_query)} chars")
        print(f"[AI_TOOLS] Available tools: {[tool.__name__ if callable(tool) else str(tool) for tool in self.available_tools]}")
        print(f"[AI_HISTORY] Conversation history: {len(self.conversation_history)} messages")
        print(f"[AI_METADATA] Metadata keys: {list((metadata or {}).keys())}")
        
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
            
            # Prepare context information for AI (but don't force it)
            context_info = []
            if original_messages and len(original_messages) > 1:
                context_info.append(f"Previous messages context: {len(original_messages)} messages available")
            
            if metadata:
                context_info.append(f"Available metadata: {list(metadata.keys())}")
            
            # Create user message with optional context hints
            user_message = user_query
            if context_info:
                user_message += f"\n\n[Optional Context Available: {', '.join(context_info)}]"
            
            # Add current user query
            conversation_history.append(
                types.Content(role="user", parts=[types.Part(text=user_message)])
            )
            
            print(f"[AI_CONVERSATION] Conversation parts for AI: {len(conversation_history)} parts")
            
            # Configure AI generation - remove JSON mime type to allow function calling
            print(f"[AI_CONFIG] Configuring AI generation settings...")
            config = types.GenerateContentConfig(
                system_instruction=self.full_instruction,
                tools=self.available_tools,
                tool_config={'function_calling_config': {'mode': 'AUTO'}},
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
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
            
            print(f"[AI_REQUEST] Sending request to Gemini AI...")
            print(f"[AI_MODEL] Using model: gemini-2.5-flash")
            print(f"[AI_TOOLS_CONFIG] Function calling mode: AUTO")
            
            # Single attempt - AI decides whether to use response_to_agent tool or respond normally
            print(f"\n[AI_PROCESSING] Starting AI generation...")
            start_time = datetime.now()
            
            # Generate response with API key rotation
            try:
                response = self._safe_api_call(
                    self.client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=conversation_history,
                    config=config
                )
            except Exception as api_error:
                print(f"[AI_API_ERROR] API call failed after retries: {api_error}")
                raise api_error
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            print(f"[AI_RESPONSE_TIME] AI response time: {processing_time:.2f} seconds")
            
            # Process AI response parts
            tool_history = getattr(self, '_current_tool_history', [])
            used_response_tool = False
            tool_response = None
            final_text = ""
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                parts = response.candidates[0].content.parts
                
                # Process all parts in this response
                for part in parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name
                        
                        # If response_to_agent is called, execute it
                        if func_name == 'response_to_agent':
                            try:
                                args = dict(part.function_call.args) if part.function_call.args else {}
                                tool_response = self.response_to_agent_tool(**args)
                                used_response_tool = True
                                
                                # Add to tool history
                                tool_history.append({
                                    "type": "function_call",
                                    "name": func_name,
                                    "args": args,
                                    "timestamp": datetime.now().isoformat()
                                })
                                
                                print(f"[TOOL_SUCCESS] response_to_agent tool was used")
                                break  # Exit part loop
                            except Exception as e:
                                print(f"[ERROR] Error executing response_to_agent: {e}")
                        
                        # Log other tool calls for history (no outputs, just calls)
                        elif func_name in ['query_database', 'get_similar_jobs_by_embedding']:
                            args = dict(part.function_call.args) if part.function_call.args else {}
                            tool_history.append({
                                "type": "function_call",
                                "name": func_name,
                                "args": args,
                                "timestamp": datetime.now().isoformat()
                            })
                                    
                    elif hasattr(part, 'function_response') and part.function_response:
                        # Skip logging function responses to keep history light
                        pass
                            
                    elif hasattr(part, 'text') and part.text:
                        final_text += part.text
                        # Skip logging AI text to keep history light
            
            # Store tool history for this session
            self._current_tool_history = tool_history
            
            # Return result based on whether response_to_agent was used
            if used_response_tool and tool_response:
                print(f"[FINAL_SUCCESS] response_to_agent tool was successfully called")
                return {
                    "success": True,
                    "used_response_tool": True,
                    "tool_response": tool_response,
                    "final_response": str(tool_response),  # Convert to string for compatibility
                    "state": tool_response.get('status', 'completed'),  # Use 'status' from new format
                    "tool_history": getattr(self, '_current_tool_history', [])
                }
            
            # Normal processing - AI responded with text (this is now acceptable)
            if not final_text.strip():
                final_text = response.text if hasattr(response, 'text') else "No response generated"
            
            print(f"[AI_TEXT_RESPONSE] AI provided text response without using response_to_agent tool")
            print(f"[RESPONSE_LENGTH] {len(final_text)} characters")
            
            # Try to parse JSON response from text if it looks like structured data
            try:
                import json
                import re
                
                # Try to extract JSON from text response
                json_match = re.search(r'\{[\s\S]*\}', final_text)
                if json_match:
                    json_text = json_match.group(0)
                    json_response = json.loads(json_text)
                    
                    # Extract status from JSON
                    status = json_response.get('status', 'completed')
                    
                    print(f"[JSON_DETECTED] Found JSON response with status: {status}")
                    
                    # Map JSON status to our state format
                    if status == 'input_required':
                        state = "input_required"
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
                        "used_response_tool": False,
                        "state": state,
                        "final_response": json_text,  # Return the JSON part
                        "process_sequence": [{
                            "type": response_type,
                            "content": json_text,
                            "timestamp": datetime.now().isoformat(),
                            "asks_for_info": asks_for_info,
                            "json_parsed": True
                        }],
                        "tool_history": getattr(self, '_current_tool_history', [])
                    }
                
            except (json.JSONDecodeError, AttributeError):
                # If JSON extraction/parsing fails, treat as regular text response
                print(f"[TEXT_RESPONSE] AI provided regular text response (not JSON)")
                pass
            
            # Handle regular text responses - this is now normal behavior
            # AI can respond with text and only use response_to_agent when ready with final result
            final_text_lower = final_text.lower()
            
            # Intelligent state detection from response content
            if any(phrase in final_text_lower for phrase in ['need more information', 'could you tell me', 'what is your', 'need to know']):
                state = "input_required"
                response_type = "information_request"
                asks_for_info = True
            elif any(phrase in final_text_lower for phrase in ['error', 'failed', 'unable to', 'cannot process']):
                state = "failed"
                response_type = "error"
                asks_for_info = False
            else:
                # Default to completed - treat normal response as career advice
                state = "completed"
                response_type = "career_advice"
                asks_for_info = False
            
            print(f"[TEXT_STATE] Determined state from text content: {state}")
            
            return {
                "success": True,
                "used_response_tool": False,
                "state": state,
                "final_response": final_text,
                "process_sequence": [{
                    "type": response_type,
                    "content": final_text,
                    "timestamp": datetime.now().isoformat(),
                    "asks_for_info": asks_for_info,
                    "json_parsed": False
                }],
                "tool_history": getattr(self, '_current_tool_history', [])
            }
                
        except Exception as e:
            print(f"[ERROR] AI processing error: {e}")
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
            print(f"[WARNING] Could not load session history: {e}")
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
            print(f"[WARNING] Could not save conversation: {e}")
    
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
    AI Career Advisor Agent for external agent-to-agent communication.

    - On the first call, do NOT send a sessionId (leave it as None or omit).
    - On subsequent calls, you MUST send the sessionId from the previous response's _metadata.sessionId (when the response_to_agent tool was used).

    Provides intelligent career counseling with minimal information requirements:
    - Skills analysis and development recommendations  
    - Career path guidance and job market insights
    - Professional growth strategies and learning roadmaps
    - Market intelligence and salary analysis

    INTELLIGENT PROCESSING:
    - Works with minimal user information through smart inference
    - Leverages database intelligence for market analysis
    - Uses logical reasoning to fill information gaps
    - Only requests additional input when analysis is truly impossible

    INPUT FORMAT (Agent-to-Agent):
    {
        "sessionId": str | None,        # Omit or set to None on FIRST call, REQUIRED for subsequent calls (use _metadata.sessionId from previous response)
        "message": List[Dict],          # Conversation messages [{"role": "user", "content": "query"}]
        "metadata": Dict                # Additional context (optional: images, urls, etc.)
    }

    OUTPUT FORMAT (Unified Response Structure):
    When response_to_agent tool is used (recommended):
    {
        "status": str,                  # "completed" | "failed" | "input_required"
        "data": {                       # Content varies by status
            "profile_assessment": {},    # Inferred user background and strengths
            "career_recommendations": [], # Matched career paths with confidence
            "market_intelligence": {},   # Job opportunities and salary insights
            "skills_development": {},    # Priority skills and learning paths
            "next_steps": []            # Actionable recommendations
        },
        "analysis": {                   # Required analysis section
            "reasoning": str,           # Why this recommendation was made
            "confidence_score": float,  # 0.0 to 1.0 confidence level
            "criteria_used": [],        # Analysis criteria applied
            "strengths": [],           # User's identified strengths
            "weaknesses": [],          # Areas for improvement
            "market_context": str      # Current market trends and positioning
        },
        "_metadata": {                  # Optional processing metadata
            "sessionId": str,          # Session tracking
            "process_sequence": [],    # Tool usage history
            "timestamp": str           # Processing timestamp
        }
    }

    Fallback FORMAT (when tool not used):
    {
        "start_time": str,              # Processing start timestamp (ISO format)
        "end_time": str,                # Processing end timestamp (ISO format)  
        "sessionId": str,               # Session ID for conversation tracking
        "state": str,                   # "completed" | "failed" | "input_required" 
        "process_sequence": List,       # Processing steps and tool usage log
        "final_response": str,          # JSON string with career guidance
        "metadata": Dict               # Processing metadata and tool history
    }

    RESPONSE STRUCTURE:
    The function returns the unified format from response_to_agent tool:
    - status: Processing state ("completed", "failed", "input_required")
    - data: Career analysis results (profile, recommendations, market data, skills)
    - analysis: Intelligence reasoning with confidence scores and market context
    - _metadata: Optional processing information and session tracking

    LEGACY SUPPORT:
    If response_to_agent tool is not used, returns fallback format with:
    - Standardized task response structure for compatibility
    - final_response as JSON string containing the unified format data

    CORE CAPABILITIES:
    - Career path recommendations based on minimal user context
    - Skills gap analysis with learning priorities and timelines
    - Job market intelligence (demand, salary, opportunities)
    - Professional development roadmaps with actionable steps
    - Industry insights and career transition guidance

    Args:
        task: Input task dictionary with message and optional metadata.
              On the first call, do NOT send sessionId. On subsequent calls, use sessionId from previous response's _metadata.sessionId.

    Returns:
        Unified career guidance response in the new format when response_to_agent
        tool is used, or fallback compatibility format for legacy integration.
        Contains intelligent career recommendations, market analysis, and 
        actionable development guidance.
    """
    try:
        # Initialize agent
        agent = UnifiedCareerAdvisor()
        
        # Process with unified agent using exact format
        result = agent.process_career_task(task)
        
        return result
        
    except Exception as e:
        # Return unified error format
        return {
            "status": "failed",
            "data": {
                "error_type": "SYSTEM_ERROR",
                "error_message": f"Career advice system error: {str(e)}",
                "fallback_guidance": "Please try again or contact support for assistance",
                "suggested_action": "Retry the request or provide more context"
            },
            "analysis": {
                "reasoning": f"System error prevented career analysis: {str(e)}",
                "confidence_score": 0.0,
                "criteria_used": ["error_handling"],
                "strengths": [],
                "weaknesses": ["System unavailable"],
                "market_context": "Unable to access career guidance system"
            },
            "_metadata": {
                "sessionId": task.get("sessionId", "error_session"),
                "timestamp": datetime.now().isoformat(),
                "error_details": str(e),
                "agent_type": "unified_career_advisor"
            }
        }
