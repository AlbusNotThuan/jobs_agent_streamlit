#!/usr/bin/env python3
"""
Toolbox for LinkedIn Jobs Skills Analyzer Agent

This module provides a collection of standalone functions that act as tools for the AI agent.
The tools are designed to work together to facilitate a multi-step, conversational analysis.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import os
import sys

# Ensure the correct path is set to import from the parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from psycopg_query import query_database


# --- "GETTER" TOOLS: For discovering top items ---

def get_top_skills(n: int = 10) -> Dict[str, Any]:
    """
    Retrieves the top N most in-demand skills based on job posting frequency over the last 4 weeks.

    This tool provides a simple list of top skills and their mention counts. It is ideal for
    an initial discovery step. The agent should present this information as a list and then
    suggest using the 'plot_skill_trend' tool as a follow-up action to visualize the trends.
    This tool does NOT produce a chart.

    Args:
        n (int): The number of top skills to retrieve (e.g., 5, 10, 15). Defaults to 10.

    Returns:
        Dict[str, Any]: A dictionary containing a list of the top skills and their frequencies.
    """
    print(f"🛠️ Executing get_top_skills for top {n}")
    try:
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        sql_query = """
        SELECT s.name, COUNT(DISTINCT j.job_id) as frequency
        FROM skill s
        JOIN job_skill js ON s.skill_id = js.skill_id
        JOIN job j ON js.job_id = j.job_id
        WHERE j.posted_date >= %s
        GROUP BY s.name
        ORDER BY frequency DESC
        LIMIT %s;
        """
        result = query_database(sql_query, [four_weeks_ago, n])

        if not result:
            return {"success": False, "message": f"Could not retrieve top {n} skills."}

        # Format data as a list of dictionaries for the agent to easily parse
        top_skills_data = [{'skill': row[0], 'frequency': row[1]} for row in result]

        return {
            "success": True,
            "message": f"Successfully retrieved the top {n} skills.",
            "data": top_skills_data
        }
    except Exception as e:
        print(f"❌ Error in get_top_skills: {e}")
        return {"success": False, "message": f"An error occurred: {e}"}


def get_top_job_expertises(n: int = 10) -> Dict[str, Any]:
    """
    Retrieves the top N most frequent job expertises from postings over the last 4 weeks.

    This tool uses the standardized 'job_expertise' column for accurate results. It provides a
    simple list of top roles and their posting counts. The agent should present this as a list
    and then suggest using the 'plot_job_trend' tool as a follow-up action.
    This tool does NOT produce a chart.

    Args:
        n (int): The number of top job expertises to retrieve. Defaults to 10.

    Returns:
        Dict[str, Any]: A dictionary containing a list of the top roles and their frequencies.
    """
    print(f"🛠️ Executing get_top_job_expertises for top {n}")
    try:
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        sql_query = """
        SELECT job_expertise, COUNT(job_id) as frequency
        FROM job
        WHERE posted_date >= %s AND job_expertise IS NOT NULL
        GROUP BY job_expertise
        ORDER BY frequency DESC
        LIMIT %s;
        """
        result = query_database(sql_query, [four_weeks_ago, n])

        if not result:
            return {"success": False, "message": f"Could not retrieve top {n} job expertises."}
            
        top_jobs_data = [{'job_expertise': row[0], 'frequency': row[1]} for row in result]

        return {
            "success": True,
            "message": f"Successfully retrieved the top {n} job expertises.",
            "data": top_jobs_data
        }
    except Exception as e:
        print(f"❌ Error in get_top_job_expertises: {e}")
        return {"success": False, "message": f"An error occurred: {e}"}


# --- "PLOTTING" TOOLS: For visualizing trends ---

def plot_skill_trend(skills: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Plots the daily demand trend of one or more skills over the last 4 weeks.

    This tool is for visualizing and comparing the recent popularity of skills. It returns
    data formatted for a line chart. The agent should use the returned 'summary' for its
    analysis and must not output the raw chart data.

    Args:
        skills (Union[str, List[str]]): A single skill or a list of skills to analyze.
    """
    if isinstance(skills, str):
        skills = [skills]
    
    print(f"🛠️ Executing plot_skill_trend for: {skills}")
    try:
        # ... (Implementation from previous step remains the same)
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        skill_patterns = [f"%{skill}%" for skill in skills]
        sql_query = """
        SELECT DATE(j.posted_date) as post_date, s.name as item_name, COUNT(DISTINCT j.job_id) as frequency
        FROM skill s JOIN job_skill js ON s.skill_id = js.skill_id JOIN job j ON js.job_id = j.job_id
        WHERE s.name ILIKE ANY(ARRAY[{}]) AND j.posted_date >= %s
        GROUP BY DATE(j.posted_date), s.name ORDER BY post_date;
        """.format(', '.join(['%s'] * len(skill_patterns)))
        result = query_database(sql_query, skill_patterns + [four_weeks_ago])
        if not result: return {"success": False, "message": f"No data found for skills: {skills}."}
        df = pd.DataFrame(result, columns=['post_date', 'item_name', 'frequency'])
        chart_df = df.pivot(index='post_date', columns='item_name', values='frequency').fillna(0)
        summary = {"analysis_type": "Skill Demand Trend", "items_analyzed": skills, "total_mentions": int(df['frequency'].sum()), "peak_skill": df.groupby('item_name')['frequency'].sum().idxmax()}
        data_dict = chart_df.to_dict('split')
        data_dict['index'] = [pd.to_datetime(ts).isoformat() for ts in data_dict['index']]
        return {"success": True, "message": "Successfully analyzed skill trend.", "chart_data": data_dict, "chart_type": "line_chart", "summary": summary}
    except Exception as e:
        return {"success": False, "message": str(e)}


