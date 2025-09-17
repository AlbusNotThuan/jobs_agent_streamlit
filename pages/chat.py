# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer Streamlit Chat Interface
AI-powered chatbot với tích hợp các tool phân tích skills và hiển thị chart

Usage:
    streamlit run streamlit_chat.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, List, Any
import streamlit as st
import pandas as pd
from io import BytesIO
import ast



# Fix import errors for tools modules
import sys
import os
tools_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
if tools_path not in sys.path:
    sys.path.append(tools_path)

try:
    from chatbot_class import SkillsAnalyzerChatbot
except ImportError as e:
    st.error(f"⚠️ Import error: {e}")
    st.error("Make sure all required files are in the same directory")
    st.stop()

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class StreamlitSkillsAnalyzerChatbot:
    def __init__(self):

        
        # Initialize the main chatbot class with verbose mode for detailed output
        self.chatbot = SkillsAnalyzerChatbot(verbose=True)
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'session_active' not in st.session_state:
            st.session_state.session_active = True
        if 'show_debug_info' not in st.session_state:
            st.session_state.show_debug_info = False
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []  # Store rich chat messages with charts, thinking process
        if 'charts_data' not in st.session_state:
            st.session_state.charts_data = {}  # Store chart data persistently

    

    def display_message(self, message: str) -> None:
        """
        Displays a message in Streamlit chat interface.

        Args:
            message (str): The message string to display.

        Returns:
            None
        """
        st.chat_message("assistant").write(message)

    def end_session(self) -> None:
        """
        Ends the chatbot session by setting session_active to False.

        Args:
            None

        Returns:
            None
        """
        st.session_state.session_active = False
        st.chat_message("assistant").write("👋 Session ended. Refresh the page to start a new conversation!")

    def create_test_chart(self, data_json: str, chart_type: str = "bar", 
                         title: str = "Test Chart") -> None:
        """
        Creates and displays a test chart directly in Streamlit.

        Args:
            data_json (str): Dictionary data as JSON string.
            chart_type (str): Type of chart ("bar", "pie", "line").
            title (str): Title of the chart.

        Returns:
            None
        """
        chart_buffer = self.create_chart_from_data(
            data_json, 
            chart_type=chart_type,
            title=title,
            xlabel="Categories",
            ylabel="Values"
        )
        if chart_buffer.getvalue():  # Check if buffer has data
            # Store chart in session state to persist after button clicks
            chart_key = f"chart_{title}_{chart_type}"
            st.session_state[chart_key] = chart_buffer.getvalue()
            
            # Display small chart with download and expand options
            st.image(chart_buffer, caption=f"{title} - {chart_type.title()} Chart", width=400)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Download button
                st.download_button(
                    label="📥 Download Chart",
                    data=st.session_state[chart_key],
                    file_name=f"{title.replace(' ', '_').lower()}_{chart_type}.png",
                    mime="image/png"
                )
            
            with col2:
                # Expand button using button + session state
                if st.button("🔍 View Full Size", key=f"expand_btn_{title}"):
                    st.session_state[f"show_full_{title}"] = not st.session_state.get(f"show_full_{title}", False)
            
            # Show full size if toggled
            if st.session_state.get(f"show_full_{title}", False):
                st.markdown("**Full Size Chart:**")
                st.image(BytesIO(st.session_state[chart_key]), caption=f"{title} - Full Size", use_column_width=True)
        else:
            st.error("❌ Failed to create chart")

    def display_skills_chart(self, data_json: str, analysis_type: str) -> None:
        """
        Displays chart for skills analysis data.

        Args:
            data_json (str): Skills analysis data from tools as JSON string.
            analysis_type (str): Type of analysis to determine chart format.

        Returns:
            None
        """
        try:
            data = json.loads(data_json)
        except:
            st.error("❌ Invalid data format for chart display")
            return
            
        if not data.get("success"):
            st.error(f"❌ {data.get('message', 'Analysis failed')}")
            return
        
        result = data["data"]
        
        if analysis_type == "all_skills" and result.get('top_skills'):
            # Create bar chart for top skills
            skills_data = {}
            for skill in result['top_skills'][:10]:
                skills_data[skill['skill']] = float(skill['frequency'])
            
            chart_buffer = self.create_chart_from_data(
                json.dumps(skills_data), 
                chart_type="bar",
                title="Top 10 Most In-Demand Skills",
                xlabel="Skills",
                ylabel="Number of Jobs"
            )
            
            # Display chart with controls
            if chart_buffer.getvalue():
                # Store chart in session state
                st.session_state["chart_top_skills"] = chart_buffer.getvalue()
                
                st.image(chart_buffer, caption="Top Skills Analysis", width=400)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.download_button(
                        label="📥 Download Chart",
                        data=st.session_state["chart_top_skills"],
                        file_name="top_skills_analysis.png",
                        mime="image/png"
                    )
                
                with col2:
                    if st.button("🔍 View Full Size", key="expand_top_skills"):
                        st.session_state["show_full_top_skills"] = not st.session_state.get("show_full_top_skills", False)
                
                # Show full size if toggled
                if st.session_state.get("show_full_top_skills", False):
                    st.markdown("**Full Size Chart:**")
                    st.image(BytesIO(st.session_state["chart_top_skills"]), caption="Top Skills Analysis - Full Size", use_column_width=True)
            else:
                st.error("❌ Failed to create top skills chart")
        
        elif analysis_type == "hot_skills" and result.get('hot_skills'):
            # Create pie chart for hot skills
            hot_skills_data = {}
            for skill in result['hot_skills'][:8]:
                hot_skills_data[skill['skill']] = float(skill['frequency'])
            
            chart_buffer = self.create_chart_from_data(
                json.dumps(hot_skills_data),
                chart_type="pie", 
                title="Hot Skills Distribution - Last Month"
            )
            
            # Display chart with controls
            if chart_buffer.getvalue():
                # Store chart in session state
                st.session_state["chart_hot_skills"] = chart_buffer.getvalue()
                
                st.image(chart_buffer, caption="Hot Skills Distribution", width=400)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.download_button(
                        label="📥 Download Chart",
                        data=st.session_state["chart_hot_skills"],
                        file_name="hot_skills_distribution.png",
                        mime="image/png"
                    )
                
                with col2:
                    if st.button("🔍 View Full Size", key="expand_hot_skills"):
                        st.session_state["show_full_hot_skills"] = not st.session_state.get("show_full_hot_skills", False)
                
                # Show full size if toggled
                if st.session_state.get("show_full_hot_skills", False):
                    st.markdown("**Full Size Chart:**")
                    st.image(BytesIO(st.session_state["chart_hot_skills"]), caption="Hot Skills Distribution - Full Size", use_column_width=True)
            else:
                st.error("❌ Failed to create hot skills chart")
        
        elif analysis_type == "category_skills":
            # Create multiple charts for different categories
            for cat_key, cat_info in result.items():
                if cat_info.get('skills') and len(cat_info['skills']) > 0:
                    cat_data = {}
                    for skill in cat_info['skills'][:5]:
                        cat_data[skill['skill']] = float(skill['frequency'])
                    
                    if cat_data:
                        chart_buffer = self.create_chart_from_data(
                            json.dumps(cat_data),
                            chart_type="bar",
                            title=f"Top Skills in {cat_info['name']}",
                            xlabel="Skills",
                            ylabel="Frequency"
                        )
                        
                        # Display chart with controls
                        if chart_buffer.getvalue():
                            # Store chart in session state
                            chart_key = f"chart_{cat_key}"
                            st.session_state[chart_key] = chart_buffer.getvalue()
                            
                            st.image(chart_buffer, caption=f"{cat_info['name']} Skills", width=400)
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.download_button(
                                    label="📥 Download Chart",
                                    data=st.session_state[chart_key],
                                    file_name=f"{cat_info['name'].replace(' ', '_').lower()}_skills.png",
                                    mime="image/png",
                                    key=f"download_{cat_key}"
                                )
                            
                            with col2:
                                if st.button("🔍 View Full Size", key=f"expand_{cat_key}"):
                                    st.session_state[f"show_full_{cat_key}"] = not st.session_state.get(f"show_full_{cat_key}", False)
                            
                            # Show full size if toggled
                            if st.session_state.get(f"show_full_{cat_key}", False):
                                st.markdown("**Full Size Chart:**")
                                st.image(BytesIO(st.session_state[chart_key]), caption=f"{cat_info['name']} Skills - Full Size", use_column_width=True)
                        else:
                            st.error(f"❌ Failed to create {cat_info['name']} chart")

    def format_skills_response(self, data_json: str, analysis_type: str) -> str:
        """
        Format the analysis results for chatbot response.

        Args:
            data_json (str): Analysis data from tools as JSON string.
            analysis_type (str): Type of analysis performed.

        Returns:
            str: Formatted response string.
        """
        try:
            data = json.loads(data_json)
        except:
            return "❌ Invalid data format for response formatting"
            
        if not data.get("success"):
            return f"❌ {data.get('message', 'Analysis failed')}"
        
        result = data["data"]
        
        if analysis_type == "all_skills":
            response = f"📊 **GENERAL SKILLS ANALYSIS**\n\n"
            response += f"📈 Total jobs analyzed: {result.get('total_jobs', 0)}\n"
            response += f"📋 Jobs with skills info: {result.get('valid_jobs', 0)}\n"
            response += f"🔍 Unique skills found: {result.get('total_unique_skills', 0)}\n\n"
            
            response += "🏆 **TOP SKILLS:**\n"
            for i, skill in enumerate(result.get('top_skills', [])[:10], 1):
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage']}%)\n"
        
        elif analysis_type == "hot_skills":
            response = f"🔥 **HOT SKILLS - LAST MONTH**\n\n"
            response += f"📅 Period: {result.get('period', 'Recent')}\n"
            response += f"📊 Jobs analyzed: {result.get('total_recent_jobs', 0)}\n\n"
            
            response += "🚀 **TOP HOT SKILLS:**\n"
            for i, skill in enumerate(result.get('hot_skills', [])[:10], 1):
                fire_level = "🔥" * min(int(skill['percentage_of_valid'] / 10) + 1, 5)
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage_of_valid']:.1f}%) {fire_level}\n"
        
        elif analysis_type == "category_skills":
            response = f"📂 **SKILLS BY CATEGORY**\n\n"
            for cat_key, cat_info in result.items():
                if cat_info.get('skills'):
                    response += f"🔸 **{cat_info['name']}:**\n"
                    for skill in cat_info['skills'][:5]:
                        response += f"   • {skill['skill']} - {skill['frequency']} jobs\n"
                    response += "\n"
        
        elif analysis_type == "trends":
            response = f"📈 **SKILLS TRENDS ANALYSIS**\n\n"
            response += f"📅 Period: {result.get('analysis_period', 'Recent')}\n"
            response += f"📊 Total jobs: {result.get('total_jobs_in_period', 0)}\n\n"
            
            response += "🏆 **TOP TRENDING SKILLS:**\n"
            for i, (skill, count) in enumerate(result.get('top_skills_overall', [])[:10], 1):
                response += f"{i:2d}. {skill} - {count} mentions\n"
        
        elif analysis_type == "job_categories":
            response = f"💼 **SKILLS BY JOB CATEGORIES**\n\n"
            for category, data in result.items():
                response += f"🔹 **{category}** ({data['job_count']} jobs):\n"
                for skill, count in data['top_skills'][:5]:
                    response += f"   • {skill}: {count}\n"
                response += "\n"
        
        return response

    def chat(self, user_message: str) -> str:
        """
        Main chat function using the SkillsAnalyzerChatbot class with a refined UI.
        The Thinking Process is always shown, while Debug Info is optional.
        """
        try:
            # Capture stdout to show thinking and tool processes
            import io
            import contextlib
            
            # Create a string buffer to capture print output
            captured_output = io.StringIO()
            
            # Use the main chatbot class for processing
            with contextlib.redirect_stdout(captured_output):
                chat_result = self.chatbot.chat(user_message)
            
            # Store result for process display
            st.session_state.last_chat_result = chat_result
            
            # Get captured output
            debug_output = captured_output.getvalue()
            
            # Handle the structured response
            if not isinstance(chat_result, dict):
                clean_response = str(chat_result)
                message_data = {
                    'type': 'assistant',
                    'content': clean_response,
                    'timestamp': datetime.now().isoformat(),
                    'thinking_process': None,
                    'charts': [],
                    'debug_info': debug_output if st.session_state.get('show_debug_info', True) else None
                }
            else:
                if not chat_result.get("success", False):
                    clean_response = chat_result.get("final_response", "❌ Error processing request")
                    if "error" in chat_result:
                        clean_response += f"\nError details: {chat_result['error']}"
                    
                    message_data = {
                        'type': 'assistant',
                        'content': clean_response,
                        'timestamp': datetime.now().isoformat(),
                        'thinking_process': None,
                        'charts': [],
                        'debug_info': debug_output if st.session_state.get('show_debug_info', True) else None,
                        'error': True
                    }
                else:
                    clean_response = chat_result.get("final_response", "🤖 No response generated")
                    
                    # Prepare message data structure
                    message_data = {
                        'type': 'assistant',
                        'content': clean_response,
                        'timestamp': datetime.now().isoformat(),
                        'thinking_process': chat_result.get("process_sequence", []),
                        'charts': [],
                        'debug_info': debug_output if st.session_state.get('show_debug_info', True) else None,
                        'career_mode': False  # Always skills analyzer mode
                    }
                    
                    # Extract and store chart data
                    charts_data = self._extract_charts_from_result(chat_result)
                    message_data['charts'] = charts_data
                    
                    # Store charts in persistent storage
                    for chart in charts_data:
                        chart_id = f"chart_{len(st.session_state.chat_messages)}_{chart['title'].replace(' ', '_')}"
                        st.session_state.charts_data[chart_id] = chart
            
            # Add assistant message to chat messages
            # Note: User message is already added in main() before calling this function
            st.session_state.chat_messages.append(message_data)
            
            # Store in legacy conversation history for backward compatibility
            st.session_state.conversation_history.append(f"User: {user_message}")
            st.session_state.conversation_history.append(f"Assistant: {clean_response}")
            
            return clean_response
            
        except Exception as e:
            error_msg = f"❌ Error processing your request: {str(e)}"
            
            # Store error message
            error_message_data = {
                'type': 'assistant',
                'content': error_msg,
                'timestamp': datetime.now().isoformat(),
                'thinking_process': None,
                'charts': [],
                'debug_info': None,
                'error': True
            }
            
            # Note: User message is already added in main() before calling this function
            st.session_state.chat_messages.append(error_message_data)
            
            st.session_state.conversation_history.append(f"User: {user_message}")
            st.session_state.conversation_history.append(f"Assistant: {error_msg}")
            
            return error_msg
    
    def _extract_charts_from_result(self, chat_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract chart data from chat result for persistent storage.
        
        Args:
            chat_result (Dict[str, Any]): Chat result containing process sequence
            
        Returns:
            List[Dict[str, Any]]: List of chart data dictionaries
        """
        charts = []
        try:
            process_sequence = chat_result.get("process_sequence", [])
            
            for step in process_sequence:
                if step.get("type") == "tool_result" and step.get("success"):
                    result_str = step.get("result")
                    
                    # Parse tool result string
                    if isinstance(result_str, str):
                        try:
                            import ast
                            result = ast.literal_eval(result_str)
                        except (ValueError, SyntaxError):
                            continue
                    else:
                        result = result_str
                    
                    # Check if result contains chart data
                    if (isinstance(result, dict) and 
                        result.get("chart_data") is not None and 
                        result.get("chart_type") is not None):
                        
                        chart_data = {
                            'chart_data': result.get("chart_data"),
                            'chart_type': result.get("chart_type", "line_chart"),
                            'summary': result.get("summary", {}),
                            'title': result.get("summary", {}).get("analysis_type", "Analysis Chart"),
                            'timestamp': datetime.now().isoformat()
                        }
                        charts.append(chart_data)
                        
        except Exception as e:
            print(f"[STREAMLIT_ERROR] Error extracting charts: {e}")
            
        return charts
    
    def _check_and_display_charts(self, chat_result: Dict[str, Any]) -> None:
        """
        Check for chart data in chat result and display charts using Streamlit.
        """
        try:
            print("[STREAMLIT_DEBUG] Calling _check_and_display_charts...")
            process_sequence = chat_result.get("process_sequence", [])
            
            for step in process_sequence:
                print(f"[STREAMLIT_DEBUG] Inspecting process step of type: {step.get('type')}")

                if step.get("type") == "tool_result" and step.get("success"):
                    result_str = step.get("result")
                    
                    # --- START OF THE FIX ---
                    # The tool result is a string representation of a Python dict.
                    # We use ast.literal_eval() to safely parse it back into a dictionary.
                    if isinstance(result_str, str):
                        try:
                            # Use ast.literal_eval for Python dict strings
                            result = ast.literal_eval(result_str)
                            print("[STREAMLIT_DEBUG] Successfully parsed tool result string using ast.literal_eval()")
                        except (ValueError, SyntaxError):
                            print(f"[STREAMLIT_DEBUG] Could not parse tool result string: {result_str[:100]}...")
                            continue # Skip to the next step if parsing fails
                    else:
                        # If it's already a dict, just use it
                        result = result_str
                    # --- END OF THE FIX ---

                    # Now 'result' is a proper dictionary, and this check will work
                    if (isinstance(result, dict) and 
                        result.get("chart_data") is not None and 
                        result.get("chart_type") is not None):
                        
                        print("[STREAMLIT_DEBUG] FOUND A VALID CHART TO DISPLAY in tool result!")
                        self._display_streamlit_chart(result) # This will now be called
                        
        except Exception as e:
            st.warning(f"⚠️ A failure occurred in _check_and_display_charts: {str(e)}")
            print(f"[STREAMLIT_ERROR] in _check_and_display_charts: {e}")
    
    def _display_streamlit_chart(self, result: Dict[str, Any]) -> None:
        """
        Displays a chart with a dynamic title based on the analysis type.
        Supports both line charts (for trends) and bar charts (for distributions).
        """
        try:
            chart_data_dict = result.get("chart_data")
            chart_type = result.get("chart_type", "line_chart")
            
            # Get the summary dictionary provided by the tool
            summary = result.get("summary", {})
            analysis_type = summary.get("analysis_type", "Analysis Trend")

            # Validation: Check if chart data exists
            if chart_data_dict is None:
                st.warning("📊 No chart data was received from the tool.")
                return

            # Handle different chart types
            if chart_type == "bar_chart":
                # Bar chart data comes as a simple dictionary {label: value}
                st.subheader(f"📊 {analysis_type} (Last 4 Weeks)")
                
                # Convert dictionary to DataFrame for bar chart
                if isinstance(chart_data_dict, dict):
                    # Create DataFrame from the dictionary
                    chart_df = pd.DataFrame(
                        list(chart_data_dict.items()), 
                        columns=['Category', 'Frequency']
                    ).set_index('Category')
                    
                    # Display the bar chart
                    st.bar_chart(
                        chart_df, 
                        height=400,
                        use_container_width=True
                    )
                    
                    # Display summary information
                    if summary:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if "total_mentions" in summary:
                                st.metric("Total Mentions", summary["total_mentions"])
                            elif "total_postings" in summary:
                                st.metric("Total Postings", summary["total_postings"])
                        with col2:
                            if "top_skill" in summary and summary["top_skill"]:
                                st.metric("Top Skill", summary["top_skill"])
                            elif "top_role" in summary and summary["top_role"]:
                                st.metric("Top Role", summary["top_role"])
                        with col3:
                            if "skills_count" in summary:
                                st.metric("Skills Analyzed", summary["skills_count"])
                            elif "roles_count" in summary:
                                st.metric("Roles Analyzed", summary["roles_count"])
                
                else:
                    st.warning("📊 Bar chart data format is not supported.")
                    
            elif chart_type == "line_chart":
                # Line chart data comes as pandas split format
                st.subheader(f"📈 {analysis_type} (Last 4 Weeks)")
                
                # Reconstruct the DataFrame from the split dictionary
                chart_data = pd.DataFrame(
                    chart_data_dict['data'],
                    index=pd.to_datetime(chart_data_dict['index']),
                    columns=chart_data_dict['columns']
                )
                
                # Display the line chart
                st.line_chart(chart_data, height=400)
                
                # Display summary information
                if summary:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if "total_mentions" in summary:
                            st.metric("Total Mentions", summary["total_mentions"])
                        elif "total_postings" in summary:
                            st.metric("Total Postings", summary["total_postings"])
                    with col2:
                        if "peak_skill" in summary and summary["peak_skill"]:
                            st.metric("Peak Skill", summary["peak_skill"])
                        elif "peak_role" in summary and summary["peak_role"]:
                            st.metric("Peak Role", summary["peak_role"])
                    with col3:
                        if "items_analyzed" in summary:
                            st.metric("Items Analyzed", len(summary["items_analyzed"]))
            
            else:
                st.warning(f"📊 Chart type '{chart_type}' is not supported.")

        except Exception as e:
            # Basic error handling in case the reconstruction or display fails
            st.error(f"❌ Failed to display the chart. Error: {e}")
            print(f"[STREAMLIT_ERROR] A failure occurred in _display_streamlit_chart: {e}")
    
    def _display_process_sequence(self, process_sequence: List[Dict[str, Any]]) -> None:
        """
        Display the structured process sequence in Streamlit.

        Args:
            process_sequence (List[Dict[str, Any]]): Process sequence from chatbot

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

    def _clean_response_from_debug(self, response: str) -> str:
        """
        Remove debug information from response to get clean user-facing content.
        
        Args:
            response (str): Raw response from chatbot including debug info
            
        Returns:
            str: Clean response without debug information
        """
        if not response:
            return response
            
        lines = response.split('\n')
        clean_lines = []
        skip_line = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip debug-related lines
            if (line_stripped.startswith(('🧠 **THINKING:', '🧠 **THOUGHT:', '💬 **RESPONSE:', 
                                        '🔧 **Using tool:', '🔧 **TOOL USED:', 
                                        '📊 **Tool result', '📊 **TOOL RESULT',
                                        '🐍 **Executing code:', '🐍 **CODE EXECUTION:',
                                        '✅ **Code execution result:', '✅ **CODE RESULT:',
                                        '[Gemini Part Fields]', '🧠 Generating response')) or
                line_stripped.startswith('-' * 20) or
                line_stripped.startswith('Arguments:') or
                line_stripped.startswith('**Arguments:**')):
                skip_line = True
                continue
            
            # Reset skip flag if we encounter non-debug content
            if line_stripped and not any(line_stripped.startswith(prefix) for prefix in 
                                       ['🧠', '🔧', '📊', '🐍', '✅', '[Gemini', 'Arguments']):
                skip_line = False
            
            # Add line if not skipping
            if not skip_line and line_stripped:
                clean_lines.append(line)
        
        # Join and clean up extra whitespace
        clean_response = '\n'.join(clean_lines).strip()
        
        # Remove any remaining debug patterns
        import re
        clean_response = re.sub(r'🧠 \*\*ANALYSIS:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        clean_response = re.sub(r'🧠 \*\*PLAN:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        
        return clean_response.strip()
    
    def _display_debug_output(self, debug_output: str) -> None:
        """
        Display debug output in a structured way for Streamlit.
        
        Args:
            debug_output (str): Captured debug output from chatbot
        """
        lines = debug_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse different types of output
            if line.startswith('🧠 Generating response'):
                st.info(f"⚡ {line}")
            elif line.startswith('🧠 **THINKING:**') or line.startswith('🧠 **THOUGHT:**'):
                thinking_text = line.replace('🧠 **THINKING:** ', '').replace('🧠 **THOUGHT:** ', '')
                st.success(f"🧠 **THINKING:** {thinking_text}")
            elif line.startswith('💬 **RESPONSE:**'):
                response_text = line.replace('💬 **RESPONSE:** ', '')
                st.info(f"💬 **RESPONSE:** {response_text}")
            elif line.startswith('🔧 **Using tool:**'):
                tool_text = line.replace('🔧 **Using tool:** ', '')
                st.warning(f"🔧 **TOOL CALL:** {tool_text}")
            elif line.startswith('🛠️  MODEL YÊU CẦU GỌI TOOL:'):
                tool_text = line.replace('🛠️  MODEL YÊU CẦU GỌI TOOL: ', '')
                st.warning(f"🛠️ **TOOL REQUEST:** {tool_text}")
            elif line.startswith('Tham số:'):
                args_text = line.replace('Tham số: ', '')
                st.text(f"   📋 Parameters: {args_text}")
            elif line.startswith('   Arguments:'):
                args_text = line.replace('   Arguments: ', '')
                st.text(f"   📋 Arguments: {args_text}")
            elif line.startswith('📊 **Tool result:**'):
                result_text = line.replace('📊 **Tool result:** ', '')
                st.success(f"✅ **Tool Result:** {result_text}")
            elif line.startswith('📊 **Tool result from'):
                result_text = line
                st.success(f"✅ {result_text}")
            elif line.startswith('🧠 **FINAL RESPONSE:**'):
                st.success("🎯 **FINAL RESPONSE GENERATED**")
            elif line.startswith('[Gemini Part Fields]'):
                # Show Gemini part fields for debugging
                st.code(line, language='json')
            elif line.startswith('-' * 20):
                st.divider()
            elif line.startswith('❌'):
                st.error(line)
            else:
                # Regular debug output
                if line:
                    st.text(line)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Toggle debug information display"""
        st.session_state.show_debug_info = enabled
        self.chatbot.set_verbose_mode(enabled)
    
    def new_chat(self) -> None:
        """Start a new chat session"""
        self.chatbot.new_chat()
        st.session_state.conversation_history = []
        st.session_state.chat_messages = []
        st.session_state.charts_data = {}
        st.session_state.session_active = True
    
    def get_session_stats(self) -> dict:
        """Get current session statistics"""
        return self.chatbot.get_session_stats()
    
    def set_thinking_budget(self, budget: int) -> None:
        """Set thinking budget for the chatbot"""
        self.chatbot.set_thinking_budget(budget)
    
    def set_generation_preset(self, preset: str) -> None:
        """Set generation preset for the chatbot"""
        self.chatbot.set_generation_preset(preset)
    
    def display_conversation_with_debug(self) -> None:
        """Display conversation history with enhanced formatting using rich message format"""
        if not st.session_state.chat_messages:
            return
            
        for i, message in enumerate(st.session_state.chat_messages):
            if message['type'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
                    
            elif message['type'] == 'assistant':
                with st.chat_message("assistant"):
                    # Display thinking process FIRST (before response)
                    if message.get('thinking_process'):
                        process_title = "🎯 **Career Analysis Process**" if message.get('career_mode') else "🧠 **Thinking Process**"
                        with st.expander(f"{process_title} ({len(message['thinking_process'])} steps)", expanded=st.session_state.get('show_debug_info', False)):
                            self._display_process_sequence(message['thinking_process'])
                    
                    # Display debug info if enabled
                    if st.session_state.get('show_debug_info', True) and message.get('debug_info'):
                        with st.expander("🔍 **Debug Information** (Console Output)", expanded=False):
                            self._display_debug_output(message['debug_info'])

                    # Display main content (AI response)
                    if message.get('error'):
                        st.error(message['content'])
                    else:
                        st.write(message['content'])
                    
                    # Handle career advisor mode responses  
                    if message.get('career_mode') and message.get('thinking_process'):
                        self._display_career_advisor_results(message['thinking_process'])
                    
                    # Display charts
                    if message.get('charts'):
                        for chart_data in message['charts']:
                            self._display_persistent_chart(chart_data)
                    
                    
    
    def _display_career_advisor_results(self, thinking_process: List[Dict[str, Any]]) -> None:
        """
        Display career advisor results from thinking process.
        
        Args:
            thinking_process (List[Dict[str, Any]]): Process sequence from chatbot
        """
        # Check if response contains career advisor tool results
        has_career_tool_result = any(
            step.get("type") == "tool_result" and step.get("tool_name") == "career_advisor_tool"
            for step in thinking_process
        )
        
        if has_career_tool_result:
            st.success("✅ **Career Advisor đã phân tích xong:**")
            
            # Find career tool result
            for step in thinking_process:
                if (step.get("type") == "tool_result" and 
                    step.get("tool_name") == "career_advisor_tool" and 
                    step.get("success", False)):
                    
                    # Try to parse career advisor result
                    try:
                        import ast
                        tool_result = step.get("result", "")
                        
                        # If result is a string representation of dict, parse it
                        if isinstance(tool_result, str) and tool_result.startswith("{"):
                            career_result = ast.literal_eval(tool_result)
                            
                            # Extract final response from career advisor
                            career_response = career_result.get("final_response", "")
                            
                            # Try to parse JSON from career response
                            if career_response:
                                try:
                                    import json
                                    json_response = json.loads(career_response)
                                    
                                    if json_response.get("status") == "input_required":
                                        st.info("💡 **Cần thêm thông tin:**")
                                        st.write(json_response.get("message", ""))
                                        if json_response.get("next_questions"):
                                            st.markdown("**Gợi ý câu hỏi:**")
                                            for q in json_response["next_questions"]:
                                                st.markdown(f"• {q}")
                                    
                                    elif json_response.get("career_recommendations"):
                                        recs = json_response["career_recommendations"]
                                        
                                        if recs.get("personality_analysis"):
                                            st.markdown("**🧠 Phân tích tính cách:**")
                                            st.write(recs["personality_analysis"])
                                        
                                        if recs.get("recommended_skills"):
                                            st.markdown("**🛠️ Kỹ năng đề xuất:**")
                                            for skill in recs["recommended_skills"][:5]:
                                                st.markdown(f"• {skill}")
                                        
                                        if recs.get("career_paths"):
                                            st.markdown("**💼 Lộ trình nghề nghiệp:**")
                                            for path in recs["career_paths"][:3]:
                                                st.markdown(f"• {path}")
                                        
                                        if recs.get("market_insights"):
                                            st.markdown("**📊 Thông tin thị trường:**")
                                            for insight in recs["market_insights"][:3]:
                                                st.markdown(f"• {insight}")
                                
                                except json.JSONDecodeError:
                                    # Display as raw text if not JSON
                                    pass
                    
                    except (ValueError, SyntaxError):
                        # If parsing fails, display raw result
                        pass
    
    def _display_persistent_chart(self, chart_data: Dict[str, Any]) -> None:
        """
        Display a chart from persistent chart data.
        
        Args:
            chart_data (Dict[str, Any]): Chart data dictionary
        """
        try:
            chart_data_dict = chart_data.get("chart_data")
            chart_type = chart_data.get("chart_type", "line_chart")
            title = chart_data.get("title", "Analysis Chart")
            summary = chart_data.get("summary", {})
            analysis_type = summary.get("analysis_type", "Analysis Trend")

            # Validation: Check if chart data exists
            if chart_data_dict is None:
                st.warning("⚠️ No chart data available to display")
                return

            # Handle different chart types
            if chart_type == "bar_chart":
                st.markdown(f"**📊 {title}**")
                
                # Convert data to format suitable for Streamlit
                data_for_chart = {}
                
                # Handle different data formats
                if isinstance(chart_data_dict, dict):
                    for key, value in chart_data_dict.items():
                        try:
                            # Convert value to float, handling lists/nested structures
                            if isinstance(value, (list, tuple)):
                                # If it's a list, take the first numeric value or sum
                                numeric_values = [v for v in value if isinstance(v, (int, float))]
                                data_for_chart[str(key)] = float(numeric_values[0]) if numeric_values else 0.0
                            elif isinstance(value, (int, float)):
                                data_for_chart[str(key)] = float(value)
                            else:
                                # Try to convert string to float
                                data_for_chart[str(key)] = float(str(value))
                        except (ValueError, TypeError, IndexError):
                            # Skip invalid values
                            continue
                elif isinstance(chart_data_dict, list):
                    # Handle list format - convert to simple indexed data
                    for i, value in enumerate(chart_data_dict):
                        try:
                            data_for_chart[f"Item {i+1}"] = float(value)
                        except (ValueError, TypeError):
                            continue
                else:
                    st.warning("⚠️ Chart data format not supported for bar chart")
                    return
                    
                if data_for_chart:
                    st.bar_chart(data_for_chart)
                else:
                    st.warning("⚠️ No valid numeric data found for bar chart")
                
            elif chart_type == "line_chart":
                st.markdown(f"**📈 {title}**")
                
                # Handle line chart data format
                try:
                    if isinstance(chart_data_dict, dict):
                        # Check if it's in pandas DataFrame format (split)
                        if 'data' in chart_data_dict and 'index' in chart_data_dict and 'columns' in chart_data_dict:
                            # Reconstruct DataFrame from split format
                            import pandas as pd
                            chart_df = pd.DataFrame(
                                chart_data_dict['data'],
                                index=pd.to_datetime(chart_data_dict['index']),
                                columns=chart_data_dict['columns']
                            )
                            st.line_chart(chart_df)
                        else:
                            # Simple dict format
                            st.line_chart(chart_data_dict)
                    elif isinstance(chart_data_dict, list):
                        # Convert list to simple line chart
                        import pandas as pd
                        chart_df = pd.DataFrame(chart_data_dict, columns=['Value'])
                        st.line_chart(chart_df)
                    else:
                        st.warning("⚠️ Chart data format not supported for line chart")
                except Exception as line_error:
                    st.warning(f"⚠️ Error creating line chart: {line_error}")
            
            else:
                st.warning(f"⚠️ Unsupported chart type: {chart_type}")

        except Exception as e:
            # Basic error handling in case the reconstruction or display fails
            st.error(f"❌ Failed to display the chart. Error: {e}")
            print(f"[STREAMLIT_ERROR] A failure occurred in _display_persistent_chart: {e}")
    
    def _display_structured_response(self, response_text: str) -> None:
        """Display structured response with different sections"""
        lines = response_text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('🧠 **THINKING:**'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "thinking"
                section_content = [line.replace('🧠 **THINKING:** ', '')]
            elif line.startswith('🔧 **TOOL'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "tool"
                section_content = [line]
            elif line.startswith('📊 **TOOL RESULT'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "result"
                section_content = [line]
            elif line and current_section:
                section_content.append(line)
            elif line and not current_section:
                # Regular text outside sections
                st.write(line)
        
        # Render final section
        if current_section:
            self._render_section(current_section, section_content)
    
    def _render_section(self, section_type: str, content: list) -> None:
        """Render a specific section with appropriate styling"""
        if section_type == "thinking":
            with st.expander("🧠 **Thinking Process**", expanded=False):
                for line in content:
                    st.write(line)
        elif section_type == "tool":
            with st.expander("🔧 **Tool Usage**", expanded=False):
                for line in content:
                    if line.startswith('**Arguments:**'):
                        st.code(line, language='json')
                    else:
                        st.write(line)
        elif section_type == "result":
            with st.expander("📊 **Tool Results**", expanded=False):
                for line in content:
                    st.write(line)

def _filter_response_for_display(response: str) -> str:
    """Filter out debug information from response for clean display"""
    lines = response.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip debug lines
        if (line.strip().startswith(('🧠 **THINKING:', '🔧 **TOOL', '📊 **TOOL', 
                                    '[Gemini Part Fields]', '💬 **RESPONSE:')) or
            line.strip().startswith('-' * 20)):
            continue
        
        # Keep regular content
        if line.strip():
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="LinkedIn Jobs Skills Analyzer",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("🤖 LinkedIn Jobs Skills Analyzer")
    st.markdown("""
<span style='font-size:2em'>👋</span> **Hi, I'm the LinkedIn Jobs Skills Analyzer Chatbot!** 🤖

<span style='font-size:1.2em'>✨ I am an AI-powered assistant designed to help you explore the job market and analyze skills trends.</span>

<span style='font-size:1.1em'>
I can:

- 🔍 **Search and analyze** the job market database
- 🧑 **Find jobs** that match your requirements
- 🤝 **Recommend jobs** based on your skills, industry, and position
- 📈 **Analyze and visualize** trending skills, job categories, and hiring trends
- 📊 **Display interactive charts** and statistics
- 💬 **Answer your questions** about job market data, skills, and trends
</span>

<span style='font-size:1.1em'>💡 Just type your questions or requests below and I'll get started!</span>
""", unsafe_allow_html=True)

    # Sidebar with help information and controls
    with st.sidebar:
        # Chat Controls
        st.markdown("""
        **🔧 Skills Analyzer:**
        - Analyze job market trends
        - Hot skills analysis
        - Industry statistics
        - Charts and reports
        
        *Example: "analyze trending skills", "top programming jobs"*
        """)
        
        st.divider()
        
        # Chatbot controls
        st.header("⚙️ Chatbot Settings")
        
        # # Debug mode toggle
        # debug_mode = st.checkbox(
        #     "🔍 Show Debug Info",
        #     value=st.session_state.get('show_debug_info', True),
        #     help="Show thinking process, tool calls, and debug information"
        # )
        # if debug_mode != st.session_state.get('show_debug_info', True):
        #     st.session_state.chatbot.set_debug_mode(debug_mode)
        
        # # Generation preset
        # preset = st.selectbox(
        #     "Generation Mode:",
        #     ["balanced", "analytical", "focused", "creative"],
        #     index=0,
        #     help="Choose the AI generation style"
        # )
        # if st.button("Apply Preset"):
        #     st.session_state.chatbot.set_generation_preset(preset)
        #     st.success(f"Applied '{preset}' preset!")
        
        # # Thinking budget
        # thinking_budget = st.slider(
        #     "Thinking Budget (tokens):",
        #     min_value=1024,
        #     max_value=8192,
        #     value=4096,
        #     step=512,
        #     help="How much thinking the AI can do"
        # )
        # if st.button("Set Thinking Budget"):
        #     st.session_state.chatbot.set_thinking_budget(thinking_budget)
        #     st.success(f"Set thinking budget to {thinking_budget} tokens!")
        
        # st.divider()
        
        # Session controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat"):
                st.session_state.chatbot.new_chat()
                st.session_state.conversation_history = []
                st.session_state.session_active = True
                st.rerun()
        
        with col2:
            if st.button("📊 Stats"):
                stats = st.session_state.chatbot.get_session_stats()
                st.info(f"Messages: {stats.get('total_messages', 0)}")
                st.info(f"Duration: {stats.get('session_duration', '0 minutes')}")
        
        # Show last process info if available
        if hasattr(st.session_state, 'last_chat_result') and st.session_state.last_chat_result:
            result = st.session_state.last_chat_result
            if result.get('success') and result.get('process_sequence'):
                st.divider()
                st.subheader("📋 Last Response Process")
                st.caption(f"Steps: {result.get('total_steps', 0)}")
                
                # Count different step types
                steps = result.get('process_sequence', [])
                thoughts = sum(1 for s in steps if s.get('type') == 'thought')
                tool_calls = sum(1 for s in steps if s.get('type') == 'tool_call')
                
                if thoughts > 0:
                    st.caption(f"🧠 Thoughts: {thoughts}")
                if tool_calls > 0:
                    st.caption(f"🛠️ Tool calls: {tool_calls}")
                    
                if st.button("🔍 View Details"):
                    with st.expander("Process Details", expanded=True):
                        st.session_state.chatbot._display_process_sequence(steps)
        
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.session_state.chat_messages = []
            st.session_state.charts_data = {}
            st.session_state.session_active = True
            st.rerun()

    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = StreamlitSkillsAnalyzerChatbot()
    
    # Ensure chatbot is always in skills analyzer mode
    if hasattr(st.session_state.chatbot, 'chatbot'):
        st.session_state.chatbot.chatbot.toggle_career_advisor_mode(False)

    # Display chat history with enhanced formatting
    st.session_state.chatbot.display_conversation_with_debug()

    # Chat input
    if st.session_state.session_active:
        placeholder = "Ask me about job market skills and trends..."
            
        user_input = st.chat_input(placeholder)
        
        if user_input:
            # Immediately add user message to session state and display it
            user_message_data = {
                'type': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            }
            st.session_state.chat_messages.append(user_message_data)
            
            # Display the user message immediately
            with st.chat_message("user"):
                st.write(user_input)
            
            # Show processing message and process AI response
            with st.status("🤔 Processing your request...", expanded=False) as status:
                st.write("🧠 AI is thinking...")
                
                # Process the request (this will add the assistant message)
                response = st.session_state.chatbot.chat(user_input)
                
                status.update(label="✅ Request completed!", state="complete", expanded=False)
            
            # Trigger rerun to display the new AI response
            st.rerun()
    else:
        st.info("Session ended. Click 'New Chat' to start a new conversation.")

    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main()
