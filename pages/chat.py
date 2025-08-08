# -*- coding: utf-8 -*-
"""
Chat Page for Skills Analyzer Chatbot
Streamlit page for the AI-powered chatbot with integrated analysis tools
"""

import streamlit as st
import os
import sys
import pandas as pd
import ast
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the chatbot class
try:
    from chatbot_class.skills_analyzer_chatbot import SkillsAnalyzerChatbot
    CHATBOT_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Could not import chatbot: {e}")
    CHATBOT_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Chat - SkillAI",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def main():
    """Main chat interface function."""
    st.title("💬 AI Skills Analyzer")
    
    if not CHATBOT_AVAILABLE:
        st.error("❌ Chatbot is not available due to import errors. Please check the configuration.")
        return
    
    # Initialize chatbot in session state
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = SkillsAnalyzerChatbot(verbose=False)
            st.session_state.messages = []
        except Exception as e:
            st.error(f"❌ Failed to initialize chatbot: {e}")
            return
    
    # Simple sidebar with minimal controls
    with st.sidebar:
        st.header("💬 Chat Controls")
        
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.chatbot.new_chat()
            st.session_state.messages = []
            st.rerun()
        
        if st.button("💾 Save Chat", use_container_width=True):
            if st.session_state.chatbot.save_conversation():
                st.success("✅ Chat saved!")
            else:
                st.error("❌ Failed to save chat")
        
        # Toggle for showing thought process
        show_process = st.checkbox("🧠 Show Thought Process", value=False)
        st.session_state.show_process = show_process
        
        # Display session stats
        stats = st.session_state.chatbot.get_session_stats()
        st.info(f"Session: {stats['session_id'][:8]}...\nMessages: {stats['total_messages']}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display charts if available in message metadata
            if "metadata" in message and "charts" in message["metadata"]:
                for chart_data in message["metadata"]["charts"]:
                    _display_streamlit_chart(chart_data)
    
    # Chat input
    if prompt := st.chat_input("Ask me about skills, jobs, or career advice..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chatbot.chat(prompt)
                    
                    if response.get("success", False):
                        bot_message = response.get("final_response", "No response generated.")
                        st.markdown(bot_message)
                        
                        # Check for charts in the process sequence and display them
                        charts_found = _check_and_display_charts(response.get("process_sequence", []))
                        
                        # Show process steps if enabled
                        if st.session_state.get("show_process", False) and response.get("process_sequence"):
                            with st.expander("🔍 AI Thought Process", expanded=False):
                                _display_process_sequence(response.get("process_sequence", []))
                        
                        # Add bot response to chat history with metadata
                        message_metadata = {}
                        if charts_found:
                            message_metadata["charts"] = charts_found
                            
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": bot_message,
                            "metadata": message_metadata
                        })
                        
                    else:
                        error_msg = response.get("final_response", "An error occurred.")
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


def _check_and_display_charts(process_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check for chart data in the process sequence and display charts.
    
    Args:
        process_sequence: List of process steps from chatbot
        
    Returns:
        List of chart data found for storage in message metadata
    """
    charts_found = []
    
    try:
        for step in process_sequence:
            if step.get("type") == "tool_result" and step.get("success", False):
                result_str = step.get("result", "")
                
                # Try to parse the result if it's a string
                result = None
                if isinstance(result_str, str):
                    try:
                        result = ast.literal_eval(result_str)
                    except (ValueError, SyntaxError):
                        continue  # Skip if parsing fails
                else:
                    result = result_str
                
                # Check if result contains chart data
                if (isinstance(result, dict) and 
                    result.get("chart_data") is not None and 
                    result.get("chart_type") is not None):
                    
                    _display_streamlit_chart(result)
                    charts_found.append(result)
                    
    except Exception as e:
        st.warning(f"⚠️ Error checking for charts: {str(e)}")
    
    return charts_found


def _display_streamlit_chart(result: Dict[str, Any]) -> None:
    """
    Display a chart with a dynamic title based on the analysis type.
    
    Args:
        result: Dictionary containing chart data and metadata
    """
    try:
        chart_data_dict = result.get("chart_data")
        
        # Get the summary dictionary and analysis type
        summary = result.get("summary", {})
        analysis_type = summary.get("analysis_type", "Analysis Trend")
        
        # Validation: Check if chart data exists
        if chart_data_dict is None:
            st.warning("📊 No chart data was received from the tool.")
            return
        
        # Reconstruct the DataFrame from the dictionary
        chart_data = pd.DataFrame(
            chart_data_dict['data'],
            index=pd.to_datetime(chart_data_dict['index']),
            columns=chart_data_dict['columns']
        )
        
        # Display the chart with dynamic title
        st.subheader(f"📈 {analysis_type} (Last 4 Weeks)")
        st.line_chart(chart_data)
        
    except Exception as e:
        st.error(f"❌ Failed to display the chart. Error: {e}")


def _display_process_sequence(process_sequence: List[Dict[str, Any]]) -> None:
    """
    Display the structured process sequence in Streamlit.
    
    Args:
        process_sequence: Process sequence from chatbot
    """
    for i, step in enumerate(process_sequence, 1):
        step_type = step.get("type", "unknown")
        timestamp = step.get("timestamp", "")
        
        # Create a clean timestamp display
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp[-8:] if len(timestamp) >= 8 else timestamp
        else:
            time_str = ""
        
        if step_type == "thought":
            with st.container():
                st.success(f"🧠 **THOUGHT** ({time_str})")
                content = step.get('content', '')
                if content:
                    st.write(content)
                if step.get('thought_signature'):
                    st.caption(f"Signature: {step.get('thought_signature')}")
                    
        elif step_type == "tool_call":
            with st.container():
                st.warning(f"🛠️ **TOOL CALL** ({time_str})")
                st.write(f"**Tool:** {step.get('tool_name', '')}")
                tool_args = step.get('tool_args', {})
                if tool_args:
                    st.json(tool_args)
                    
        elif step_type == "tool_result":
            with st.container():
                success = step.get('success', False)
                if success:
                    st.success(f"📊 **TOOL RESULT** ({time_str})")
                else:
                    st.error(f"❌ **TOOL ERROR** ({time_str})")
                
                st.write(f"**Tool:** {step.get('tool_name', '')}")
                result = step.get('result', '')
                
                # Display result based on length and content
                if len(str(result)) > 500:
                    with st.expander("View Result", expanded=False):
                        st.text(str(result))
                else:
                    st.code(str(result))
                
                if not success and step.get('error'):
                    st.error(f"Error: {step.get('error')}")
                    
        elif step_type == "response":
            with st.container():
                st.info(f"💬 **INTERMEDIATE RESPONSE** ({time_str})")
                content = step.get('content', '')
                if content:
                    st.write(content)
                    
        elif step_type == "final_response":
            with st.container():
                st.success(f"🎯 **FINAL RESPONSE** ({time_str})")
                content = step.get('content', '')
                if content:
                    st.write(content)
                    
        elif step_type == "error":
            with st.container():
                st.error(f"❌ **ERROR** ({time_str})")
                st.write(step.get('content', ''))
                if step.get('error'):
                    st.code(step.get('error'), language='text')
        
        # Add separator between steps (except for last step)
        if i < len(process_sequence):
            st.write("---")

if __name__ == "__main__":
    main()