def plot_job_trend(job_expertises: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Plots the daily hiring trend of one or more standardized job roles over the last 4 weeks.

    This tool uses the clean 'job_expertise' column to track and compare hiring trends.
    The agent should use the returned 'summary' for analysis and must not output raw chart data.

    Args:
        job_expertises (Union[str, List[str]]): A single standardized job role or a list of them.
    """
    if isinstance(job_expertises, str):
        job_expertises = [job_expertises]

    print(f"🛠️ Executing plot_job_trend for: {job_expertises}")
    try:
        # ... (Implementation from previous step remains the same)
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        expertise_patterns = [f"%{expertise}%" for expertise in job_expertises]
        sql_query = """
        SELECT DATE(posted_date) as post_date, job_expertise as item_name, COUNT(job_id) as frequency
        FROM job
        WHERE job_expertise ILIKE ANY(ARRAY[{}]) AND posted_date >= %s
        GROUP BY DATE(posted_date), job_expertise ORDER BY post_date;
        """.format(', '.join(['%s'] * len(expertise_patterns)))
        result = query_database(sql_query, expertise_patterns + [four_weeks_ago])
        if not result: return {"success": False, "message": f"No data found for job expertises: {job_expertises}."}
        df = pd.DataFrame(result, columns=['post_date', 'item_name', 'frequency'])
        chart_df = df.pivot(index='post_date', columns='item_name', values='frequency').fillna(0)
        summary = {"analysis_type": "Job Hiring Trend", "items_analyzed": job_expertises, "total_postings": int(df['frequency'].sum()), "peak_role": df.groupby('item_name')['frequency'].sum().idxmax()}
        data_dict = chart_df.to_dict('split')
        data_dict['index'] = [pd.to_datetime(ts).isoformat() for ts in data_dict['index']]
        return {"success": True, "message": "Successfully analyzed job trend.", "chart_data": data_dict, "chart_type": "line_chart", "summary": summary}
    except Exception as e:
        return {"success": False, "message": str(e)}


# --- Utility/Demo Tool ---
def create_dummy_line_chart() -> Dict[str, Any]:
    """Creates a line chart with dummy data for demonstration purposes."""
    # ... (Implementation is unchanged)
    print("🛠️ Generating dummy line chart...")
    try:
        date_range = pd.to_datetime(pd.date_range(end=datetime.now(), periods=30, freq='D'))
        chart_data_df = pd.DataFrame(
            (abs(pd.np.random.randn(30, 3).cumsum(axis=0)) + 10),
            index=date_range,
            columns=["Alpha Trend", "Beta Trend", "Gamma Trend"]
        )
        data_dict = chart_data_df.to_dict('split')
        data_dict['index'] = [ts.isoformat() for ts in data_dict['index']]
        summary = {"analysis_type": "Demonstration"}
        return {"success": True, "message": "Successfully created dummy chart.", "chart_data": data_dict, "chart_type": "line_chart", "summary": summary}
    except Exception as e:
        return {"success": False, "message": str(e)}