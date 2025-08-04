import streamlit as st
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Any
from google import genai
from google.genai import types
import pandas as pd
from psycopg_query import query_database
from toolbox import plot_skill_frequency
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the autonomous agent
from test import SkillsAnalyzerChatbot

# Cấu hình trang
st.set_page_config(
    page_title="SkillPath AI - Smart Job Recommendation System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS tùy chỉnh tối ưu cho Streamlit
def load_css():
    st.markdown("""
    <link href="https://cdnjs.cloudflare.co        # Quick suggestions
        st.markdown("#### 🚀 Try These Autonomous Queries:")
        suggestions = [
            "📊 What are the most in-demand skills right now?",
            "📈 Plot Python vs JavaScript demand trends",
            "💰 Show me salary ranges for data science roles",
            "🎯 Analyze AI/ML job market trends",
            "📊 Compare frontend framework popularity",
            "🔍 Find the hottest skills in cybersecurity",
            "📋 What skills should I learn for remote work?",
            "💼 Visualize React job opportunities over time"
        ]font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Import fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif !important;
        }

        .stApp {
            background-color: #f8fafc;
        }

        /* Material Design Cards - Tương thích Streamlit */
        .material-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin: 1rem 0;
        }

        /* Skill Cards tương thích Streamlit */
        .skill-card {
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            background: white;
            padding: 1.5rem;
            margin: 1rem 0;
        }

        .material-button {
            border-radius: 20px;
            font-weight: 500;
            background: #6366f1;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            cursor: pointer;
        }

        /* Gradient Backgrounds đơn giản */
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
        }

        /* Chat Enhancements */
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border-radius: 16px;
            background: white;
            padding: 1rem;
            margin: 1rem 0;
        }

        .chat-message {
            margin: 1rem 0;
            display: flex;
            align-items: flex-start;
        }

        .chat-message.user {
            flex-direction: row-reverse;
        }

        .chat-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 0.5rem;
            flex-shrink: 0;
        }

        .chat-bubble {
            max-width: 70%;
            padding: 0.75rem 1rem;
            border-radius: 16px;
            word-wrap: break-word;
        }

        /* Pathway Steps đơn giản */
        .pathway-step {
            position: relative;
            padding-left: 2rem;
        }
        
        .pathway-step::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 12px;
            width: 8px;
            height: 8px;
            background: #3b82f6;
            border-radius: 50%;
        }
        
        .pathway-step::after {
            content: '';
            position: absolute;
            left: 11px;
            top: 20px;
            width: 2px;
            height: calc(100% - 8px);
            background: #e5e7eb;
        }
        
        .pathway-step:last-child::after {
            display: none;
        }

        /* Category Badges đơn giản */
        .category-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .tech-badge { background: #dbeafe; color: #1e40af; }
        .design-badge { background: #fce7f3; color: #be185d; }
        .business-badge { background: #d1fae5; color: #047857; }
        .data-badge { background: #fef3c7; color: #92400e; }

        .chat-avatar.ai {
            background: #6366f1;
            color: white;
        }

        .chat-avatar.user {
            background: #3b82f6;
            color: white;
        }

        .chat-bubble.ai {
            background: #f1f5f9;
            color: #1e293b;
            border-top-left-radius: 4px;
        }

        .chat-bubble.user {
            background: #6366f1;
            color: white;
            border-top-right-radius: 4px;
        }

        .job-tag {
            background: linear-gradient(45deg, #10b981, #059669);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            margin: 0.25rem;
            display: inline-block;
        }

        .salary-badge {
            background: linear-gradient(45deg, #f59e0b, #d97706);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
        }

        /* Ẩn header và footer mặc định của Streamlit */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        .stDeployButton {
            display: none;
        }
        
        footer {
            display: none;
        }
        
        .stMainBlockContainer {
            padding-top: 0;
        }

        /* Style cho input chat */
        .stTextInput > div > div > input {
            border-radius: 20px;
            border: 2px solid #e2e8f0;
            padding: 0.75rem 1rem;
        }

        .stTextInput > div > div > input:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        /* Style cho button */
        .stButton > button {
            border-radius: 20px;
            background: #6366f1;
            color: white;
            border: none;
            font-weight: 500;
        }

        .stButton > button:hover {
            background: #4f46e5;
        }

        /* Smooth scrolling for anchor links */
        html {
            scroll-behavior: smooth;
        }

        /* Highlight chat section when accessed via button */
        #chat-section {
            scroll-margin-top: 2rem;
        }

        /* Enhanced chat section styling */
        .chat-section-highlight {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(168, 85, 247, 0.05));
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            border: 2px solid rgba(99, 102, 241, 0.1);
        }

        /* Chat message styling fixes */
        .stChatMessage {
            color: #1e293b !important;
        }
        
        .stChatMessage p {
            color: #1e293b !important;
        }
        
        .stChatMessage div {
            color: #1e293b !important;
        }
        
        /* Ensure all text in chat is dark */
        [data-testid="chatAvatarIcon-assistant"] + div,
        [data-testid="chatAvatarIcon-user"] + div {
            color: #1e293b !important;
        }
        
        /* Fix for markdown in chat messages */
        [data-testid="stChatMessageContent"] * {
            color: #1e293b !important;
        }
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

# Chat component
def render_chat_interface():
    st.markdown("""
    <div class="material-card">
        <div class="gradient-bg">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-robot" style="color: white;"></i>
                </div>
                <div>
                    <h3 style="margin: 0; font-weight: 600;">Autonomous Career AI Agent</h3>
                    <p style="margin: 0; font-size: 0.875rem; opacity: 0.9;">
                        <span style="display: inline-block; width: 8px; height: 8px; background: #6ee7b7; border-radius: 50%; margin-right: 0.5rem;" class="animate-pulse-slow"></span>
                        ReAct Framework • Database Analysis • Auto-Visualization
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Khởi tạo session state
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "🤖 Hi! I'm your autonomous AI career assistant powered by advanced ReAct framework. I can help you with:\n\n📊 **Database Analysis**: Real-time job market insights and salary data\n📈 **Skill Visualization**: Interactive plots of skill demand trends\n💼 **Career Guidance**: Personalized recommendations based on current market data\n🎯 **Autonomous Research**: I'll automatically query databases and create visualizations without asking for permission\n\nWhat would you like to explore in the job market today?"
            }
        ]
    
    # Initialize image storage for generated plots
    if 'last_generated_image' not in st.session_state:
        st.session_state.last_generated_image = None
    
    # Initialize the autonomous agent if not already done
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = SkillsAnalyzerChatbot()
        # Configure for web interface
        st.session_state.chatbot.verbose_mode = False  # Disable verbose for cleaner web UI
        st.session_state.chatbot.thought_process_enabled = False  # Disable thought process display for web
        st.session_state.chatbot.max_autonomous_cycles = 5  # Reduce cycles for web environment

