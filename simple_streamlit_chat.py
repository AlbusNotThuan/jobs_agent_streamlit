
import streamlit as st
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from psycopg_query import query_database
from toolbox import plot_skill_frequency

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class SkillsAnalyzerChatbot:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.conversation_history = []
        self.session_active = 1
        self.max_autonomous_cycles = 10
        self.verbose_mode = False
        self.last_print_message = None
        self.thought_process_enabled = False

    def print_message(self, message: str) -> None:
        self.last_print_message = message

    def end_session(self) -> None:
        self.session_active = 0

    def chat(self, user_message: str) -> str:
        import os
        system_instruction_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_instruction.md")
        try:
            with open(system_instruction_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
        except Exception:
            system_instruction = ""

        config = types.GenerateContentConfig(
            tools=[
                self.print_message,
                self.end_session,
                query_database,
                plot_skill_frequency
            ],
            tool_config={'function_calling_config': {'mode': 'AUTO'}},
            system_instruction=system_instruction
        )
        try:
            autonomous_prompt = f"""
AUTONOMOUS AGENT ACTIVATION:
User Request: {user_message}

Instructions: You are now operating as a fully autonomous agent. Follow the ReAct framework and SHOW YOUR THINKING:

CRITICAL: ALWAYS make your thought process visible by using these exact formats:
 **THOUGHT:** [Analyze what the user needs and create your own analysis plan]
 **ACTION:** [Explain what tool you're about to use and why]
 **OBSERVATION:** [Analyze the results and decide next steps]

ReAct Framework Steps:
1. START with " **THOUGHT:**" - Analyze the user's request and determine what type of job market analysis is needed. Create your own plan based on the request.
2. State " **ACTION:**" before each tool use - Explain what database query or analysis you're performing
3. After each tool result, use " **OBSERVATION:**" - Analyze the results and decide if you need more data
4. Continue the cycle until you have complete information to answer the user's question
5. Provide comprehensive analysis and insights based on the data you retrieved
6. IMPORTANT: Always provide a brief summary in your response BEFORE calling end_session
7. Call print_message with your detailed findings, then end_session

AUTONOMY RULES:
- NO predefined categories or keyword matching - interpret the request naturally
- CREATE your own analysis approach based on what the user is asking
- DECIDE what database queries are needed based on the context
- ADAPT your analysis to the specific request, not preset patterns

Remember: NO CONFIRMATIONS NEEDED. Act immediately and autonomously.
SHOW YOUR THINKING PROCESS throughout the entire interaction.
Always include a summary of your findings in your final response text.
"""
            conversation_context = ""
            if self.conversation_history:
                conversation_context = "\n\nPrevious conversation context:\n" + "\n".join(self.conversation_history[-4:])
            full_message = autonomous_prompt + conversation_context
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_message,
                config=config
            )
            self.conversation_history.append(f"User: {user_message}")
            self.conversation_history.append(f"Agent: {response.text}")
            return response.text
        except Exception as e:
            return f"❌ Autonomous agent error: {str(e)}"

st.set_page_config(page_title="Simple Chatbot", page_icon="💬", layout="centered")

st.markdown("""
<style>
.chat-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 1.5rem 0 2.5rem 0;
}
.chat-bubble {
    padding: 0.75rem 1.2rem;
    border-radius: 18px;
    margin-bottom: 0.5rem;
    max-width: 80%;
    word-break: break-word;
    display: inline-block;
    font-size: 1.05rem;
}
.user-row {
    display: flex;
    justify-content: flex-end;
    align-items: flex-end;
    margin-bottom: 0.5rem;
}
.ai-row {
    display: flex;
    justify-content: flex-start;
    align-items: flex-end;
    margin-bottom: 0.5rem;
}
.user-bubble {
    background: linear-gradient(90deg, #6366f1 0%, #60a5fa 100%);
    color: white;
    border-bottom-right-radius: 4px;
}
.ai-bubble {
    background: #f1f5f9;
    color: #1e293b;
    border-bottom-left-radius: 4px;
    border: 1px solid #e5e7eb;
}
.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin: 0 0.5rem;
    background: #6366f1;
    color: white;
}
.avatar-ai {
    background: #f1f5f9;
    color: #6366f1;
    border: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;'>💬 Simple Streamlit Chatbot</h2>", unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'chatbot' not in st.session_state:
    st.session_state['chatbot'] = SkillsAnalyzerChatbot()

for sender, msg in st.session_state['messages']:
    if sender == "user":
        st.markdown(f"""
        <div class="user-row">
            <div class="chat-bubble user-bubble">{msg}</div>
            <div class="avatar">🧑</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-row">
            <div class="avatar avatar-ai">🤖</div>
            <div class="chat-bubble ai-bubble">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", "", key="user_input", placeholder="Type your message...")
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        st.session_state['messages'].append(("user", user_input))
        ai_response = st.session_state['chatbot'].chat(user_input)
        st.session_state['messages'].append(("ai", ai_response))
