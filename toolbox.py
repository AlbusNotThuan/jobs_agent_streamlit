#!/usr/bin/env python3
"""
Toolbox for LinkedIn Jobs Skills Analyzer Agent
Collection of tools for analyzing job market data and visualizing trends
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from typing import List, Union, Optional, Dict, Any
import os
from psycopg_query import query_database

class SkillsAnalyzerToolbox:
    """Toolbox containing various analysis and visualization tools for the skills analyzer agent"""
    
    def __init__(self):
        """Initialize the toolbox"""
        self.setup_plotting_style()
    
    def setup_plotting_style(self):
        """Set up a professional plotting style"""
        plt.style.use('default')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (2, 1)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 14
        plt.rcParams['xtick.labelsize'] = 14
        plt.rcParams['ytick.labelsize'] = 14
        plt.rcParams['legend.fontsize'] = 14
    
    def plot_skill_frequency(
        self, 
        skills: Union[str, List[str]], 
        timeframe: Optional[str] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> Dict[str, Any]:
        """
        Plot the frequency/demand of specific skills in the job market database.
        
        Args:
            skills: Single skill name (str) or list of skill names to analyze
            timeframe: Time period to analyze. Options:
                      - None or "all": All time (default)
                      - "4w": Last 4 weeks (recommended for data constraints)
                      - "1m": Last 1 month
                      - "3m": Last 3 months  
                      - "6m": Last 6 months
                      - "1y": Last 1 year
                      - Custom format: "YYYY-MM-DD" to "YYYY-MM-DD"
            save_path: Optional path to save the plot image
            show_plot: Whether to display the plot (default: True for terminal display)
            
        Returns:
            Dictionary containing:
            - success: bool
            - data: DataFrame with skill frequency data
            - plot_path: str (if saved)
            - message: str
        """
        
        # Normalize skills input
        if isinstance(skills, str):
            skills = [skills]
        
        # Default to 4 weeks if no timeframe specified (data constraint consideration)
        if timeframe is None:
            timeframe = "4w"
        
        # Build the SQL query based on timeframe
        date_filter = self._build_date_filter(timeframe)
        
        # SQL query template for skill frequency analysis over time
        sql_query = f"""
        SELECT 
            DATE(j.posted_date) as post_date,
            s.name as skill_name,
            COUNT(DISTINCT js.job_id) as daily_frequency
        FROM skill s
        JOIN job_skill js ON s.skill_id = js.skill_id
        JOIN job j ON js.job_id = j.job_id
        WHERE s.name ILIKE ANY(ARRAY[{','.join(['%s'] * len(skills))}])
        {date_filter}
        GROUP BY DATE(j.posted_date), s.name
        ORDER BY post_date, s.name;
        """
        
        try:
            # Prepare skill names for SQL query (case-insensitive search)
            skill_patterns = [f"%{skill}%" for skill in skills]
            
            # print(f"🔍 DEBUG: Skills input: {skills}")
            # print(f"🔍 DEBUG: Skill patterns: {skill_patterns}")
            # print(f"🔍 DEBUG: Timeframe: {timeframe}")
            # print(f"🔍 DEBUG: Date filter: {date_filter}")
            # print(f"🔍 DEBUG: SQL Query:\n{sql_query}")
            
            # Execute the query - pass parameters as a list
            result = query_database(sql_query, skill_patterns)
            
            # print(f"🔍 DEBUG: Query result type: {type(result)}")
            # print(f"🔍 DEBUG: Query result: {result}")
            
            # Handle different return types from query_database
            if isinstance(result, list):
                print(f"🔍 DEBUG: Result is list with {len(result)} items")
                # if result:
                #     print(f"🔍 DEBUG: First item: {result[0]}")
                #     print(f"🔍 DEBUG: First item type: {type(result[0])}")
                
                # If result is a list, assume it's the data directly
                df = pd.DataFrame(result)
                # print(f"🔍 DEBUG: DataFrame shape: {df.shape}")
                # print(f"🔍 DEBUG: DataFrame columns: {list(df.columns)}")
                if not df.empty:
                    print(f"🔍 DEBUG: DataFrame head:\n{df.head()}")
                
                success = len(result) > 0
                message = f"Successfully plotted frequency for {len(result)} skills" if success else "No data found"
            else:
                # print(f"🔍 DEBUG: Result is dict")
                # print(f"🔍 DEBUG: Result keys: {result.keys() if hasattr(result, 'keys') else 'No keys'}")
                
                # If result is a dict, handle it as before
                if not result.get("success"):
                    return {
                        "success": False,
                        "message": f"Database query failed: {result.get('message', 'Unknown error')}",
                        "data": None,
                        "plot_path": None
                    }
                
                # print(f"🔍 DEBUG: Result data: {result.get('data', 'No data key')}")
                df = pd.DataFrame(result["data"])
                # print(f"🔍 DEBUG: DataFrame shape: {df.shape}")
                # print(f"🔍 DEBUG: DataFrame columns: {list(df.columns)}")
                if not df.empty:
                    print(f"🔍 DEBUG: DataFrame head:\n{df.head()}")
                
                success = result.get("success", False)
                message = f"Successfully plotted frequency for {len(df)} skills matching: {', '.join(skills)}"
            
            if df.empty:
                return {
                    "success": False,
                    "message": f"No data found for skills: {', '.join(skills)}",
                    "data": df,
                    "plot_path": None
                }
            
            # print(f"🔍 DEBUG: Before plotting - DataFrame info:")
            # print(f"🔍 DEBUG: Columns: {list(df.columns)}")
            # print(f"🔍 DEBUG: Data types:\n{df.dtypes}")
            # print(f"🔍 DEBUG: First few rows:\n{df.head()}")
            
            # Check if we have the expected columns for time series data
            expected_columns = ['post_date', 'skill_name', 'daily_frequency']
            actual_columns = list(df.columns)
            
            # print(f"🔍 DEBUG: Expected time series columns: {expected_columns}")
            # print(f"🔍 DEBUG: Actual columns: {actual_columns}")
            
            # Try to fix column names if they don't match
            if not all(col in df.columns for col in expected_columns):
                print(f"🔍 DEBUG: Column mismatch detected, attempting to fix...")
                
                # Map columns based on position and common names
                column_mapping = {}
                
                # Try to identify columns by position and content
                for i, col in enumerate(actual_columns):
                    # Convert column name to string for checking
                    col_str = str(col).lower() if col is not None else ""
                    
                    if i == 0:  # First column should be post_date
                        if 'date' in col_str or 'post' in col_str or isinstance(col, int):
                            column_mapping[col] = 'post_date'
                        elif col != 'post_date':
                            column_mapping[col] = 'post_date'
                    elif i == 1:  # Second column should be skill_name  
                        if 'skill' in col_str or 'name' in col_str or isinstance(col, int):
                            column_mapping[col] = 'skill_name'
                        elif col != 'skill_name':
                            column_mapping[col] = 'skill_name'
                    elif i == 2:  # Third column should be daily_frequency
                        if 'frequency' in col_str or 'count' in col_str or isinstance(col, int):
                            column_mapping[col] = 'daily_frequency'
                        elif col != 'daily_frequency':
                            column_mapping[col] = 'daily_frequency'
                
                # Apply the mapping
                for old_col, new_col in column_mapping.items():
                    print(f"🔍 DEBUG: Mapping {old_col} -> {new_col}")
                
                df = df.rename(columns=column_mapping)
                print(f"🔍 DEBUG: After renaming - Columns: {list(df.columns)}")
            
            # Verify we have the required columns after mapping
            if not all(col in df.columns for col in expected_columns):
                print(f"🔍 DEBUG: Still missing columns after mapping. Setting default column names by position.")
                # If we still don't have the right columns, use positional mapping
                if len(df.columns) >= 3:
                    df.columns = expected_columns[:len(df.columns)]
                    print(f"🔍 DEBUG: Forced column names to: {list(df.columns)}")
                else:
                    raise ValueError(f"DataFrame doesn't have enough columns. Expected 3, got {len(df.columns)}")
            
            # print(f"🔍 DEBUG: Final DataFrame columns: {list(df.columns)}")
            # print(f"🔍 DEBUG: Final DataFrame dtypes:\n{df.dtypes}")
            # print(f"🔍 DEBUG: Final DataFrame sample:\n{df.head()}")
            
            # Create the visualization
            plot_path = self._create_skill_frequency_plot(
                df, skills, timeframe, save_path, show_plot
            )
            
            return {
                "success": True,
                "data": df,
                "plot_path": plot_path,
                "message": message,
                "summary": self._generate_skill_summary(df, timeframe)
            }
            
        except Exception as e:
            # print(f"🔍 DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
            import traceback
            # print(f"🔍 DEBUG: Full traceback:\n{traceback.format_exc()}")
            return {
                "success": False,
                "message": f"Error plotting skill frequency: {str(e)}",
                "data": None,
                "plot_path": None
            }
    
    def _build_date_filter(self, timeframe: Optional[str]) -> str:
        """Build SQL date filter based on timeframe parameter"""
        if not timeframe or timeframe.lower() == "all":
            return ""
        
        # Default to 4 weeks
        if timeframe == "4w":
            days_back = 28
        elif timeframe == "1m":
            days_back = 30
        elif timeframe == "3m":
            days_back = 90
        elif timeframe == "6m":
            days_back = 180
        elif timeframe == "1y":
            days_back = 365
        else:
            # If unknown timeframe, default to 4 weeks
            days_back = 28
        
        # Calculate the date threshold
        threshold_date = datetime.now() - timedelta(days=days_back)
        return f"AND j.posted_date >= '{threshold_date.strftime('%Y-%m-%d')}'"
    
    def _create_skill_frequency_plot(
        self, 
        df: pd.DataFrame, 
        skills: List[str], 
        timeframe: Optional[str],
        save_path: Optional[str],
        show_plot: bool
    ) -> Optional[str]:
        """Create and display/save the skill frequency time series plot"""
        
        # Set up matplotlib for terminal display
        import matplotlib
        matplotlib.use('TkAgg')  # Use TkAgg backend for better terminal display
        
        # Convert post_date to datetime if it's not already
        df['post_date'] = pd.to_datetime(df['post_date'])
        df = df.sort_values('post_date')
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        
        # Create a line plot for each skill
        colors = sns.color_palette("husl", len(skills))
        
        for i, skill in enumerate(skills):
            skill_data = df[df['skill_name'].str.contains(skill, case=False, na=False)]
            
            if not skill_data.empty:
                ax.plot(skill_data['post_date'], skill_data['daily_frequency'], 
                       marker='o', linewidth=2, markersize=6, 
                       color=colors[i], label=skill, alpha=0.8)
                
                # # Add trend line (optional, requires scipy)
                # try:
                #     from scipy import stats
                #     if len(skill_data) > 1:
                #         x_numeric = pd.to_numeric(skill_data['post_date'])
                #         slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, skill_data['daily_frequency'])
                #         trend_line = slope * x_numeric + intercept
                #         ax.plot(skill_data['post_date'], trend_line, '--', 
                #                color=colors[i], alpha=0.5, linewidth=1)
                # except ImportError:
                #     # Continue without trend lines if scipy not available
                #     pass
        
        ax.set_xlabel('Date', fontweight='bold', fontsize=14)
        ax.set_ylabel('Daily Job Postings', fontweight='bold', fontsize=14)
        
        # Format x-axis
        ax.tick_params(axis='x', rotation=45)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format the plot
        plt.tight_layout()
        
        # Save plot if path provided
        plot_path = None
        if save_path:
            try:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plot_path = save_path
                print(f"📊 Time series plot saved to: {save_path}")
            except Exception as e:
                print(f"Warning: Could not save plot to {save_path}: {e}")
        
        # Show plot in terminal
        if show_plot:
            print(f"\n📈 Displaying skill frequency time series for: {', '.join(skills)}")
            print(f"⏰ Timeframe: {self._format_timeframe_title(timeframe)}")
            plt.show(block=False)  # Non-blocking show for terminal
            
            # Keep the plot window open and give user control
            input("\n🎯 Press Enter to close the plot and continue...")
            plt.close()
        else:
            plt.close()
        
        return plot_path
    
    def _format_timeframe_title(self, timeframe: Optional[str]) -> str:
        """Format timeframe for plot title"""
        if not timeframe or timeframe.lower() == "all":
            return "(All Time)"
        elif timeframe == "4w":
            return "(Last 4 Weeks)"
        elif timeframe == "1m":
            return "(Last 1 Month)"
        elif timeframe == "3m":
            return "(Last 3 Months)"
        elif timeframe == "6m":
            return "(Last 6 Months)"
        elif timeframe == "1y":
            return "(Last 1 Year)"
        else:
            return f"({timeframe})"
    
    def _generate_skill_summary(self, df: pd.DataFrame, timeframe: Optional[str]) -> Dict[str, Any]:
        """Generate a summary of the skill analysis for time series data"""
        if df.empty:
            return {
                "timeframe": self._format_timeframe_title(timeframe).strip("()"),
                "total_skills_found": 0,
                "total_data_points": 0,
                "summary": "No data found"
            }
        
        # For time series data, calculate aggregated stats
        skill_totals = df.groupby('skill_name')['daily_frequency'].agg(['sum', 'mean', 'count']).reset_index()
        skill_totals = skill_totals.sort_values('sum', ascending=False)
        
        timeframe_text = self._format_timeframe_title(timeframe).strip("()")
        
        # Get date range from the data
        date_range = f"{df['post_date'].min().strftime('%Y-%m-%d')} to {df['post_date'].max().strftime('%Y-%m-%d')}"
        
        summary = {
            "timeframe": timeframe_text,
            "date_range": date_range,
            "total_skills_found": len(skill_totals),
            "total_data_points": len(df),
            "total_job_postings": int(skill_totals['sum'].sum()),
            "most_active_skill": {
                "name": skill_totals.iloc[0]['skill_name'] if len(skill_totals) > 0 else None,
                "total_frequency": int(skill_totals.iloc[0]['sum']) if len(skill_totals) > 0 else 0,
                "avg_daily_frequency": float(skill_totals.iloc[0]['mean']) if len(skill_totals) > 0 else 0.0,
                "days_with_data": int(skill_totals.iloc[0]['count']) if len(skill_totals) > 0 else 0
            },
            "skills_ranking": [
                {
                    "skill_name": row['skill_name'],
                    "total_frequency": int(row['sum']),
                    "avg_daily_frequency": float(row['mean']),
                    "days_with_data": int(row['count'])
                }
                for _, row in skill_totals.iterrows()
            ]
        }
        
        return summary

# Create a global instance for easy import
toolbox = SkillsAnalyzerToolbox()

# Simple function to plot skills frequency graph
def plot_skill_frequency(skills: Union[str, List[str]]) -> str:
    """
    Simple function to plot skill frequency and save the graph.
    
    Creates a bar chart showing how frequently the skills appear in job listings
    from the last 4 weeks. Automatically saves the graph to a file.
    
    Args:
        skills: A skill name or list of skill names to analyze
        
    Returns:
        Path to the saved plot image
    """
    # Create plots directory
    output_dir = "plots"
    os.makedirs(output_dir, exist_ok=True)
    
    # Format skills list
    skills_list = [skills] if isinstance(skills, str) else skills
    
    # Generate filename
    safe_name = "_".join(skills_list).replace(" ", "_")[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.png"
    save_path = os.path.join(output_dir, filename)
    
    # Always use 4 weeks of data
    result = toolbox.plot_skill_frequency(
        skills=skills_list,
        timeframe="4w",
        save_path=save_path,
        show_plot=False
    )
    
    # Just return the path to the saved graph
    if result["success"]:
        print(f"📊 Graph saved to: {save_path}")
        return save_path
    else:
        print(f"❌ Failed to create graph: {result['message']}")
        return None

if __name__ == "__main__":
    # Example usage
    print("🛠️ Skills Analyzer Toolbox")
    print("=" * 40)
    
    # Test the skill frequency plotting
    print("Testing skill frequency plotting...")
    
    # Example 1: Single skill
    path1 = plot_skill_frequency(["english", "AI"])
    print(f"Graph 1 saved to: {path1}")
    
    # Example 2: Multiple skills
    # path2 = plot_skill_frequency(["JavaScript", "React", "Node.js"])
    # print(f"Graph 2 saved to: {path2}")
    
    print("\n✅ Toolbox ready for use!")