# Hiển thị tin nhắn chat với Streamlit components
def display_chat_messages():
    """Display chat messages using proper Streamlit components with image support"""
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            # AI Message
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])
                
                # Check if there are any images to display from the autonomous agent
                if hasattr(st.session_state, 'last_generated_image') and st.session_state.last_generated_image:
                    st.image(st.session_state.last_generated_image, caption="Generated Visualization", use_column_width=True)
                    # Clear the image after displaying to avoid duplication
                    st.session_state.last_generated_image = None
        else:
            # User Message
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])

# Hàm xử lý phản hồi AI sử dụng autonomous agent
def get_ai_response(user_input):
    """Get response from the autonomous SkillsAnalyzerChatbot agent"""
    try:
        # Use the autonomous agent from session state
        chatbot = st.session_state.chatbot
        
        # Reset any previous stored messages
        chatbot.last_print_message = None
        
        # Get response from autonomous agent
        response = chatbot.chat(user_input)
        
        # Check if any visualizations were generated
        import matplotlib.pyplot as plt
        import os
        
        # Look for any newly generated plot files
        plot_files = []
        for file in os.listdir('.'):
            if file.endswith(('.png', '.jpg', '.jpeg', '.svg')) and 'skill' in file.lower():
                plot_files.append(file)
        
        # If plots were generated, store the most recent one
        if plot_files:
            # Sort by modification time and get the most recent
            latest_plot = max(plot_files, key=os.path.getmtime)
            st.session_state.last_generated_image = latest_plot
        
        # Combine agent response with any captured output
        final_response = ""
        
        # Add the main response if available
        if response and response.strip():
            final_response += response.strip()
        
        # Add any captured agent analysis from print_message
        if chatbot.last_print_message:
            if final_response:
                final_response += "\n\n---\n\n"
            final_response += f"📋 **Agent Analysis:** {chatbot.last_print_message}"
        
        # If plots were generated, mention them
        if plot_files:
            if final_response:
                final_response += "\n\n"
            final_response += f"📊 **Generated Visualization:** I've created a visualization based on your request. You can see it displayed above."
        
        # If no response, provide a default message
        if not final_response:
            final_response = "🤖 I've processed your request using my autonomous analysis tools. The results should be displayed above, including any generated visualizations."
        
        return final_response
        
    except Exception as e:
        error_msg = f"❌ **Autonomous Agent Error:** {str(e)}\n\nThe agent encountered an issue while processing your request. Please try rephrasing your question or ask about job market trends, skills analysis, or career insights."
        print(f"Streamlit AI Response Error: {e}")  # For debugging
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
    
    # Chat Interface Header
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: #1e293b;">💬 Chat with Your Autonomous AI Agent</h2>
        <p style="margin: 0.5rem 0 0 0; color: #6b7280;">Real-time database analysis • Automatic visualizations • Career insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create highlighted container for chat section
    st.markdown('<div class="chat-section-highlight">', unsafe_allow_html=True)
    
    # Chat Interface Card
    st.markdown("""
    <div style="background: white; border-radius: 20px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-robot" style="color: white; font-size: 1.25rem;"></i>
            </div>
            <div>
                <h3 style="margin: 0; font-weight: 600; color: #1e293b;">Autonomous Career AI Agent</h3>
                <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 0.5rem;"></span>
                    Online • ReAct Framework • Database Analysis • Auto-Visualization
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Messages Container with fixed height and proper styling
    st.markdown("### 💭 Conversation")
    
    # Create a chat container with margins
    st.markdown("""
    <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)
    
    # Display chat messages in a scrollable container
    chat_container = st.container(height=400)
    with chat_container:
        display_chat_messages()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat Input Section - centered with max width
    st.markdown("""
    <div style="max-width: 800px; margin: 2rem auto;">
    """, unsafe_allow_html=True)
    
    st.markdown("### 💬 Ask Your Question")
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message here...", 
            placeholder="Ask about skills, careers, salaries, job market trends, or request visualizations...",
            height=120,
            label_visibility="collapsed"
        )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            send_button = st.form_submit_button("🚀 Send Message", use_container_width=True, type="primary")
        with col_btn2:
            clear_button = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    # Handle form submissions
    if send_button and user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Get AI response
        with st.spinner("🤖 AI Agent is analyzing and querying database..."):
            ai_response = get_ai_response(user_input)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_response
            })
        
        # Refresh to show new messages
        st.rerun()
    
    if clear_button:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "🤖 Hi! I'm your autonomous AI career assistant. I can analyze job market data, create visualizations, and provide career insights. What would you like to explore?"
            }
        ]
        # Clear any stored images
        st.session_state.last_generated_image = None
        st.rerun()
    
    # Quick Suggestions Section - below the input
    st.markdown("#### 🚀 Quick Suggestions")
    suggestions = [
        "📊 What are the most in-demand skills right now?",
        "📈 Plot Python vs JavaScript demand trends",
        "💰 Show me salary ranges for data science roles",
        "🎯 Analyze AI/ML job market trends",
        "📊 Compare frontend framework popularity",
        "🔍 Find the hottest skills in cybersecurity",
        "📋 What skills should I learn for remote work?",
        "💼 Visualize React job opportunities over time"
    ]
    
    # Display suggestions in a grid
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": suggestion
                })
                ai_response = get_ai_response(suggestion)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": ai_response
                })
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display Generated Visualizations Section
    st.markdown("---")
    st.markdown("### 📊 Generated Visualizations")
    
    # Check for any generated plot files
    import os
    plot_files = []
    for file in os.listdir('.'):
        if file.endswith(('.png', '.jpg', '.jpeg', '.svg')) and any(keyword in file.lower() for keyword in ['skill', 'plot', 'chart', 'graph']):
            plot_files.append(file)
    
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
                            label=f"📥 Download {plot_file}",
                            data=file.read(),
                            file_name=plot_file,
                            mime="image/png",
                            key=f"download_{plot_file}_{i}"
                        )
                except Exception as e:
                    st.error(f"Error displaying {plot_file}: {str(e)}")
    else:
        st.info("📊 No visualizations generated yet. Ask the AI agent to create charts or analyze data to see visualizations here!")
        st.markdown("#### 🚀 Try These Autonomous Queries:")
        suggestions = [
            "� What are the most in-demand skills right now?",
            "📈 Plot Python vs JavaScript demand trends",
            "� Show me salary ranges for data science roles",
            "🎯 Analyze AI/ML job market trends",
            "� Compare frontend framework popularity",
            "🔍 Find the hottest skills in cybersecurity",
            "📋 What skills should I learn for remote work?",
            "💼 Visualize React job opportunities over time"
        ]
        
        for suggestion in suggestions:
            if st.button(suggestion, key=f"suggestion_{suggestion[:10]}", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": suggestion
                })
                ai_response = get_ai_response(suggestion)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": ai_response
                })
                st.rerun()
        
        # Real-time Market Insights Widget
        st.markdown("""
        <div class="material-card" style="margin-top: 1.5rem;">
            <h4 style="margin: 0 0 1rem 0; font-weight: 600; color: #1e293b;">📈 Live Market Data</h4>
            <p style="font-size: 0.75rem; color: #6b7280; margin-bottom: 1rem;">Powered by autonomous database analysis</p>
            <div style="font-size: 0.875rem; color: #374151;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>🤖 AI/ML Skills</span>
                    <span style="color: #10b981; font-weight: 500;">↗ Hot Trend</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>🐍 Python Jobs</span>
                    <span style="color: #10b981; font-weight: 500;">↗ High Demand</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>🏠 Remote Work</span>
                    <span style="color: #3b82f6; font-weight: 500;">→ Stable</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>🔐 Cybersecurity</span>
                    <span style="color: #10b981; font-weight: 500;">↗ Growing</span>
                </div>
            </div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 0.75rem; color: #6b7280; margin: 0;">💡 Ask the AI agent for detailed analysis and visualizations!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Close the chat section highlight container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
