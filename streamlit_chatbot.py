import streamlit as st
import os
import sys
import random
import re
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Any
from io import BytesIO
from google import genai
from google.genai import types
import pandas as pd
from tools.psycopg_query import query_database
from tools.toolbox import plot_skill_frequency
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the autonomous agent
try:
    from chatbot_class import SkillsAnalyzerChatbot
except ImportError:
    try:
        from chatbot_class.skills_analyzer_chatbot import SkillsAnalyzerChatbot
    except ImportError:
        st.error("❌ Could not import SkillsAnalyzerChatbot. Please check the imports.")
        st.stop()

# Cấu hình trang
st.set_page_config(
    page_title="SkillPath AI - Smart Job Recommendation System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS tùy chỉnh tối ưu cho Streamlit
def load_css():
    """Load CSS from external file for better organization"""
    # Load external CSS file
    css_file_path = os.path.join(os.path.dirname(__file__), "static", "styles.css")
    
    # Default CSS if file doesn't exist
    default_css = """
    .material-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    .gradient-bg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    
    .material-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .material-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .skill-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .skill-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .animate-pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    """
    
    try:
        with open(css_file_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    except FileNotFoundError:
        css_content = default_css
        
    st.markdown(f"""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
    {css_content}
    </style>
    """, unsafe_allow_html=True)

# Header component tối ưu cho Streamlit
def render_header():
    st.html("""
    <div style="background: white; padding: 1rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-graduation-cap" style="color: white; font-size: 1.25rem;"></i>
                    </div>
                    <div>
                        <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #1e293b;">SkillPath AI</h1>
                        <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">Your Future Skills Navigator</p>
                    </div>
                </div>
                <nav style="display: flex; gap: 2rem; align-items: center;">
                    <a href="#skills" style="color: #6b7280; text-decoration: none; font-weight: 500;">Skills</a>
                    <a href="#pathways" style="color: #6b7280; text-decoration: none; font-weight: 500;">Pathways</a>
                    <a href="#insights" style="color: #6b7280; text-decoration: none; font-weight: 500;">Insights</a>
                    <div style="position: relative; padding: 0.5rem; color: #6b7280;">
                        <i class="fas fa-bell" style="font-size: 1.125rem;"></i>
                        <span style="position: absolute; top: -4px; right: -4px; width: 20px; height: 20px; background: #ef4444; color: white; font-size: 0.75rem; border-radius: 50%; display: flex; align-items: center; justify-content: center;">3</span>
                    </div>
                    <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #3b82f6, #14b8a6); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-user" style="color: white; font-size: 0.875rem;"></i>
                    </div>
                </nav>
            </div>
        </div>
    </div>
    """)

# Skills Recommendation Component tối ưu cho Streamlit
def render_skills_section():
    st.html("""
    <section id="skills" style="margin-bottom: 3rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <div>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">Recommended Skills</h2>
                <p style="margin: 0.5rem 0 0 0; color: #6b7280;">Build the skills you need for tomorrow's jobs</p>
            </div>
            <div style="color: #6366f1; font-weight: 500;">
                View All Skills <i class="fas fa-arrow-right" style="margin-left: 0.5rem;"></i>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
            <!-- Python Skill Card -->
            <div class="skill-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #3776ab, #ffd343); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                            <i class="fab fa-python" style="color: white; font-size: 1.5rem;"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">Python Programming</h3>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem;">
                                <span class="category-badge tech-badge">Technology</span>
                                <span style="color: #10b981; font-size: 0.875rem; font-weight: 500;">95% Job Match</span>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 60px; height: 60px; background: #e5e7eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                            <div style="width: 40px; height: 40px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 0.75rem; font-weight: 600; color: #3b82f6;">80%</span>
                            </div>
                        </div>
                        <span style="font-size: 0.75rem; color: #6b7280;">Market Demand</span>
                    </div>
                </div>
                
                <p style="color: #374151; margin-bottom: 1rem; font-size: 0.875rem;">
                    Essential for data science, web development, and AI. High demand across industries with excellent career prospects.
                </p>
                
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Avg. Salary</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">$85K - $150K</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Learning Time</span>
                        <span style="font-size: 0.875rem; font-weight: 600;">3-6 months</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Job Openings</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">15,000+</span>
                    </div>
                </div>
                
                <div style="display: flex; gap: 0.75rem;">
                    <button style="flex: 1; background: #6366f1; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
                        Start Learning
                    </button>
                    <button style="background: #f3f4f6; color: #374151; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-bookmark"></i>
                    </button>
                </div>
            </div>

            <!-- Data Science Skill Card -->
            <div class="skill-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-chart-line" style="color: white; font-size: 1.5rem;"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">Data Science</h3>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem;">
                                <span class="category-badge data-badge">Data</span>
                                <span style="color: #10b981; font-size: 0.875rem; font-weight: 500;">92% Job Match</span>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 60px; height: 60px; background: #e5e7eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                            <div style="width: 40px; height: 40px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 0.75rem; font-weight: 600; color: #f59e0b;">70%</span>
                            </div>
                        </div>
                        <span style="font-size: 0.75rem; color: #6b7280;">Market Demand</span>
                    </div>
                </div>
                
                <p style="color: #374151; margin-bottom: 1rem; font-size: 0.875rem;">
                    Turn data into insights. Master statistics, machine learning, and data visualization for high-impact roles.
                </p>
                
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Avg. Salary</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">$95K - $180K</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Learning Time</span>
                        <span style="font-size: 0.875rem; font-weight: 600;">6-12 months</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Job Openings</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">8,500+</span>
                    </div>
                </div>
                
                <div style="display: flex; gap: 0.75rem;">
                    <button style="flex: 1; background: #6366f1; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
                        Start Learning
                    </button>
                    <button style="background: #f3f4f6; color: #374151; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-bookmark"></i>
                    </button>
                </div>
            </div>

            <!-- UX Design Skill Card -->
            <div class="skill-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8b5cf6, #ec4899); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-palette" style="color: white; font-size: 1.5rem;"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">UX Design</h3>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem;">
                                <span class="category-badge design-badge">Design</span>
                                <span style="color: #10b981; font-size: 0.875rem; font-weight: 500;">88% Job Match</span>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 60px; height: 60px; background: #e5e7eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                            <div style="width: 40px; height: 40px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 0.75rem; font-weight: 600; color: #8b5cf6;">60%</span>
                            </div>
                        </div>
                        <span style="font-size: 0.75rem; color: #6b7280;">Market Demand</span>
                    </div>
                </div>
                
                <p style="color: #374151; margin-bottom: 1rem; font-size: 0.875rem;">
                    Create user-centered designs that drive business results. High-growth field with creative and technical challenges.
                </p>
                
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Avg. Salary</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">$75K - $140K</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Learning Time</span>
                        <span style="font-size: 0.875rem; font-weight: 600;">4-8 months</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Job Openings</span>
                        <span style="font-size: 0.875rem; font-weight: 600; color: #059669;">6,200+</span>
                    </div>
                </div>
                
                <div style="display: flex; gap: 0.75rem;">
                    <button style="flex: 1; background: #6366f1; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
                        Start Learning
                    </button>
                    <button style="background: #f3f4f6; color: #374151; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-bookmark"></i>
                    </button>
                </div>
            </div>
        </div>
    </section>
    """)

# Learning Pathways Component tối ưu cho Streamlit
def render_learning_pathways():
    st.html("""
    <section id="pathways" style="margin-bottom: 3rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <div>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">Learning Pathways</h2>
                <p style="margin: 0.5rem 0 0 0; color: #6b7280;">Structured learning paths to reach your career goals</p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem;">
            <!-- Frontend Developer Pathway -->
            <div class="material-card">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="width: 56px; height: 56px; background: linear-gradient(135deg, #3b82f6, #06b6d4); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-code" style="color: white; font-size: 1.5rem;"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">Frontend Developer</h3>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">6-month comprehensive program</p>
                    </div>
                    <div style="margin-left: auto;">
                        <span style="background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500;">Beginner</span>
                    </div>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">HTML & CSS Fundamentals</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">4 weeks • Build responsive layouts</p>
                    </div>
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">JavaScript Essentials</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">6 weeks • Interactive programming</p>
                    </div>
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">React Development</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">8 weeks • Modern UI development</p>
                    </div>
                    <div class="pathway-step">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">Portfolio & Job Prep</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">4 weeks • Professional projects</p>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="flex: 1; background: #e5e7eb; border-radius: 4px; height: 8px; margin-right: 1rem;">
                        <div style="background: #3b82f6; height: 100%; width: 45%; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 0.875rem; color: #6b7280;">45% Complete</span>
                </div>
                
                <button style="width: 100%; background: #6366f1; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
                    Continue Learning
                </button>
            </div>

            <!-- Data Scientist Pathway -->
            <div class="material-card">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="width: 56px; height: 56px; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-chart-bar" style="color: white; font-size: 1.5rem;"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">Data Scientist</h3>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">9-month intensive program</p>
                    </div>
                    <div style="margin-left: auto;">
                        <span style="background: #fef3c7; color: #92400e; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500;">Intermediate</span>
                    </div>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">Python & Statistics</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">6 weeks • Foundation building</p>
                    </div>
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">Data Analysis & Pandas</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">5 weeks • Data manipulation</p>
                    </div>
                    <div class="pathway-step" style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">Machine Learning</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">10 weeks • ML algorithms</p>
                    </div>
                    <div class="pathway-step">
                        <h4 style="margin: 0 0 0.25rem 0; font-weight: 500;">Portfolio Projects</h4>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">6 weeks • Real-world projects</p>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="flex: 1; background: #e5e7eb; border-radius: 4px; height: 8px; margin-right: 1rem;">
                        <div style="background: #f59e0b; height: 100%; width: 25%; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 0.875rem; color: #6b7280;">25% Complete</span>
                </div>
                
                <button style="width: 100%; background: #6366f1; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
                    Start Pathway
                </button>
            </div>
        </div>
    </section>
    """)

# Progress Dashboard Component
def render_progress_dashboard():
    st.html("""
    <section style="margin-bottom: 3rem;">
        <h3 style="margin: 0 0 2rem 0; font-size: 2rem; font-weight: 700; color: #1e293b;">Your Learning Progress</h3>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
            <div style="background: white; border-radius: 16px; padding: 1.5rem; text-center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="width: 48px; height: 48px; background: #dbeafe; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                    <i class="fas fa-trophy" style="color: #3b82f6; font-size: 1.25rem;"></i>
                </div>
                <h4 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">8</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Skills Completed</p>
            </div>
            
            <div style="background: white; border-radius: 16px; padding: 1.5rem; text-center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="width: 48px; height: 48px; background: #d1fae5; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                    <i class="fas fa-clock" style="color: #10b981; font-size: 1.25rem;"></i>
                </div>
                <h4 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">42</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Hours This Week</p>
            </div>
            
            <div style="background: white; border-radius: 16px; padding: 1.5rem; text-center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="width: 48px; height: 48px; background: #fce7f3; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                    <i class="fas fa-certificate" style="color: #8b5cf6; font-size: 1.25rem;"></i>
                </div>
                <h4 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">3</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Certificates Earned</p>
            </div>
            
            <div style="background: white; border-radius: 16px; padding: 1.5rem; text-center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="width: 48px; height: 48px; background: #fef3c7; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                    <i class="fas fa-fire" style="color: #f59e0b; font-size: 1.25rem;"></i>
                </div>
                <h4 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">15</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Day Streak</p>
            </div>
        </div>
    </section>
    """)

# Career Insights Component
def render_career_insights():
    st.html("""
    <section id="insights" style="margin-bottom: 3rem;">
        <h3 style="margin: 0 0 2rem 0; font-size: 2rem; font-weight: 700; color: #1e293b;">Career Market Insights</h3>
        
        <div style="background: white; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem;">
                <div>
                    <h4 style="margin: 0 0 1.5rem 0; font-size: 1.25rem; font-weight: 600; color: #1e293b;">Trending Skills This Month</h4>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span style="color: #374151; font-weight: 500;">Artificial Intelligence</span>
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <div style="width: 80px; background: #e5e7eb; border-radius: 9999px; height: 8px;">
                                    <div style="background: #10b981; height: 100%; width: 85%; border-radius: 9999px;"></div>
                                </div>
                                <span style="font-size: 0.875rem; color: #10b981; font-weight: 600;">+25%</span>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span style="color: #374151; font-weight: 500;">Cybersecurity</span>
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <div style="width: 80px; background: #e5e7eb; border-radius: 9999px; height: 8px;">
                                    <div style="background: #3b82f6; height: 100%; width: 78%; border-radius: 9999px;"></div>
                                </div>
                                <span style="font-size: 0.875rem; color: #3b82f6; font-weight: 600;">+20%</span>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span style="color: #374151; font-weight: 500;">Blockchain</span>
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <div style="width: 80px; background: #e5e7eb; border-radius: 9999px; height: 8px;">
                                    <div style="background: #8b5cf6; height: 100%; width: 65%; border-radius: 9999px;"></div>
                                </div>
                                <span style="font-size: 0.875rem; color: #8b5cf6; font-weight: 600;">+18%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 1.5rem 0; font-size: 1.25rem; font-weight: 600; color: #1e293b;">Career Opportunities</h4>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="padding: 1rem; background: #dbeafe; border-radius: 12px;">
                            <h5 style="margin: 0; font-weight: 600; color: #1e40af;">Software Engineer</h5>
                            <p style="margin: 0; font-size: 0.875rem; color: #1d4ed8; margin-top: 0.25rem;">High demand • $95k average salary</p>
                        </div>
                        <div style="padding: 1rem; background: #d1fae5; border-radius: 12px;">
                            <h5 style="margin: 0; font-weight: 600; color: #047857;">UX Designer</h5>
                            <p style="margin: 0; font-size: 0.875rem; color: #059669; margin-top: 0.25rem;">Growing field • $78k average salary</p>
                        </div>
                        <div style="padding: 1rem; background: #fce7f3; border-radius: 12px;">
                            <h5 style="margin: 0; font-weight: 600; color: #be185d;">Data Analyst</h5>
                            <p style="margin: 0; font-size: 0.875rem; color: #be185d; margin-top: 0.25rem;">Strong growth • $72k average salary</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """)

# Chat component with compact settings
def render_chat_interface():
    # Chat Interface Header
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">💬 Chat with Your AI Skills Analyzer</h2>
        <p style="margin: 0.5rem 0 0 0; color: #6b7280;">Real-time database analysis • Automatic visualizations • Career insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Compact Settings Section
    with st.expander("⚙️ Chat Settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            debug_mode = st.checkbox(
                "🔍 Debug Mode",
                value=st.session_state.get('show_debug_info', False),
                help="Show AI thinking process"
            )
            if debug_mode != st.session_state.get('show_debug_info', False):
                st.session_state.chatbot.set_debug_mode(debug_mode)
        
        with col2:
            if st.button("🔄 New Chat", help="Start fresh conversation", key="new_chat_btn"):
                st.session_state.chatbot.new_chat()
                st.rerun()
        
        with col3:
            # Show session stats as text instead of button
            stats = st.session_state.chatbot.get_session_stats()
            st.metric("💬 Messages", stats.get('total_messages', 0))

    # Chat Status Indicator
    st.markdown("""
    <div class="material-card" style="margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-robot" style="color: white;"></i>
            </div>
            <div>
                <h4 style="margin: 0; font-weight: 600; color: #1e293b;">AI Skills Analyzer</h4>
                <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 0.5rem;" class="animate-pulse"></span>
                    Ready to analyze job market data
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Messages Container with increased height
    st.markdown("### 💭 Conversation")
    chat_container = st.container(height=600)  # Increased from 400 to 600
    with chat_container:
        display_chat_messages()
    
    # Chat Input Section
    st.markdown("### 💬 Ask Your Question")
    
    # Chat input with form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message here...", 
            placeholder="Ask about skills, careers, salaries, job market trends, or request visualizations...",
            height=100,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([4, 1])
        with col1:
            send_button = st.form_submit_button("🚀 Send Message", use_container_width=True, type="primary")
        with col2:
            clear_button = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    # Handle form submissions
    if send_button and user_input:
        # Add user message to conversation history first
        st.session_state.conversation_history.append(f"User: {user_input}")
        
        # Process and get AI response
        with st.spinner("🤔 Analyzing your request..."):
            response = st.session_state.chatbot.chat(user_input)
            if response and response.strip():
                # Don't add again since chatbot.chat() already adds to history
                pass
            else:
                st.session_state.conversation_history.append("Assistant: I'm sorry, I couldn't generate a response. Please try again.")
        
        st.rerun()
    
    if clear_button:
        # Clear button only clears the input form, not conversation
        st.rerun()
    
    # Quick Suggestions
    st.markdown("#### 🚀 Quick Suggestions")
    suggestions = [
        "📊 What are the most in-demand skills?",
        "📈 Show Python vs JavaScript trends",
        "💰 Data science salary ranges",
        "🎯 AI/ML job market analysis",
        "📊 Frontend framework popularity",
        "🔍 Cybersecurity skills demand",
        "📋 Remote work skill requirements",
        "💼 React job opportunities"
    ]
    
    # Display suggestions in grid
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    # Add user message to conversation history first
                    st.session_state.conversation_history.append(f"User: {suggestion}")
                    
                    # Process and get AI response
                    with st.spinner("🤔 Analyzing your request..."):
                        response = st.session_state.chatbot.chat(suggestion)
                        if not (response and response.strip()):
                            st.session_state.conversation_history.append("Assistant: I'm sorry, I couldn't generate a response. Please try again.")
                    
                    st.rerun()# Enhanced Streamlit Skills Analyzer Chatbot Class  
class StreamlitSkillsAnalyzerChatbot:
    def __init__(self):
        if not API_KEY:
            st.error("❌ GEMINI_API_KEY not found in environment variables")
            st.stop()
        
        # Initialize the main chatbot class with verbose mode for detailed output
        self.chatbot = SkillsAnalyzerChatbot(verbose=True)
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'session_active' not in st.session_state:
            st.session_state.session_active = True
        if 'show_debug_info' not in st.session_state:
            st.session_state.show_debug_info = True

    def display_message(self, message: str) -> None:
        """
        Displays a message in Streamlit chat interface.
        """
        st.chat_message("assistant").write(message)

    def end_session(self) -> None:
        """
        Ends the chatbot session by setting session_active to False.
        """
        st.session_state.session_active = False
        st.chat_message("assistant").write("👋 Session ended. Refresh the page to start a new conversation!")

    def chat(self, user_message: str) -> str:
        """
        Main chat function using the SkillsAnalyzerChatbot class with detailed UI.
        """
        try:
            # Don't add user message here since it's already added in the UI handler
            # Process the chat request
            response = self.chatbot.chat(user_message)
            
            # Add assistant response to conversation history
            st.session_state.conversation_history.append(f"Assistant: {response}")
            
            return self._clean_response_from_debug(response)
            
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            st.error(error_msg)
            st.session_state.conversation_history.append(f"Assistant: {error_msg}")
            return error_msg
    
    def _clean_response_from_debug(self, response: str) -> str:
        """
        Remove debug information from response to get clean user-facing content.
        """
        if not response:
            return "I'm sorry, I couldn't generate a response. Please try again."
            
        lines = response.split('\n')
        clean_lines = []
        skip_line = False
        
        for line in lines:
            # Skip debug patterns
            if any(pattern in line for pattern in ['🧠 **THINKING:', '🔧 **TOOL', '📊 **TOOL', 
                                                  '[Gemini Part Fields]', '💬 **RESPONSE:', '-' * 20]):
                skip_line = True
                continue
            
            if not skip_line and line.strip():
                clean_lines.append(line)
        
        # Join and clean up extra whitespace
        clean_response = '\n'.join(clean_lines).strip()
        
        # Remove any remaining debug patterns
        clean_response = re.sub(r'🧠 \*\*ANALYSIS:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        clean_response = re.sub(r'🧠 \*\*PLAN:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        
        return clean_response.strip()
    
    def _display_debug_output(self, debug_output: str) -> None:
        """
        Display debug output in a structured way for Streamlit.
        """
        lines = debug_output.strip().split('\n')
        
        for line in lines:
            if line.strip().startswith('🧠'):
                st.info(line)
            elif line.strip().startswith('🔧'):
                st.warning(line)
            elif line.strip().startswith('📊'):
                st.success(line)
            else:
                st.text(line)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Toggle debug information display"""
        st.session_state.show_debug_info = enabled
        if hasattr(self.chatbot, 'set_verbose_mode'):
            self.chatbot.set_verbose_mode(enabled)
        else:
            self.chatbot.verbose = enabled
    
    def new_chat(self) -> None:
        """Start a new chat session"""
        if hasattr(self.chatbot, 'new_chat'):
            self.chatbot.new_chat()
        elif hasattr(self.chatbot, 'reset_conversation'):
            self.chatbot.reset_conversation()
        else:
            # Reinitialize chatbot if reset method doesn't exist
            self.chatbot = SkillsAnalyzerChatbot(verbose=True)
        st.session_state.conversation_history = []
        st.session_state.session_active = True
    
    def get_session_stats(self) -> dict:
        """Get current session statistics"""
        if hasattr(self.chatbot, 'get_session_stats'):
            return self.chatbot.get_session_stats()
        else:
            return {
                'total_messages': len(st.session_state.conversation_history),
                'session_active': st.session_state.session_active
            }
    
    def set_thinking_budget(self, budget: int) -> None:
        """Set thinking budget for the chatbot"""
        if hasattr(self.chatbot, 'set_thinking_budget'):
            self.chatbot.set_thinking_budget(budget)
    
    def set_generation_preset(self, preset: str) -> None:
        """Set generation preset for the chatbot"""
        if hasattr(self.chatbot, 'set_generation_preset'):
            self.chatbot.set_generation_preset(preset)
    
    def display_conversation_with_debug(self) -> None:
        """Display conversation history with enhanced formatting"""
        for i, message in enumerate(st.session_state.conversation_history):
            if message.startswith("User: "):
                # User message with right alignment
                user_text = message[6:]  # Remove "User: " prefix
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
                    <div style="background: #e3f2fd; padding: 0.75rem 1rem; border-radius: 18px 18px 4px 18px; max-width: 70%; color: #1565c0;">
                        <strong>You:</strong><br>{user_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif message.startswith("Assistant: "):
                # Assistant message with left alignment
                response_text = message[11:]  # Remove "Assistant: " prefix
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                    <div style="background: #f5f5f5; padding: 0.75rem 1rem; border-radius: 18px 18px 18px 4px; max-width: 85%; color: #333;">
                        <strong>🤖 AI Assistant:</strong><br>
                """, unsafe_allow_html=True)
                
                if st.session_state.show_debug_info:
                    self._display_structured_response(response_text)
                else:
                    # Filter out debug info for clean display
                    clean_response = self._clean_response_from_debug(response_text)
                    st.markdown(clean_response)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
    
    def _display_structured_response(self, response_text: str) -> None:
        """Display structured response with different sections"""
        # First display the main response
        clean_response = self._clean_response_from_debug(response_text)
        if clean_response.strip():
            st.markdown(clean_response)
        
        # Then display debug sections in expandable format
        lines = response_text.split('\n')
        thinking_content = []
        tool_content = []
        result_content = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'THINKING:' in line or '🧠' in line:
                current_section = "thinking"
                continue
            elif 'TOOL' in line and ('🔧' in line or '📊' in line):
                current_section = "tool" if '🔧' in line else "result"
                continue
            elif line and current_section == "thinking":
                thinking_content.append(line)
            elif line and current_section == "tool":
                tool_content.append(line)
            elif line and current_section == "result":
                result_content.append(line)
        
        # Render sections with proper expandable format
        if thinking_content:
            with st.expander("🧠 View AI Thinking Process", expanded=False):
                for line in thinking_content:
                    if line.strip():
                        st.text(line)
        
        if tool_content:
            with st.expander("🔧 View Tool Usage", expanded=False):
                for line in tool_content:
                    if line.strip():
                        st.code(line)
        
        if result_content:
            with st.expander("📊 View Tool Results", expanded=False):
                for line in result_content:
                    if line.strip():
                        if line.startswith('{') or line.startswith('['):
                            try:
                                import json
                                st.json(json.loads(line))
                            except:
                                st.text(line)
                        else:
                            st.text(line)
    
    def _render_section(self, section_type: str, content: list) -> None:
        """Render a specific section with appropriate styling"""
        import time
        unique_key = f"{section_type}_{int(time.time() * 1000000)}"
        
        if section_type == "thinking":
            with st.expander("🧠 **Thinking Process**", expanded=False, key=f"thinking_{unique_key}"):
                for line in content:
                    st.text(line)
        elif section_type == "tool":
            with st.expander("🔧 **Tool Usage**", expanded=False, key=f"tool_{unique_key}"):
                for line in content:
                    st.code(line)
        elif section_type == "result":
            with st.expander("📊 **Tool Results**", expanded=False, key=f"result_{unique_key}"):
                for line in content:
                    st.json(line) if line.startswith('{') else st.text(line)

# Khởi tạo session state
def init_session_state():
    # Initialize chatbot if not already done
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = StreamlitSkillsAnalyzerChatbot()
    
    # Initialize messages for compatibility (optional)
    if 'messages' not in st.session_state:
        st.session_state.messages = []

# Hiển thị tin nhắn chat với enhanced chatbot system
def display_chat_messages():
    """Display chat messages using enhanced chatbot with debug support"""
    if hasattr(st.session_state, 'chatbot') and hasattr(st.session_state.chatbot, 'display_conversation_with_debug'):
        # Use the enhanced display method from chatbot class
        st.session_state.chatbot.display_conversation_with_debug()
    else:
        # Fallback to simple display
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message["content"])

# Hàm xử lý phản hồi AI sử dụng enhanced chatbot
def get_ai_response(user_input):
    """Get response from the enhanced SkillsAnalyzerChatbot"""
    try:
        chatbot = st.session_state.chatbot
        response = chatbot.chat(user_input)
        
        # Check for generated visualizations
        import os
        plot_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg', '.svg')) 
                     and any(keyword in f.lower() for keyword in ['skill', 'plot', 'chart', 'graph'])]
        
        if plot_files:
            # Get the most recent plot
            latest_plot = max(plot_files, key=os.path.getmtime)
            response += f"\n\n📊 **Visualization Generated:** {latest_plot}"
        
        return response
        
    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}\n\nPlease try rephrasing your question."
        return error_msg

# Main app với enhanced features từ genai.html
def main():
    load_css()
    init_session_state()
    
    # Header
    render_header()
    
    # Hero Section
    st.markdown("""
    <div class="gradient-bg" style="text-align: center; margin-bottom: 3rem;">
        <h2 style="margin: 0; font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem;">Discover Your Future Skills</h2>
        <p style="margin: 0; font-size: 1.25rem; opacity: 0.9; margin-bottom: 2rem;">Chat with our autonomous AI agent that automatically analyzes job market data, creates visualizations, and provides insights using advanced ReAct framework</p>
        <a href="#chat-section" style="display: inline-block; text-decoration: none;">
            <button class="material-button" style="font-size: 1.125rem; padding: 1rem 2rem; cursor: pointer;" onclick="document.getElementById('chat-section').scrollIntoView({behavior: 'smooth'});">
                <i class="fas fa-comments" style="margin-right: 0.5rem;"></i>Start Career Chat
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Skills Section
    render_skills_section()
    
    # Learning Pathways
    render_learning_pathways()
    
    # Progress Dashboard
    render_progress_dashboard()
    
    # Career Insights
    render_career_insights()
    
    # Chat Interface Section
    st.markdown("---")
    st.markdown('<div id="chat-section"></div>', unsafe_allow_html=True)
    
    # Render the enhanced chat interface with compact settings
    render_chat_interface()
    
    # Display Generated Visualizations Section
    st.markdown("---")
    st.markdown("### 📊 Generated Visualizations")
    
    # Check for any generated plot files
    plot_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg', '.svg')) 
                  and any(keyword in f.lower() for keyword in ['skill', 'plot', 'chart', 'graph'])]
    
    if plot_files:
        # Sort by modification time and display the most recent ones
        plot_files.sort(key=os.path.getmtime, reverse=True)
        
        # Display up to 3 most recent plots
        cols = st.columns(min(len(plot_files[:3]), 3))
        for i, plot_file in enumerate(plot_files[:3]):
            with cols[i]:
                try:
                    st.image(plot_file, caption=f"Generated: {plot_file}", use_column_width=True)
                    
                    # Add download button
                    with open(plot_file, "rb") as file:
                        st.download_button(
                            label=f"📥 Download",
                            data=file.read(),
                            file_name=plot_file,
                            mime="image/png",
                            key=f"download_{plot_file}_{i}"
                        )
                except Exception as e:
                    st.error(f"Error displaying {plot_file}: {str(e)}")
    else:
        st.info("📊 No visualizations generated yet. Ask the AI agent to create charts and analyze data!")

if __name__ == "__main__":
    main()
