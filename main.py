import streamlit as st
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="SkillAI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

with st.container():
    st.markdown(
        """
        <div style='
            background: linear-gradient(90deg, rgba(203,120,92,0.95) 0%, rgba(255,173,128,0.8) 60%, rgba(255,214,170,0.7) 100%);
            padding: 32px; 
            border-radius: 12px; 
            text-align: center;
            color: #360d00;
        '>
            <h2>Your future starts here!</h2>
            <p>Discover career paths and build the skills you need for tomorrow grounded by data of today.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    # --- Card 1: The App's Mission ---
    with col1:
        # The border=True parameter creates the clean "GitHub style" card
        with st.container(border=True, height=300):
            st.subheader("🧭 Our Mission")
            st.write(
                "This app is an AI agent powered by real-time job market data. "
                "By analyzing thousands of online job postings, our mission is to provide you with "
                "clear, data-driven guidance for your future career."
            )

    # --- Card 2: What The User Can Do ---
    with col2:
        with st.container(border=True, height=300):
            st.subheader("💬 What You Can Do")
            st.write(
                "Chat with our AI to get instant answers. You can ask about "
                "job market trends, discover in-demand skills, or receive personalized "
                "career recommendations tailored to your goals."
            )

    st.markdown("<br><br>", unsafe_allow_html=True)

    with st.container(border=True):
        
        # We use st.columns to center the content and control its width
        col1, col2, col3 = st.columns([1, 4, 1]) # The middle column is 4x wider
        
        with col2:
            st.markdown(
                "<h2 style='text-align: center;'>Ready to Explore Your Future?</h2>",
                unsafe_allow_html=True
            )
            st.write(
                """
                <p style='text-align: center;'>
                Our AI assistant is waiting to answer your questions. Get data-driven insights
                and personalized career recommendations in seconds.
                </p>
                """,
                unsafe_allow_html=True
            )

            # A little space before the button
            st.markdown("<br>", unsafe_allow_html=True)

            # This is the main button
            if st.button(
                "Let's Start Chatting Now",
                type="primary",           # This makes the button use your theme's primary color
                use_container_width=True  # This makes the button fill the column width
            ):
                st.switch_page("pages/chat.py")