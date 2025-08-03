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
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
    
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
        
        # SQL query template for skill frequency analysis
        sql_query = f"""
        SELECT 
            s.name as skill_name,
            COUNT(js.job_id) as frequency,
            COUNT(DISTINCT js.job_id) as unique_jobs,
            ROUND(
                (COUNT(js.job_id) * 100.0 / (
                    SELECT COUNT(DISTINCT job_id) 
                    FROM job_skill js2 
                    JOIN job j2 ON js2.job_id = j2.job_id
                    {date_filter}
                )), 2
            ) as percentage_of_jobs
        FROM skill s
        JOIN job_skill js ON s.skill_id = js.skill_id
        JOIN job j ON js.job_id = j.job_id
        WHERE s.name ILIKE ANY(%s)
        {date_filter}
        GROUP BY s.name
        ORDER BY frequency DESC;
        """
        
        try:
            # Prepare skill names for SQL query (case-insensitive search)
            skill_patterns = [f"%{skill}%" for skill in skills]
            
            # Execute the query
            result = query_database(sql_query, skill_patterns)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "message": f"Database query failed: {result.get('message', 'Unknown error')}",
                    "data": None,
                    "plot_path": None
                }
            
            df = pd.DataFrame(result["data"])
            
            if df.empty:
                return {
                    "success": False,
                    "message": f"No data found for skills: {', '.join(skills)}",
                    "data": df,
                    "plot_path": None
                }
            
            # Create the visualization
            plot_path = self._create_skill_frequency_plot(
                df, skills, timeframe, save_path, show_plot
            )
            
            return {
                "success": True,
                "data": df,
                "plot_path": plot_path,
                "message": f"Successfully plotted frequency for {len(df)} skills matching: {', '.join(skills)}",
                "summary": self._generate_skill_summary(df, timeframe)
            }
            
        except Exception as e:
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
        
        # Parse timeframe
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
            # Custom date range format: "YYYY-MM-DD to YYYY-MM-DD"
            if " to " in timeframe:
                try:
                    start_date, end_date = timeframe.split(" to ")
                    return f"AND j.posted_date BETWEEN '{start_date}' AND '{end_date}'"
                except:
                    return ""  # Fall back to all time if parsing fails
            else:
                return ""  # Fall back to all time
        
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
        """Create and display/save the skill frequency plot optimized for terminal display"""
        
        # Set up matplotlib for terminal display
        import matplotlib
        matplotlib.use('TkAgg')  # Use TkAgg backend for better terminal display
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot 1: Frequency bar chart
        bars1 = ax1.bar(df['skill_name'], df['frequency'], 
                        color=sns.color_palette("husl", len(df)))
        ax1.set_title(f'Skill Frequency in Job Postings\n{self._format_timeframe_title(timeframe)}', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Skills', fontweight='bold')
        ax1.set_ylabel('Number of Job Postings', fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Percentage of jobs
        bars2 = ax2.bar(df['skill_name'], df['percentage_of_jobs'],
                        color=sns.color_palette("viridis", len(df)))
        ax2.set_title(f'Skills as % of Total Jobs\n{self._format_timeframe_title(timeframe)}',
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Skills', fontweight='bold')
        ax2.set_ylabel('Percentage of Jobs (%)', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add percentage labels on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot if path provided
        plot_path = None
        if save_path:
            try:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plot_path = save_path
                print(f"📊 Plot saved to: {save_path}")
            except Exception as e:
                print(f"Warning: Could not save plot to {save_path}: {e}")
        
        # Show plot in terminal
        if show_plot:
            print(f"\n📈 Displaying skill frequency chart for: {', '.join(skills)}")
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
        """Generate a summary of the skill analysis"""
        total_jobs = df['unique_jobs'].sum()
        most_demanded = df.iloc[0] if not df.empty else None
        
        timeframe_text = self._format_timeframe_title(timeframe).strip("()")
        
        summary = {
            "timeframe": timeframe_text,
            "total_skills_found": len(df),
            "total_job_postings": total_jobs,
            "most_demanded_skill": {
                "name": most_demanded['skill_name'] if most_demanded is not None else None,
                "frequency": int(most_demanded['frequency']) if most_demanded is not None else 0,
                "percentage": float(most_demanded['percentage_of_jobs']) if most_demanded is not None else 0.0
            },
            "skills_ranking": df[['skill_name', 'frequency', 'percentage_of_jobs']].to_dict('records')
        }
        
        return summary

# Create a global instance for easy import
toolbox = SkillsAnalyzerToolbox()

# Convenience function for the agent to use directly
def plot_skill_frequency(
    skills: Union[str, List[str]], 
    timeframe: Optional[str] = None,
    save_path: Optional[str] = None,
    show_plot: bool = True
) -> Dict[str, Any]:
    """
    Convenience wrapper for the plot_skill_frequency method.
    
    Plot the frequency/demand of specific skills in the job market database.
    Optimized for terminal display with interactive plot windows.
    
    Args:
        skills: Single skill name (str) or list of skill names to analyze
        timeframe: Time period to analyze (None defaults to "4w" for data constraints)
                  Options: "all", "4w", "1m", "3m", "6m", "1y", or custom date range
        save_path: Optional path to save the plot image
        show_plot: Whether to display the plot in terminal (default: True)
        
    Returns:
        Dictionary with success status, data, plot_path, message, and summary
        
    Examples:
        # Single skill, default 4 weeks (recommended)
        result = plot_skill_frequency("Python")
        
        # Multiple skills, all time
        result = plot_skill_frequency(["Python", "JavaScript", "Java"], "all")
        
        # Custom date range
        result = plot_skill_frequency("React", "2024-01-01 to 2024-06-30")
    """
    return toolbox.plot_skill_frequency(skills, timeframe, save_path, show_plot)

if __name__ == "__main__":
    # Example usage
    print("🛠️ Skills Analyzer Toolbox")
    print("=" * 40)
    
    # Test the skill frequency plotting
    print("Testing skill frequency plotting...")
    
    # Example 1: Single skill
    result1 = plot_skill_frequency("Python", show_plot=False)
    print(f"Result 1: {result1['message']}")
    
    # Example 2: Multiple skills with timeframe
    result2 = plot_skill_frequency(["JavaScript", "React", "Node.js"], "6m", show_plot=False)
    print(f"Result 2: {result2['message']}")
    
    print("\n✅ Toolbox ready for use!")
