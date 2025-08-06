#!/usr/bin/env python3
"""
Toolbox for LinkedIn Jobs Skills Analyzer Agent

This module provides a collection of standalone functions that act as tools for the AI agent.
Each function is designed to query the database, process data, and return a structured,
serializable dictionary containing chart data and a summary for analysis.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import sys

# Ensure the correct path is set to import from the parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from psycopg_query import query_database


def analyze_skill_frequency(skills: List[str]) -> Dict[str, Any]:
    """
    Analyzes the daily posting frequency of specific skills over the last 4 weeks.

    This tool queries the database for job postings that mention the given skills
    within the last 28 days. It is ideal for understanding the recent demand trend
    for technical skills, programming languages, or certifications. The function
    returns data formatted for a time-series line chart and a summary for analysis.

    Args:
        skills (List[str]): A list of skill names to analyze (e.g., ["Python", "SQL"]).

    Returns:
        Dict[str, Any]: A dictionary containing the analysis results, including
                        chart-ready data and a summary.
    """
    print(f"🛠️ Executing analyze_skill_frequency for: {skills}")
    try:
        # 1. Prepare SQL query for the last 4 weeks
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        skill_patterns = [f"%{skill}%" for skill in skills]

        sql_query = """
        SELECT
            DATE(j.posted_date) as post_date,
            s.name as item_name,
            COUNT(DISTINCT j.job_id) as frequency
        FROM skill s
        JOIN job_skill js ON s.skill_id = js.skill_id
        JOIN job j ON js.job_id = j.job_id
        WHERE s.name ILIKE ANY(ARRAY[%s])
        AND j.posted_date >= %s
        GROUP BY DATE(j.posted_date), s.name
        ORDER BY post_date;
        """
        # Note: psycopg automatically handles placeholder substitution and quoting
        params = (', '.join(['%s'] * len(skill_patterns)), four_weeks_ago)
        
        # Psycopg3 expects parameters to be passed in a list or tuple for the execute method
        db_params = skill_patterns + [four_weeks_ago]
        sql_query_for_psycopg = sql_query.replace(
            "ILIKE ANY(ARRAY[%s])",
            "ILIKE ANY(ARRAY[" + ", ".join(["%s"] * len(skill_patterns)) + "])"
        )

        result = query_database(sql_query_for_psycopg, db_params)

        # 2. Process the results
        if not result:
            return {"success": False, "message": f"No data found for skills: {skills} in the last 4 weeks."}

        df = pd.DataFrame(result, columns=['post_date', 'item_name', 'frequency'])
        df['post_date'] = pd.to_datetime(df['post_date'])

        # 3. Create the chart data by pivoting the DataFrame
        chart_df = df.pivot(index='post_date', columns='item_name', values='frequency').fillna(0)

        # 4. Generate a summary for the agent
        summary = {
            "analysis_type": "Skill Frequency",
            "items_analyzed": skills,
            "time_period": "Last 4 Weeks",
            "total_mentions": int(df['frequency'].sum()),
            "most_frequent_skill": df.groupby('item_name')['frequency'].sum().idxmax(),
        }

        # 5. Serialize the chart data correctly
        data_dict = chart_df.to_dict('split')
        data_dict['index'] = [ts.isoformat() for ts in data_dict['index']]

        return {
            "success": True,
            "message": f"Successfully analyzed skill frequency for {len(skills)} skills.",
            "chart_data": data_dict,
            "chart_type": "line_chart",
            "summary": summary
        }

    except Exception as e:
        print(f"❌ Error in analyze_skill_frequency: {e}")
        return {"success": False, "message": f"An error occurred: {e}"}


def analyze_job_expertise_frequency(job_expertises: List[str]) -> Dict[str, Any]:
    """
    Analyzes the daily posting frequency of specific, standardized job expertises over the last 4 weeks.

    This is the correct tool for tracking hiring trends for specific roles. It queries
    the 'job_expertise' column, which contains clean, standardized data (e.g., "Data Scientist",
    "Software Engineer", "Frontend Developer"). Do NOT use this tool for raw, unstructured titles.
    The function returns data formatted for a time-series line chart and a summary for analysis.

    Args:
        job_expertises (List[str]): A list of standardized job expertise titles to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing the analysis results, including
                        chart-ready data and a summary.
    """
    print(f"🛠️ Executing analyze_job_expertise_frequency for: {job_expertises}")
    try:
        # 1. Prepare SQL query for the last 4 weeks
        four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
        expertise_patterns = [f"%{expertise}%" for expertise in job_expertises]

        # This query correctly targets the standardized 'job_expertise' column for reliable analysis.
        sql_query = """
        SELECT
            DATE(posted_date) as post_date,
            job_expertise as item_name,
            COUNT(job_id) as frequency
        FROM job
        WHERE job_expertise ILIKE ANY(ARRAY[%s])
        AND posted_date >= %s
        GROUP BY DATE(posted_date), job_expertise
        ORDER BY post_date;
        """
        db_params = expertise_patterns + [four_weeks_ago]
        # This formatting is kept for compatibility with psycopg's parameter handling for ANY(ARRAY[...])
        sql_query_for_psycopg = sql_query.replace(
            "ILIKE ANY(ARRAY[%s])",
            "ILIKE ANY(ARRAY[" + ", ".join(["%s"] * len(expertise_patterns)) + "])"
        )
        
        result = query_database(sql_query_for_psycopg, db_params)

        # 2. Process the results
        if not result:
            return {"success": False, "message": f"No data found for job expertises: {job_expertises} in the last 4 weeks."}

        df = pd.DataFrame(result, columns=['post_date', 'item_name', 'frequency'])
        df['post_date'] = pd.to_datetime(df['post_date'])

        # 3. Create the chart data by pivoting the DataFrame
        chart_df = df.pivot(index='post_date', columns='item_name', values='frequency').fillna(0)

        # 4. Generate a summary for the agent, using corrected terminology
        summary = {
            "analysis_type": "Job Expertise Frequency",
            "items_analyzed": job_expertises,
            "time_period": "Last 4 Weeks",
            "total_postings": int(df['frequency'].sum()),
            "most_frequent_expertise": df.groupby('item_name')['frequency'].sum().idxmax(),
        }

        # 5. Serialize the chart data correctly for JSON compatibility
        data_dict = chart_df.to_dict('split')
        data_dict['index'] = [ts.isoformat() for ts in data_dict['index']]

        return {
            "success": True,
            "message": f"Successfully analyzed job expertise frequency for {len(job_expertises)} expertises.",
            "chart_data": data_dict,
            "chart_type": "line_chart",
            "summary": summary
        }

    except Exception as e:
        print(f"❌ Error in analyze_job_expertise_frequency: {e}")
        return {"success": False, "message": f"An error occurred: {e}"}


def create_dummy_line_chart() -> Dict[str, Any]:
    """
    Creates a line chart with dummy data for demonstration purposes.

    This tool does not query the database. It generates a random time-series
    DataFrame to test and demonstrate the application's charting capabilities.
    It returns the data in the same standardized format as the analysis tools.

    Returns:
        Dict[str, Any]: A dictionary containing the sample chart data and summary.
    """
    print("🛠️ Generating dummy line chart...")
    try:
        # 1. Create dummy data
        date_range = pd.to_datetime(pd.date_range(end=datetime.now(), periods=30, freq='D'))
        chart_data_df = pd.DataFrame(
            (abs(pd.np.random.randn(30, 3).cumsum(axis=0)) + 10),
            index=date_range,
            columns=["Alpha Trend", "Beta Trend", "Gamma Trend"]
        )

        # 2. Serialize the chart data correctly
        data_dict = chart_data_df.to_dict('split')
        data_dict['index'] = [ts.isoformat() for ts in data_dict['index']]

        # 3. Create a sample summary
        summary = {
            "analysis_type": "Demonstration",
            "items_analyzed": ["Alpha", "Beta", "Gamma"],
            "time_period": "Sample Data",
        }

        return {
            "success": True,
            "message": "Successfully created a dummy line chart.",
            "chart_data": data_dict,
            "chart_type": "line_chart",
            "summary": summary
        }

    except Exception as e:
        print(f"❌ Error creating dummy chart: {e}")
        return {"success": False, "message": f"Error creating dummy chart: {e}"}