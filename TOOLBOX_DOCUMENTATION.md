# Skills Analyzer Toolbox Documentation

## Overview

The Skills Analyzer Toolbox provides powerful visualization and analysis tools for your autonomous LinkedIn Jobs Skills Analyzer agent. The toolbox includes functions that can be called directly by your LLM agent to create insightful visualizations of job market data.

## 🛠️ Available Tools

### 1. `plot_skill_frequency(skills, timeframe=None, save_path=None, show_plot=True)`

**Purpose:** Plot the frequency and demand of specific skills in the job market database.

**Parameters:**
- `skills` (str or List[str]): Single skill name or list of skill names to analyze
- `timeframe` (str, optional): Time period to analyze
  - `None` or `"all"`: All time (default)
  - `"1m"`: Last 1 month
  - `"3m"`: Last 3 months
  - `"6m"`: Last 6 months
  - `"1y"`: Last 1 year
  - Custom: `"YYYY-MM-DD to YYYY-MM-DD"` for specific date ranges
- `save_path` (str, optional): Path to save the plot image
- `show_plot` (bool): Whether to display the plot (default: True)

**Returns:** Dictionary containing:
- `success` (bool): Whether the operation succeeded
- `data` (DataFrame): Skill frequency data
- `plot_path` (str): Path to saved plot (if saved)
- `message` (str): Status message
- `summary` (dict): Statistical summary of the analysis

**SQL Query Template Used:**
```sql
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
```

## 📊 Visualization Features

The plotting tool creates dual visualizations:

1. **Frequency Bar Chart**: Shows absolute number of job postings mentioning each skill
2. **Percentage Bar Chart**: Shows skills as percentage of total jobs in the timeframe

Both charts include:
- Professional styling with clear labels
- Value annotations on bars
- Appropriate color schemes
- Responsive sizing

## 🤖 Agent Integration

The toolbox is fully integrated into your autonomous agent. The agent can:

1. **Automatically decide** when to use visualization tools based on user requests
2. **Generate appropriate parameters** (skills, timeframes) from natural language
3. **Interpret results** and provide insights based on the visualizations
4. **Combine multiple tools** (database queries + visualizations) for comprehensive analysis

## 💡 Usage Examples

### Example 1: Single Skill Analysis
```python
# Agent receives: "Show me Python demand"
result = plot_skill_frequency("Python")
```

### Example 2: Multi-Skill Comparison
```python
# Agent receives: "Compare JavaScript vs React popularity"
result = plot_skill_frequency(["JavaScript", "React"])
```

### Example 3: Timeframe Analysis
```python
# Agent receives: "Plot AI skills demand over the last 6 months"
result = plot_skill_frequency(["AI", "Machine Learning", "Deep Learning"], "6m")
```

### Example 4: Custom Date Range
```python
# Agent receives: "Analyze Python trends from January to June 2024"
result = plot_skill_frequency("Python", "2024-01-01 to 2024-06-30")
```

## 🔄 ReAct Framework Integration

The agent uses the plotting tool within its ReAct cycles:

```
🧠 **THOUGHT:** User wants to see skill demand trends. I should create a visualization to show the data clearly.

⚡ **ACTION:** I'll use plot_skill_frequency to create a chart showing the demand for the requested skills.

👁️ **OBSERVATION:** The visualization shows clear trends. Let me analyze the results and provide insights.
```

## 🎯 Data Analysis Features

The tool provides comprehensive analysis including:

- **Absolute frequency** of skill mentions
- **Percentage of total jobs** requiring each skill
- **Ranking** of skills by demand
- **Time-based filtering** for trend analysis
- **Statistical summaries** for easy interpretation

## 📈 Future Extensions

The toolbox architecture supports easy addition of new tools:

- **Salary analysis charts**
- **Geographic demand mapping**
- **Skill correlation analysis**
- **Time series trend analysis**
- **Company-specific skill requirements**

## 🚀 Getting Started

1. **Install dependencies:** `pip install matplotlib seaborn pandas`
2. **Import the toolbox:** Already integrated in your agent
3. **Test the functionality:** Run `python test_toolbox.py`
4. **Use with your agent:** The agent will automatically use visualization tools when appropriate

## 📋 Error Handling

The toolbox includes robust error handling:

- **Database connection issues** are caught and reported
- **Invalid skill names** return helpful error messages
- **Malformed timeframes** fall back to "all time" analysis
- **Plotting errors** are handled gracefully with informative messages

Your autonomous agent now has powerful visualization capabilities that enhance its ability to provide insightful job market analysis! 🎉
