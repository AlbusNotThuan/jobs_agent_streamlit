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
    
    def __init__(self, conversations_dir: str = "conversations"):
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
            self._response_to_agent_called = False  # Track if response_to_agent was called

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
            def response_to_agent(final_response: str) -> str:
                """
                Tool for AI to provide final response to the user.
                
                Call this tool when you have completed your analysis and are ready to provide
                the final career guidance response. Pass the complete final response as the
                final_response parameter.
                
                Args:
                    final_response (str): The complete final response to be returned to the user.
                                        Should be in structured JSON format as specified in instructions.
                
                Returns:
                    Confirmation that response has been captured
                """
                print(f"[TOOL_CALL] response_to_agent invoked with final response")
                print(f"[FINAL_RESPONSE_LENGTH] {len(final_response)} characters")
                
                # Set flag to indicate response_to_agent was called and store the response
                self._response_to_agent_called = True
                self._final_response_text = final_response
                
                return f"Final response captured ({len(final_response)} characters). Processing complete."
            
            
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

    def _get_tool_result_summary(self, func_name: str, tool_result: Any) -> str:
        """
        Create a summary of tool result for logging without storing full data.
        
        Args:
            func_name: Name of the tool function
            tool_result: The result returned by the tool
            
        Returns:
            A brief summary string describing the result
        """
        try:
            if func_name == "query_database":
                if isinstance(tool_result, list):
                    return f"Database query returned {len(tool_result)} rows"
                else:
                    return f"Database query completed"
                    
            elif func_name == "get_similar_jobs_by_embedding":
                if isinstance(tool_result, list):
                    job_count = len(tool_result)
                    if job_count > 0:
                        # Get top similarity score if available
                        try:
                            first_job = tool_result[0]
                            if isinstance(first_job, dict) and 'similarity_score' in first_job:
                                top_score = first_job['similarity_score']
                                return f"Found {job_count} similar jobs (top similarity: {top_score:.3f})"
                            else:
                                return f"Found {job_count} similar jobs"
                        except:
                            return f"Found {job_count} similar jobs"
                    else:
                        return "No similar jobs found"
                else:
                    return "Job similarity search completed"
                    
            elif func_name == "response_to_agent":
                return "Final response prepared"
                
            else:
                # Generic summary for unknown tools
                if isinstance(tool_result, (list, tuple)):
                    return f"Tool returned {len(tool_result)} items"
                elif isinstance(tool_result, dict):
                    return f"Tool returned dictionary with {len(tool_result)} keys"
                elif isinstance(tool_result, str):
                    length = len(tool_result)
                    if length > 1000:
                        return f"Tool returned long text ({length} chars)"
                    else:
                        return f"Tool returned text ({length} chars)"
                else:
                    return f"Tool returned: {type(tool_result).__name__}"
                    
        except Exception as e:
            return f"Tool executed (summary error: {str(e)[:50]})"

    
    
    def process_career_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to process career counseling tasks.
        
        This is the unified entry point that handles the standardized input/output format.
        
        Args:
            task: Input task with sessionId, message, and metadata
            
        Returns:
            Standardized output task with career guidance (only when response_to_agent tool is used)
        """
        start_time = datetime.now()
        self._task_start_time = start_time  # Store for response_to_agent tool
        self._current_tool_history = []  # Reset tool history for new task
        self._response_to_agent_called = False  # Reset flag for new task
        
        print(f"\n[PROCESS_CAREER_TASK] Starting at {start_time.isoformat()}")
        print(f"[INPUT_VALIDATION] Received task with keys: {list(task.keys())}")
        
        try:
            # Validate input
            print(f"[STEP_1] Input validation...")
            validation = self.task_handler.validate_input_task(task)
            print(f"[VALIDATION_RESULT] Valid: {validation['valid']}")
            if not validation['valid']:
                print(f"[VALIDATION_ERRORS] {validation['errors']}")
                return self.task_handler.create_failed_task(
                    start_time=start_time,
                    reason=f"Invalid input: {'; '.join(validation['errors'])}",
                    metadata={"validation_errors": validation['errors']}
                )
            
            # Extract components
            print(f"[STEP_2] Extracting task components...")
            session_id = task.get('sessionId')
            messages = task['message']
            metadata = task.get('metadata', {})
            print(f"[COMPONENTS] SessionId: {session_id}, Messages: {len(messages)}, Metadata keys: {list(metadata.keys())}")
            
            # Session management
            print(f"[STEP_3] Session management...")
            if session_id:
                print(f"[SESSION_CHECK] Checking if session '{session_id}' exists...")
                if not self.task_handler.check_session_exists(session_id):
                    print(f"[SESSION_ERROR] Session '{session_id}' not found")
                    return self.task_handler.create_failed_task(
                        start_time=start_time,
                        reason=f"Session '{session_id}' not found",
                        session_id=session_id
                    )
                print(f"[SESSION_FOUND] Loading existing session '{session_id}'")
                self.current_session_id = session_id
                # Load conversation history if needed
                print(f"[SESSION_LOAD] Loading conversation history...")
                self._load_session_history(session_id)
                print(f"[SESSION_HISTORY] Loaded {len(self.conversation_history)} previous messages")
            else:
                # Create new session
                new_session = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"[SESSION_CREATE] Creating new session: {new_session}")
                self.current_session_id = new_session
                self.conversation_history = []
            
            # Extract user query
            print(f"[STEP_4] Extracting user query from messages...")
            user_query = self.task_handler.extract_user_query(messages)
            print(f"[USER_QUERY] Length: {len(user_query)} chars, Content: '{user_query[:100]}{'...' if len(user_query) > 100 else ''}'")
            if not user_query.strip():
                print(f"[ERROR] Empty user query detected")
                return self.task_handler.create_failed_task(
                    start_time=start_time,
                    reason="No user query found",
                    session_id=self.current_session_id
                )
            
            # Direct processing - let AI decide what context it needs
            print(f"[STEP_5] Processing with AI (no pre-enhancement)...")
            result = self._process_with_ai(user_query, messages, metadata)
            print(f"[AI_RESULT] Success: {result.get('success')}, Used response tool: {result.get('used_response_tool')}")
            
            # Save conversation
            print(f"[STEP_7] Saving conversation history...")
            self._save_conversation_history(messages, result.get('final_response', ''))
            print(f"[CONVERSATION_SAVED] Total messages in history: {len(self.conversation_history)}")
            
            # Check if response_to_agent tool was used
            print(f"[STEP_8] Checking tool usage...")
            if result.get('used_response_tool', False):
                print(f"[TOOL_SUCCESS] response_to_agent tool was used - creating standardized response")
                
                # Use the captured final response text as the main content
                final_response = result.get('final_response', '')
                state = result.get('state', 'completed')
                
                # Create standardized output using task handler
                end_time = datetime.now()
                
                return self.task_handler.create_output_task(
                    start_time=start_time,
                    end_time=end_time,
                    session_id=self.current_session_id,
                    state=state,
                    process_sequence=result.get('tool_history', []),
                    final_response=final_response,
                    metadata={
                        "agent_type": "unified_career_advisor",
                        "enhanced_processing": True,
                        "session_id": self.current_session_id,
                        "attempts_taken": result.get('attempts_taken', 1),
                        "execution_time_seconds": (end_time - start_time).total_seconds()
                    }
                )
            else:
                print(f"[FALLBACK] response_to_agent tool was NOT used - using fallback logic")
                # Fallback - create output (should not happen if AI follows instructions)
                end_time = datetime.now()
                
                if result.get('success', False):
                    state = result.get('state', 'completed')
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
                        "agent_type": "unified_career_advisor",
                        "enhanced_processing": True,
                        "session_id": self.current_session_id,
                        "fallback_response": True,  # Indicates AI didn't use response_to_agent tool
                        "asks_for_info": result.get('process_sequence', [{}])[0].get('asks_for_info', False),
                        "execution_time_seconds": (end_time - start_time).total_seconds()
                    }
                )
            
        except Exception as e:
            return self.task_handler.create_failed_task(
                start_time=start_time,
                reason=f"Processing error: {str(e)}",
                session_id=getattr(self, 'current_session_id', None),
                metadata={"error_details": str(e)}
            )
    
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
            for msg in self.conversation_history:  # Last 5 messages for context
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
            
            # Reset flag for this processing
            self._response_to_agent_called = False
            
            # Retry loop for AI processing until response_to_agent tool is called
            max_attempts = 5
            attempt = 0
            final_response_text = None
            
            while attempt < max_attempts and not self._response_to_agent_called:
                attempt += 1
                print(f"\n[AI_ATTEMPT_{attempt}] Starting AI generation attempt {attempt}/{max_attempts}")
                start_time = datetime.now()
                #print conversation history
                print(f"[AI_CONVERSATION_HISTORY] {conversation_history}")
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
                    # If it's a non-retryable error or all keys failed, break the attempt loop
                    if '400' in str(api_error).lower():
                        print(f"[AI_ERROR] 400 error - stopping all attempts")
                        raise api_error
                    else:
                        # For other errors, continue to next attempt if available
                        continue
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                print(f"[AI_RESPONSE_TIME] AI response time: {processing_time:.2f} seconds")
                
                # Process AI response parts
                tool_history = getattr(self, '_current_tool_history', [])
                
                # Safely access response candidates
                candidate = None
                has_function_call = False
                
                try:
                    print(f"[DEBUG] Response type: {type(response)}")
                    print(f"[DEBUG] Has candidates attr: {hasattr(response, 'candidates')}")
                    
                    if hasattr(response, 'candidates'):
                        print(f"[DEBUG] Candidates type: {type(response.candidates)}")
                        print(f"[DEBUG] Candidates value: {response.candidates}")
                        
                        if response.candidates and len(response.candidates) > 0:
                            candidate = response.candidates[0]
                            print(f"[DEBUG] Successfully got candidate")
                        else:
                            print(f"[AI_RESPONSE_WARNING] No candidates found in response")
                            candidate = None
                    else:
                        print(f"[AI_RESPONSE_WARNING] Response has no candidates attribute")
                        print(f"[AI_RESPONSE_DEBUG] Response type: {type(response)}")
                        print(f"[AI_RESPONSE_DEBUG] Response attributes: {dir(response)}")
                        candidate = None
                except Exception as e:
                    print(f"[AI_RESPONSE_ERROR] Error accessing response candidates: {e}")

                    candidate = None
                
                if candidate and candidate.content and candidate.content.parts:
                    parts = candidate.content.parts
                    
                    # First, add the model's response (including thoughts/reasoning) to conversation history
                    conversation_history.append(candidate.content)
                    
                    # Check for function calls first (following the reference pattern)
                    for part in parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            has_function_call = True
                            function_call = part.function_call
                            func_name = function_call.name
                            args = dict(function_call.args) if function_call.args else {}
                            
                            print(f"[FUNCTION_CALL] Detected function call: {func_name}")
                            print(f"[FUNCTION_CALL_ARGS] Arguments: {args}")
                            
                            # Add simplified tool history (no full args)
                            tool_history.append({
                                "type": "function_call",
                                "name": func_name,
                                "args_summary": f"{len(args)} arguments" if args else "no arguments",
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Execute tool and add response to conversation
                            if func_name == 'response_to_agent':
                                try:
                                    confirmation = self.response_to_agent_tool(**args)
                                    print(f"[RESPONSE_TO_AGENT] Tool executed: {confirmation}")
                                    # Don't add function response for response_to_agent - it's just a trigger
                                except Exception as e:
                                    print(f"[ERROR] Error executing response_to_agent: {e}")
                            
                            elif func_name in self.tool_functions:
                                try:
                                    # Execute the tool
                                    tool_function = self.tool_functions[func_name]
                                    tool_result = tool_function(**args)
                                    
                                    # Determine result summary based on tool type
                                    result_summary = self._get_tool_result_summary(func_name, tool_result)
                                    
                                    print(f"[TOOL_RESULT] {func_name} executed successfully - {result_summary}")
                                    
                                    # Add simplified tool result to history (no full result data)
                                    tool_history.append({
                                        "type": "function_response",
                                        "name": func_name,
                                        "result_summary": result_summary,
                                        "success": True,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    # Add tool response to conversation history (AI still gets full result)
                                    conversation_history.append(
                                        types.Content(
                                            role="model",
                                            parts=[
                                                types.Part(
                                                    function_response=types.FunctionResponse(
                                                        name=func_name,
                                                        response={'result': str(tool_result)}
                                                    )
                                                )
                                            ]
                                        )
                                    )
                                    
                                except Exception as e:
                                    error_message = f"Error executing {func_name}: {str(e)}"
                                    print(f"[TOOL_ERROR] {error_message}")
                                    
                                    # Add simplified tool error to history
                                    tool_history.append({
                                        "type": "function_response",
                                        "name": func_name,
                                        "result_summary": f"Tool failed: {str(e)[:100]}",
                                        "success": False,
                                        "error_type": type(e).__name__,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    # Add error response to conversation history
                                    conversation_history.append(
                                        types.Content(
                                            role="model", 
                                            parts=[
                                                types.Part(
                                                    function_response=types.FunctionResponse(
                                                        name=func_name,
                                                        response={'error': error_message}
                                                    )
                                                )
                                            ]
                                        )
                                    )
                            break  # Only handle one function call per iteration
                    
                    # Process other parts (thoughts and text)
                    for part in parts:
                        if hasattr(part, 'thought') and part.thought:
                            # Handle thinking parts - truncate for logging
                            thought_content = part.text if hasattr(part, 'text') else str(part.thought)
                            truncated_thought = (thought_content or '')[:500] + ('...' if len(thought_content or '') > 500 else '')
                            print(f"[AI_THOUGHT] Detected thinking: {truncated_thought}")
                            tool_history.append({
                                "type": "ai_thinking",
                                "content": truncated_thought,
                                "timestamp": datetime.now().isoformat()
                            })
                        
                        elif hasattr(part, 'text') and part.text and not hasattr(part, 'function_call'):
                            text_content = part.text
                            if self._response_to_agent_called:
                                # This is the final response text after response_to_agent was called
                                final_response_text = text_content
                                print(f"[FINAL_RESPONSE_CAPTURED] Length: {len(text_content or '')} chars")
                                print(f"[FINAL_RESPONSE_PREVIEW] {(text_content or '')[:200]}...")
                            else:
                                # Add reasoning text to history - truncate long content
                                truncated_text = (text_content or '')[:500] + ('...' if len(text_content or '') > 500 else '')
                                tool_history.append({
                                    "type": "ai_reasoning",
                                    "content": truncated_text,
                                    "timestamp": datetime.now().isoformat()
                                })
                    
                    # If we have a function call, continue the loop for next iteration
                    if has_function_call:
                        # Don't break the loop here - let it check _response_to_agent_called in the main condition
                        pass
                
                # Store tool history for this session
                self._current_tool_history = tool_history
                
                # If response_to_agent was called, we should have the final text
                if self._response_to_agent_called:
                    # Get final response from the tool parameter instead of text response
                    if hasattr(self, '_final_response_text') and self._final_response_text:
                        final_response_text = self._final_response_text
                        print(f"[FINAL_SUCCESS] response_to_agent tool called with final response after {attempt} attempts")
                        break
                    else:
                        # Fallback if somehow the final response wasn't captured
                        final_response_text = "No final response captured from response_to_agent tool"
                        print(f"[FINAL_WARNING] response_to_agent tool called but no final response captured")
                        break
                else:
                    print(f"[ATTEMPT_{attempt}_RESULT] response_to_agent tool NOT called - continuing...")
                    if attempt < max_attempts:
                        # If there were function calls, they were already added to conversation_history
                        # If there were no function calls, add a prompt to continue
                        if not has_function_call:
                            conversation_history.append(
                                types.Content(
                                    role="user", 
                                    parts=[types.Part(text="Continue with analysis using available tools and call response_to_agent tool when ready with final answer.")]
                                )
                            )
                        print(f"[RETRY_PREP] Prepared for attempt {attempt + 1} with updated conversation history")
                    else:
                        print(f"[MAX_ATTEMPTS_REACHED] Reached maximum {max_attempts} attempts without response_to_agent tool")
            
            # Return result based on whether response_to_agent was used
            if self._response_to_agent_called and final_response_text:
                print(f"[SUCCESS] response_to_agent tool was successfully used after {attempt} attempts")
                
                # Try to determine state from final response text
                state = "completed"
                try:
                    # Try to extract JSON from text response
                    json_match = re.search(r'\{[\s\S]*\}', final_response_text)
                    if json_match:
                        json_text = json_match.group(0)
                        json_response = json.loads(json_text)
                        
                        # Extract state from JSON
                        status = json_response.get('status', 'completed')
                        
                        # Map JSON status to our state format
                        if status == 'input_required':
                            state = "input_required"
                        elif status == 'failed':
                            state = "failed"
                        else:
                            state = "completed"
                except:
                    # If JSON parsing fails, keep default state
                    pass
                
                return {
                    "success": True,
                    "used_response_tool": True,
                    "final_response": final_response_text,
                    "state": state,
                    "attempts_taken": attempt,
                    "tool_history": getattr(self, '_current_tool_history', [])
                }
            
            # Fallback processing if response_to_agent tool wasn't used after all attempts
            final_text = response.text if 'response' in locals() else "No response generated"
            print(f"[FALLBACK_WARNING] response_to_agent tool was NOT used after {attempt} attempts")
            print(f"[FALLBACK_REASON] AI may need more context or different instruction approach")
            
            # Try to parse JSON response from text (fallback)
            try:
                if final_text:  # Check if final_text is not None
                    # Try to extract JSON from text response
                    json_match = re.search(r'\{[\s\S]*\}', final_text)
                    if json_match:
                        json_text = json_match.group(0)
                        json_response = json.loads(json_text)
                    
                    # Extract state from JSON
                    status = json_response.get('status', 'completed')
                    
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
                # If JSON extraction/parsing fails, continue with fallback
                pass
            
            # Final fallback - if AI didn't use response_to_agent tool as instructed
            # This should rarely happen if system instruction is followed
            final_text_lower = (final_text or '').lower()
            
            # Let AI model determine state naturally from its response content
            # No hard-coded keywords - rely on AI's structured JSON response
            if 'input_required' in final_text_lower or 'input_required' in final_text_lower:
                state = "input_required"
                response_type = "information_request"
                asks_for_info = True
            elif 'failed' in final_text_lower or 'error' in final_text_lower:
                state = "failed"
                response_type = "error"
                asks_for_info = False
            else:
                # Default to completed - AI should have provided complete response
                state = "completed"
                response_type = "career_advice"
                asks_for_info = False
            
            # Log fallback usage (should not happen often)
            print(f"   [FALLBACK_STATE] Determined state from content: {state}")
            print(f"   [FALLBACK_NOTE] AI should use response_to_agent tool instead")
            
            return {
                "success": True,
                "used_response_tool": False,
                "state": state,
                "final_response": final_text or "No response generated",
                "process_sequence": [{
                    "type": response_type,
                    "content": final_text or "No response generated",
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
        "sessionId": str | None,        # Optional on FIRST call, REQUIRED for subsequent calls for conversation continuity
        "message": List[Dict],          # Conversation messages [{"role": "user", "content": "query"}]
        "metadata": Dict                # Additional context (optional: images, urls, etc.)
    }

    OUTPUT FORMAT (Standardized):
    {
        "start_time": str,              # Processing start timestamp (ISO format)
        "end_time": str,                # Processing end timestamp (ISO format)  
        "sessionId": str,               # Session ID for conversation tracking
        "state": str,                   # "completed" | "failed" | "input_required" 
        "process_sequence": List,       # Processing steps and tool usage log
        "final_response": str,          # Structured JSON response with career guidance
        "metadata": {                   # Processing metadata
            "tool_history": List[Dict], # Complete tool execution history
            "agent_type": str,          # "unified_career_advisor"
            "reasoning_process": List   # AI reasoning and inference steps
        }
    }

    RESPONSE CONTENT STRUCTURE:
    The final_response contains JSON with:
    - status: "completed|failed|input_required"
    - data: Career recommendations, market intelligence, skills analysis
    - analysis: Reasoning, confidence scores, strengths/weaknesses assessment

    CORE CAPABILITIES:
    - Career path recommendations based on minimal user context
    - Skills gap analysis with learning priorities and timelines
    - Job market intelligence (demand, salary, opportunities)
    - Professional development roadmaps with actionable steps
    - Industry insights and career transition guidance

    Args:
        task: Input task dictionary with message and optional metadata.
              No strict format requirements - works with basic user information.

    Returns:
        Structured career guidance response for agent consumption with complete
        processing metadata and intelligent recommendations.
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
