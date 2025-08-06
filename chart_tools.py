import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime

def create_bar_chart(data: Dict[str, float], 
                    title: str = "Bar Chart", 
                    xlabel: str = "Categories", 
                    ylabel: str = "Values",
                    figsize: Tuple[int, int] = (10, 6),
                    save_path: Optional[str] = None) -> None:
    """
    Creates a bar chart from dictionary data.

    Args:
        data (Dict[str, float]): Dictionary with category names as keys and values as numbers.
        title (str): Title of the chart. Defaults to "Bar Chart".
        xlabel (str): Label for x-axis. Defaults to "Categories".
        ylabel (str): Label for y-axis. Defaults to "Values".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (10, 6).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    categories = list(data.keys())
    values = list(data.values())
    
    plt.bar(categories, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_line_chart(x_data: List[str], 
                     y_data: List[float], 
                     title: str = "Line Chart",
                     xlabel: str = "X-axis", 
                     ylabel: str = "Y-axis",
                     figsize: Tuple[int, int] = (10, 6),
                     save_path: Optional[str] = None) -> None:
    """
    Creates a line chart from x and y data arrays.

    Args:
        x_data (List[str]): List of x-axis values (dates, strings, or numbers).
        y_data (List[float]): List of y-axis values (numeric).
        title (str): Title of the chart. Defaults to "Line Chart".
        xlabel (str): Label for x-axis. Defaults to "X-axis".
        ylabel (str): Label for y-axis. Defaults to "Y-axis".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (10, 6).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    plt.plot(x_data, y_data, marker='o')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_pie_chart(data: Dict[str, float], 
                    title: str = "Pie Chart",
                    figsize: Tuple[int, int] = (8, 8),
                    save_path: Optional[str] = None) -> None:
    """
    Creates a pie chart from dictionary data.

    Args:
        data (Dict[str, float]): Dictionary with category names as keys and values as numbers.
        title (str): Title of the chart. Defaults to "Pie Chart".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (8, 8).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    labels = list(data.keys())
    values = list(data.values())
    
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    plt.axis('equal')
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_heatmap(data: List[List[float]], 
                  row_labels: List[str], 
                  col_labels: List[str],
                  title: str = "Heatmap",
                  figsize: Tuple[int, int] = (10, 8),
                  save_path: Optional[str] = None) -> None:
    """
    Creates a heatmap from 2D data array.

    Args:
        data (List[List[float]]): 2D array of numeric values.
        row_labels (List[str]): Labels for rows.
        col_labels (List[str]): Labels for columns.
        title (str): Title of the chart. Defaults to "Heatmap".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (10, 8).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    sns.heatmap(data, xticklabels=col_labels, yticklabels=row_labels, 
                annot=True, fmt='.2f', cmap='viridis')
    plt.title(title)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_histogram(data: List[float], 
                    bins: int = 20,
                    title: str = "Histogram",
                    xlabel: str = "Values", 
                    ylabel: str = "Frequency",
                    figsize: Tuple[int, int] = (10, 6),
                    save_path: Optional[str] = None) -> None:
    """
    Creates a histogram from numeric data.

    Args:
        data (List[float]): List of numeric values.
        bins (int): Number of bins for the histogram. Defaults to 20.
        title (str): Title of the chart. Defaults to "Histogram".
        xlabel (str): Label for x-axis. Defaults to "Values".
        ylabel (str): Label for y-axis. Defaults to "Frequency".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (10, 6).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    plt.hist(data, bins=bins, alpha=0.7, edgecolor='black')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_scatter_plot(x_data: List[float], 
                       y_data: List[float],
                       title: str = "Scatter Plot",
                       xlabel: str = "X-axis", 
                       ylabel: str = "Y-axis",
                       figsize: Tuple[int, int] = (10, 6),
                       save_path: Optional[str] = None) -> None:
    """
    Creates a scatter plot from x and y data arrays.

    Args:
        x_data (List[float]): List of x-axis values (numeric).
        y_data (List[float]): List of y-axis values (numeric).
        title (str): Title of the chart. Defaults to "Scatter Plot".
        xlabel (str): Label for x-axis. Defaults to "X-axis".
        ylabel (str): Label for y-axis. Defaults to "Y-axis".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (10, 6).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    plt.scatter(x_data, y_data, alpha=0.6)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

def create_multi_line_chart(data: Dict[str, List[float]], 
                           x_data: List[str],
                           title: str = "Multi-Line Chart",
                           xlabel: str = "X-axis", 
                           ylabel: str = "Y-axis",
                           figsize: Tuple[int, int] = (12, 6),
                           save_path: Optional[str] = None) -> None:
    """
    Creates a multi-line chart with multiple data series.

    Args:
        data (Dict[str, List[float]]): Dictionary with series names as keys and y-values as lists.
        x_data (List[str]): List of x-axis values shared by all series.
        title (str): Title of the chart. Defaults to "Multi-Line Chart".
        xlabel (str): Label for x-axis. Defaults to "X-axis".
        ylabel (str): Label for y-axis. Defaults to "Y-axis".
        figsize (Tuple[int, int]): Figure size (width, height). Defaults to (12, 6).
        save_path (Optional[str]): Path to save the chart. If None, displays the chart. Defaults to None.

    Returns:
        None: Displays or saves the chart.
    """
    plt.figure(figsize=figsize)
    
    for series_name, y_values in data.items():
        plt.plot(x_data, y_values, marker='o', label=series_name)
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {save_path}")
    else:
        plt.show()
    plt.close()

if __name__ == "__main__":
    # Ví dụ sử dụng các function
    
    # 1. Bar chart example
    skill_scores = {"python": 1.0052, "sql": 0.9626, "ml": 0.5234, "java": 0.3421}
    create_bar_chart(skill_scores, 
                     title="Skill Hot Scores", 
                     xlabel="Skills", 
                     ylabel="Hot Score",
                     save_path="skill_scores_chart.png")
    
    # 2. Line chart example
    dates = ["2025-07-27", "2025-07-28", "2025-07-29", "2025-07-30", "2025-07-31"]
    job_counts = [15, 23, 18, 31, 27]
    create_line_chart(dates, job_counts,
                     title="Daily Job Posts",
                     xlabel="Date",
                     ylabel="Number of Jobs")
    
    # 3. Pie chart example
    exp_distribution = {"Internship": 10, "Entry Level": 25, "Junior Level": 40, "Senior Level": 25}
    create_pie_chart(exp_distribution, title="Experience Level Distribution")
