# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer
Analyze the most in-demand skills from LinkedIn jobs data

Usage:
    python skills_analyzer.py
"""

import pandas as pd
import os
from collections import Counter, defaultdict
from datetime import datetime

def extract_in_demand_skills(csv_file_path, top_n=20, min_frequency=2):
    """
    Analyze and extract the most in-demand skills from LinkedIn jobs CSV data
    
    Args:
        csv_file_path (str): Path to CSV file
        top_n (int): Number of top skills to retrieve (default: 20)
        min_frequency (int): Minimum frequency of skills to be counted (default: 2)
    
    Returns:
        dict: Dictionary containing skills statistics
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Extract all skills
        all_skills = []
        valid_jobs = 0
        
        for index, row in df.iterrows():
            skills_text = str(row.get('Skills', ''))
            if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                # Split skills by comma and clean
                skills = [skill.strip() for skill in skills_text.split(',')]
                skills = [skill for skill in skills if skill and len(skill) > 1]
                all_skills.extend(skills)
                valid_jobs += 1
        
        # Count skill frequency
        skill_counter = Counter(all_skills)
        
        # Filter skills with minimum frequency
        filtered_skills = {skill: count for skill, count in skill_counter.items() 
                          if count >= min_frequency}
        
        # Get top skills
        top_skills = sorted(filtered_skills.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Categorize skills
        skill_categories = categorize_skills([skill[0] for skill in top_skills])
        
        # Calculate percentages
        total_jobs = len(df)
        top_skills_with_percentage = []
        for skill, count in top_skills:
            percentage = (count / total_jobs) * 100
            top_skills_with_percentage.append({
                'skill': skill,
                'frequency': count,
                'percentage': round(percentage, 2)
            })
        
        # Skills frequency distribution
        frequency_distribution = defaultdict(int)
        for count in skill_counter.values():
            if count >= min_frequency:
                frequency_distribution[count] += 1
        
        result = {
            'top_skills': top_skills_with_percentage,
            'skill_categories': skill_categories,
            'total_jobs': total_jobs,
            'valid_jobs': valid_jobs,
            'total_unique_skills': len(filtered_skills),
            'skills_distribution': dict(frequency_distribution),
            'all_skills_count': len(all_skills)
        }
        
        return result
        
    except Exception as e:
        return {}

def categorize_skills(skills):
    """Categorize skills into main categories"""
    categories = {
        'Programming Languages': [],
        'AI/ML Technologies': [],
        'Data Technologies': [],
        'Cloud Platforms': [],
        'Development Tools': [],
        'Soft Skills': [],
        'Frameworks/Libraries': [],
        'Databases': [],
        'Other Technical': []
    }
    
    # Define keywords for each category
    category_keywords = {
        'Programming Languages': ['python', 'javascript', 'java', 'c++', 'c#', 'r', 'scala', 'go', 'rust', 'typescript', 'node.js', 'php', 'react'],
        'AI/ML Technologies': ['ai', 'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch', 'keras', 'generative ai', 'llm', 'neural networks', 'reinforcement learning', 'mlops'],
        'Data Technologies': ['data analysis', 'data science', 'big data', 'data mining', 'data visualization', 'analytics', 'statistics', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'power bi', 'tableau', 'looker', 'sql'],
        'Cloud Platforms': ['aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'kubernetes', 'docker'],
        'Development Tools': ['git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops', 'linux', 'unix', 'bash', 'shell scripting', 'automation test'],
        'Soft Skills': ['communication', 'teamwork', 'leadership', 'problem solving', 'analytical thinking', 'project management', 'agile', 'scrum', 'english', 'business analysis'],
        'Frameworks/Libraries': ['flask', 'django', 'spring', 'express', 'fastapi', 'langchain', 'hugging face', 'angular', 'vue'],
        'Databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'bigquery', 'oracle', 'sqlite'],
        'Other Technical': []
    }
    
    for skill in skills:
        skill_lower = skill.lower()
        categorized = False
        
        for category, keywords in category_keywords.items():
            if any(keyword in skill_lower for keyword in keywords):
                categories[category].append(skill)
                categorized = True
                break
        
        if not categorized:
            categories['Other Technical'].append(skill)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def analyze_skills_trends(csv_file_path, date_column='Posted_Date'):
    """
    Analyze skills trends over time
    
    Args:
        csv_file_path (str): Path to CSV file
        date_column (str): Name of date column
    
    Returns:
        dict: Skills trends statistics
    """
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Convert date column
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.dropna(subset=[date_column])
        
        # Create month/year column
        df['Month_Year'] = df[date_column].dt.to_period('M')
        
        # Analyze skills by time
        monthly_skills = {}
        
        for month_year in df['Month_Year'].unique():
            month_data = df[df['Month_Year'] == month_year]
            skills_in_month = []
            
            for _, row in month_data.iterrows():
                skills_text = str(row.get('Skills', ''))
                if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                    skills = [skill.strip() for skill in skills_text.split(',')]
                    skills_in_month.extend(skills)
            
            skill_counter = Counter(skills_in_month)
            monthly_skills[str(month_year)] = dict(skill_counter.most_common(10))
        
        return monthly_skills
        
    except Exception as e:
        return {}

def get_hot_skills_last_month(csv_file_path, date_column='Posted_Date', top_n=15):
    """
    Analyze hot skills in the last month
    
    Args:
        csv_file_path (str): Path to CSV file
        date_column (str): Name of date column
        top_n (int): Number of hot skills to retrieve
    
    Returns:
        dict: Dictionary containing hot skills with detailed statistics
    """
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Convert date column
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.dropna(subset=[date_column])
        
        # Get latest date and calculate one month ago
        max_date = df[date_column].max()
        one_month_ago = max_date - pd.DateOffset(months=1)
        
        # Filter data for the last month
        recent_jobs = df[df[date_column] >= one_month_ago]
        
        # Extract skills from recent jobs
        recent_skills = []
        valid_recent_jobs = 0
        
        for _, row in recent_jobs.iterrows():
            skills_text = str(row.get('Skills', ''))
            if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                skills = [skill.strip() for skill in skills_text.split(',')]
                skills = [skill for skill in skills if skill and len(skill) > 1]
                recent_skills.extend(skills)
                valid_recent_jobs += 1
        
        # Count frequency
        skill_counter = Counter(recent_skills)
        hot_skills = skill_counter.most_common(top_n)
        
        # Calculate percentages and growth rate
        hot_skills_data = []
        for skill, count in hot_skills:
            percentage = (count / len(recent_jobs)) * 100
            # Calculate appearance rate in valid jobs
            valid_percentage = (count / valid_recent_jobs) * 100 if valid_recent_jobs > 0 else 0
            
            hot_skills_data.append({
                'skill': skill,
                'frequency': count,
                'percentage_of_total': round(percentage, 2),
                'percentage_of_valid': round(valid_percentage, 2)
            })
        
        # Categorize hot skills
        hot_skill_categories = categorize_skills([item['skill'] for item in hot_skills_data])
        
        result = {
            'period': f"{one_month_ago.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}",
            'total_recent_jobs': len(recent_jobs),
            'valid_recent_jobs': valid_recent_jobs,
            'hot_skills': hot_skills_data,
            'skill_categories': hot_skill_categories,
            'total_skill_mentions': len(recent_skills)
        }
        
        return result
        
    except Exception as e:
        return {}

def get_skills_by_category(csv_file_path, category_type='all', top_n=10):
    """
    Get skills filtered by specific category
    
    Args:
        csv_file_path (str): Path to CSV file
        category_type (str): Category type ('programming', 'ai_ml', 'data', 'cloud', 'soft_skills', 'all')
        top_n (int): Number of skills to retrieve for each category
    
    Returns:
        dict: Dictionary containing skills by requested category
    """
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Extract all skills
        all_skills = []
        for _, row in df.iterrows():
            skills_text = str(row.get('Skills', ''))
            if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                skills = [skill.strip() for skill in skills_text.split(',')]
                skills = [skill for skill in skills if skill and len(skill) > 1]
                all_skills.extend(skills)
        
        # Count frequency
        skill_counter = Counter(all_skills)
        
        # Define detailed categories
        detailed_categories = {
            'programming': {
                'name': 'Programming Languages',
                'keywords': ['python', 'javascript', 'java', 'c++', 'c#', 'r', 'scala', 'go', 'rust', 'typescript', 'node.js', 'php', 'kotlin', 'swift', 'dart']
            },
            'ai_ml': {
                'name': 'AI/ML Technologies', 
                'keywords': ['ai', 'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch', 'keras', 'generative ai', 'llm', 'neural networks', 'reinforcement learning', 'mlops', 'opencv', 'scikit-learn']
            },
            'data': {
                'name': 'Data Technologies',
                'keywords': ['data analysis', 'data science', 'big data', 'data mining', 'data visualization', 'analytics', 'statistics', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'power bi', 'tableau', 'looker', 'sql', 'excel', 'r']
            },
            'cloud': {
                'name': 'Cloud & DevOps',
                'keywords': ['aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'kubernetes', 'docker', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'devops']
            },
            'web': {
                'name': 'Web Technologies',
                'keywords': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'node.js', 'express', 'django', 'flask', 'spring', 'asp.net', 'php', 'laravel']
            },
            'database': {
                'name': 'Database Technologies',
                'keywords': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'bigquery', 'oracle', 'sqlite', 'cassandra', 'dynamodb']
            },
            'soft_skills': {
                'name': 'Soft Skills',
                'keywords': ['communication', 'teamwork', 'leadership', 'problem solving', 'analytical thinking', 'project management', 'agile', 'scrum', 'english', 'business analysis', 'creativity']
            },
            'tools': {
                'name': 'Development Tools',
                'keywords': ['git', 'github', 'gitlab', 'jira', 'confluence', 'visual studio', 'intellij', 'linux', 'unix', 'bash', 'powershell', 'vim']
            }
        }
        
        def categorize_skill_advanced(skill, categories_dict):
            """Advanced skill categorization"""
            skill_lower = skill.lower()
            for cat_key, cat_info in categories_dict.items():
                if any(keyword in skill_lower for keyword in cat_info['keywords']):
                    return cat_key, cat_info['name']
            return 'other', 'Other Technical'
        
        # Categorize all skills
        categorized_skills = {}
        for category_key, category_info in detailed_categories.items():
            categorized_skills[category_key] = {
                'name': category_info['name'],
                'skills': []
            }
        categorized_skills['other'] = {'name': 'Other Technical', 'skills': []}
        
        for skill, count in skill_counter.items():
            cat_key, cat_name = categorize_skill_advanced(skill, detailed_categories)
            categorized_skills[cat_key]['skills'].append({
                'skill': skill,
                'frequency': count,
                'percentage': round((count / len(df)) * 100, 2)
            })
        
        # Sort skills in each category by frequency
        for cat_key in categorized_skills:
            categorized_skills[cat_key]['skills'].sort(key=lambda x: x['frequency'], reverse=True)
            categorized_skills[cat_key]['skills'] = categorized_skills[cat_key]['skills'][:top_n]
        
        # Return based on request
        if category_type == 'all':
            return categorized_skills
        elif category_type in categorized_skills:
            return {category_type: categorized_skills[category_type]}
        else:
            return {}
        
    except Exception as e:
        return {}

def get_trending_skills_comparison(csv_file_path, days_back=30):
    """
    Compare skills trends from the last N days from current time
    
    Args:
        csv_file_path (str): Path to CSV file
        days_back (int): Number of days to analyze from current time (default: 30)
    
    Returns:
        dict: Dictionary containing skills trends analysis
    """
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Convert date column
        df['Posted_Date'] = pd.to_datetime(df['Posted_Date'], errors='coerce')
        df = df.dropna(subset=['Posted_Date'])
        
        # Get current time and calculate cutoff date
        current_time = datetime.now()
        cutoff_date = current_time - pd.Timedelta(days=days_back)
        
        # Filter data for the last N days
        recent_data = df[df['Posted_Date'] >= cutoff_date]
        
        # Create weekly periods for trend analysis
        recent_data['Week'] = recent_data['Posted_Date'].dt.to_period('W')
        
        # Get unique weeks and sort them
        recent_weeks = sorted(recent_data['Week'].unique())
        
        weekly_skills = {}
        
        for week in recent_weeks:
            week_data = recent_data[recent_data['Week'] == week]
            week_skills = []
            
            for _, row in week_data.iterrows():
                skills_text = str(row.get('Skills', ''))
                if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                    skills = [skill.strip() for skill in skills_text.split(',')]
                    week_skills.extend(skills)
            
            skill_counter = Counter(week_skills)
            weekly_skills[str(week)] = skill_counter.most_common(15)
        
        # Calculate growth rate between most recent weeks
        trending_analysis = {}
        if len(recent_weeks) >= 2:
            current_week = str(recent_weeks[-1])
            previous_week = str(recent_weeks[-2])
            
            current_skills = dict(weekly_skills[current_week])
            previous_skills = dict(weekly_skills[previous_week])
            
            for skill, current_count in current_skills.items():
                previous_count = previous_skills.get(skill, 0)
                
                if previous_count > 0:
                    growth_rate = ((current_count - previous_count) / previous_count) * 100
                else:
                    growth_rate = float('inf') if current_count > 0 else 0
                
                trending_analysis[skill] = {
                    'current_week_count': current_count,
                    'previous_week_count': previous_count,
                    'growth_rate': round(growth_rate, 2) if growth_rate != float('inf') else 'NEW'
                }
        
        # Also analyze overall skills in the period
        all_recent_skills = []
        for _, row in recent_data.iterrows():
            skills_text = str(row.get('Skills', ''))
            if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                skills = [skill.strip() for skill in skills_text.split(',')]
                all_recent_skills.extend(skills)
        
        overall_skill_counter = Counter(all_recent_skills)
        
        result = {
            'analysis_period': f"{cutoff_date.strftime('%Y-%m-%d')} to {current_time.strftime('%Y-%m-%d')}",
            'days_analyzed': days_back,
            'total_jobs_in_period': len(recent_data),
            'weeks_analyzed': [str(week) for week in recent_weeks],
            'weekly_breakdown': weekly_skills,
            'trending_analysis': trending_analysis,
            'top_skills_overall': overall_skill_counter.most_common(20)
        }
        
        return result
        
    except Exception as e:
        return {}

def get_job_categories_analysis(csv_file_path):
    """Analyze skills by job categories"""
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Categorize jobs based on title
        job_categories = {
            'AI/ML Jobs': ['ai', 'machine learning', 'ml', 'data scientist', 'deep learning'],
            'Data Jobs': ['data analyst', 'data engineer', 'business analyst', 'bi analyst'],
            'Software Engineering': ['software engineer', 'developer', 'programmer', 'full stack'],
            'DevOps/Cloud': ['devops', 'cloud engineer', 'sre', 'infrastructure'],
            'Intern Positions': ['intern', 'trainee', 'graduate']
        }
        
        categorized_jobs = {}
        
        for category, keywords in job_categories.items():
            category_jobs = []
            for _, row in df.iterrows():
                title = str(row.get('Title', '')).lower()
                if any(keyword in title for keyword in keywords):
                    category_jobs.append(row)
            
            if category_jobs:
                # Analyze skills for each job category
                category_skills = []
                for job in category_jobs:
                    skills_text = str(job.get('Skills', ''))
                    if skills_text and skills_text != 'nan' and skills_text != 'Not specified':
                        skills = [skill.strip() for skill in skills_text.split(',')]
                        category_skills.extend(skills)
                
                skill_counter = Counter(category_skills)
                categorized_jobs[category] = {
                    'job_count': len(category_jobs),
                    'top_skills': skill_counter.most_common(10)
                }
        
        return categorized_jobs
        
    except Exception as e:
        return {}

# TEST FUNCTIONS - These functions include print statements for testing/display purposes

def print_skills_report(skills_data):
    """Print formatted skills report (TEST FUNCTION)"""
    if not skills_data:
        print("❌ No data to display")
        return
    
    print("=" * 70)
    print("📊 MOST IN-DEMAND SKILLS ANALYSIS REPORT")
    print("=" * 70)
    
    print(f"📈 Total jobs analyzed: {skills_data['total_jobs']}")
    print(f"📋 Jobs with skills info: {skills_data['valid_jobs']}")
    print(f"🔍 Total unique skills: {skills_data['total_unique_skills']}")
    print(f"📝 Total skill mentions: {skills_data['all_skills_count']}")
    print()
    
    print("🏆 TOP MOST DEMANDED SKILLS:")
    print("-" * 60)
    print(f"{'Rank':<4} {'Skill':<25} {'Jobs':<6} {'Percentage':<10} {'Bar'}")
    print("-" * 60)
    
    for i, skill_info in enumerate(skills_data['top_skills'], 1):
        skill = skill_info['skill']
        freq = skill_info['frequency']
        pct = skill_info['percentage']
        bar_length = int(pct / 2)  # Bar ratio
        bar = "█" * bar_length + "░" * (25 - bar_length)
        print(f"{i:2d}.  {skill:<25} {freq:3d}    {pct:5.1f}%     {bar}")
    
    print()
    print("📂 SKILLS CATEGORIZATION:")
    print("-" * 60)
    
    for category, skills in skills_data['skill_categories'].items():
        print(f"\n🔸 {category} ({len(skills)} skills):")
        for skill in skills[:7]:  # Display top 7 of each category
            print(f"   • {skill}")
        if len(skills) > 7:
            print(f"   ... and {len(skills) - 7} more skills")

def print_hot_skills_report(hot_skills_data):
    """Print hot skills report for last month (TEST FUNCTION)"""
    if not hot_skills_data:
        print("❌ No hot skills data to display")
        return
    
    print("🔥 HOT SKILLS IN THE LAST MONTH")
    print("-" * 60)
    print(f"📅 Period: {hot_skills_data['period']}")
    print(f"📊 Jobs count: {hot_skills_data['total_recent_jobs']} (with skills: {hot_skills_data['valid_recent_jobs']})")
    print()
    
    print("🚀 TOP HOT SKILLS:")
    print("-" * 50)
    print(f"{'Rank':<4} {'Skill':<25} {'Jobs':<6} {'% Valid':<8} {'🔥'}")
    print("-" * 50)
    
    for i, skill_info in enumerate(hot_skills_data['hot_skills'], 1):
        skill = skill_info['skill']
        freq = skill_info['frequency']
        pct = skill_info['percentage_of_valid']
        fire_level = "🔥" * min(int(pct / 10) + 1, 5)  # 1-5 fire icons
        print(f"{i:2d}.  {skill:<25} {freq:3d}    {pct:5.1f}%   {fire_level}")

def print_skills_by_category_report(category_data, category_type='all'):
    """Print skills by category report (TEST FUNCTION)"""
    if not category_data:
        print("❌ No category data to display")
        return
    
    print("📂 SKILLS BY CATEGORY")
    print("-" * 60)
    
    if category_type == 'all':
        for cat_key, cat_info in category_data.items():
            if cat_info['skills']:  # Only display categories with skills
                print(f"\n🔸 {cat_info['name']} ({len(cat_info['skills'])} skills):")
                for skill_info in cat_info['skills'][:5]:  # Top 5 each category
                    print(f"   • {skill_info['skill']:<20} ({skill_info['frequency']} jobs - {skill_info['percentage']}%)")
    else:
        cat_info = list(category_data.values())[0]
        print(f"\n🔸 {cat_info['name']}:")
        for skill_info in cat_info['skills']:
            print(f"   • {skill_info['skill']:<20} ({skill_info['frequency']} jobs - {skill_info['percentage']}%)")

def print_trending_report(trending_data):
    """Print skills trends report (TEST FUNCTION)"""
    if not trending_data:
        print("❌ No trending data to display")
        return
    
    print("📈 SKILLS TRENDS ANALYSIS")
    print("-" * 60)
    print(f"📅 Analysis period: {trending_data['analysis_period']}")
    print(f"📊 Days analyzed: {trending_data['days_analyzed']}")
    print(f"💼 Total jobs in period: {trending_data['total_jobs_in_period']}")
    print()
    
    # Show top skills overall in the period
    print("🏆 TOP SKILLS IN ANALYZED PERIOD:")
    print("-" * 50)
    for i, (skill, count) in enumerate(trending_data['top_skills_overall'][:10], 1):
        print(f"{i:2d}. {skill:<25} {count:3d} mentions")
    
    # Show weekly breakdown if available
    if trending_data.get('weekly_breakdown'):
        print(f"\n📊 WEEKLY BREAKDOWN:")
        for week, skills in list(trending_data['weekly_breakdown'].items())[-3:]:  # Last 3 weeks
            print(f"\n📅 Week {week}:")
            for skill, count in skills[:5]:
                print(f"   • {skill}: {count}")
    
    # Show growth rate analysis if available
    if trending_data.get('trending_analysis'):
        print(f"\n📈 WEEK-OVER-WEEK GROWTH ANALYSIS:")
        print(f"{'Skill':<25} {'Current':<8} {'Previous':<9} {'Growth':<10}")
        print("-" * 55)
        
        # Sort by growth rate
        sorted_trends = sorted(trending_data['trending_analysis'].items(), 
                             key=lambda x: x[1]['growth_rate'] if isinstance(x[1]['growth_rate'], (int, float)) else -1, 
                             reverse=True)
        
        for skill, data in sorted_trends[:10]:
            growth = data['growth_rate']
            growth_str = f"+{growth}%" if isinstance(growth, (int, float)) and growth > 0 else str(growth)
            if isinstance(growth, (int, float)) and growth < 0:
                growth_str = f"{growth}%"
            
            print(f"{skill:<25} {data['current_week_count']:<8} {data['previous_week_count']:<9} {growth_str:<10}")

def demo_new_features():
    """Demo new features (TEST FUNCTION)"""
    csv_file = r"c:\Users\Dang\Desktop\jobs_crawler\tools_LLM\2025-07-30_020028_linkedin_jobs.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    print("🎯 DEMO NEW FEATURES")
    print("=" * 60)
    
    # 1. Hot skills last month
    print("\n1️⃣ HOT SKILLS IN THE LAST MONTH:")
    hot_skills = get_hot_skills_last_month(csv_file, top_n=15)
    print_hot_skills_report(hot_skills)
    
    # 2. Skills by category - AI/ML
    print(f"\n\n2️⃣ SKILLS BY CATEGORY - AI/ML:")
    ai_skills = get_skills_by_category(csv_file, 'ai_ml', top_n=10)
    print_skills_by_category_report(ai_skills, 'ai_ml')
    
    # 3. Skills by category - Programming
    print(f"\n\n3️⃣ SKILLS BY CATEGORY - PROGRAMMING:")
    prog_skills = get_skills_by_category(csv_file, 'programming', top_n=10)
    print_skills_by_category_report(prog_skills, 'programming')
    
    # 4. Skills by category - Data
    print(f"\n\n4️⃣ SKILLS BY CATEGORY - DATA:")
    data_skills = get_skills_by_category(csv_file, 'data', top_n=10)
    print_skills_by_category_report(data_skills, 'data')
    
    # 5. Skills trends
    print(f"\n\n5️⃣ SKILLS TRENDS (LAST 30 DAYS):")
    trending = get_trending_skills_comparison(csv_file, days_back=30)
    print_trending_report(trending)

def export_to_csv(skills_data, output_file):
    """Export analysis results to CSV file (TEST FUNCTION)"""
    try:
        # Create DataFrame from top skills
        df = pd.DataFrame(skills_data['top_skills'])
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"📄 Exported results to CSV file: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting CSV file: {e}")

def main():
    """Main function to run complete analysis (TEST FUNCTION)"""
    print("🚀 LinkedIn Jobs Skills Analyzer - Enhanced Version")
    print("=" * 60)
    
    # CSV file path
    csv_file = r"c:\Users\Dang\Desktop\jobs_crawler\tools_LLM\2025-07-30_020028_linkedin_jobs.csv"
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    print(f"📂 Analyzing file: {os.path.basename(csv_file)}")
    print()
    
    # Selection menu
    print("🎯 CHOOSE ANALYSIS TYPE:")
    print("1. General Analysis")
    print("2. Hot Skills Last Month")
    print("3. Skills by Category")
    print("4. Skills Trends")
    print("5. Demo All Features")
    print("6. Full Analysis")
    print()
    
    try:
        choice = input("Enter choice (1-6): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    if choice == '1':
        # General analysis
        skills_data = extract_in_demand_skills(csv_file, top_n=25, min_frequency=2)
        if skills_data:
            print_skills_report(skills_data)
    
    elif choice == '2':
        # Hot skills last month
        hot_skills = get_hot_skills_last_month(csv_file, top_n=20)
        print_hot_skills_report(hot_skills)
    
    elif choice == '3':
        # Skills by category
        print("\n📂 AVAILABLE CATEGORIES:")
        categories = ['programming', 'ai_ml', 'data', 'cloud', 'web', 'database', 'soft_skills', 'tools', 'all']
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        try:
            cat_choice = input("\nChoose category (1-9): ").strip()
            cat_index = int(cat_choice) - 1
            if 0 <= cat_index < len(categories):
                selected_category = categories[cat_index]
                category_data = get_skills_by_category(csv_file, selected_category, top_n=15)
                print_skills_by_category_report(category_data, selected_category)
            else:
                print("❌ Invalid choice")
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid choice")
    
    elif choice == '4':
        # Skills trends
        try:
            days = input("Enter number of days to analyze (default 30): ").strip()
            days_back = int(days) if days else 30
        except ValueError:
            days_back = 30
        
        trending = get_trending_skills_comparison(csv_file, days_back=days_back)
        print_trending_report(trending)
    
    elif choice == '5':
        # Demo all features
        demo_new_features()
    
    elif choice == '6':
        # Full analysis
        print("🔄 Running full analysis...")
        
        # 1. General analysis
        skills_data = extract_in_demand_skills(csv_file, top_n=25, min_frequency=2)
        if skills_data:
            print_skills_report(skills_data)
        
        # 2. Hot skills
        print("\n" + "=" * 70)
        hot_skills = get_hot_skills_last_month(csv_file, top_n=15)
        print_hot_skills_report(hot_skills)
        
        # 3. Skills trends analysis
        print("\n" + "=" * 70)
        trending = get_trending_skills_comparison(csv_file, days_back=30)
        print_trending_report(trending)
        
        # 4. Analysis by job categories
        print("\n" + "=" * 70)
        print("💼 SKILLS ANALYSIS BY JOB CATEGORIES")
        print("=" * 70)
        
        job_categories = get_job_categories_analysis(csv_file)
        for category, data in job_categories.items():
            print(f"\n🔹 {category} ({data['job_count']} jobs):")
            for skill, count in data['top_skills'][:5]:
                print(f"   • {skill}: {count}")
        
        # Export file
        output_dir = os.path.join(os.path.dirname(csv_file), 'skills_analysis_output')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_output_file = os.path.join(output_dir, f'top_skills_{timestamp}.csv')
        if skills_data:
            export_to_csv(skills_data, csv_output_file)
        
        print(f"\n📁 Results saved in: {output_dir}")
    
    else:
        print("❌ Invalid choice. Please restart and choose 1-6.")
        return
    
    print("\n✅ Analysis completed!")

# Quick analysis utility function
def quick_analysis():
    """Quick analysis with common options (TEST FUNCTION)"""
    csv_file = r"c:\Users\Dang\Desktop\jobs_crawler\tools_LLM\2025-07-30_020028_linkedin_jobs.csv"
    
    print("⚡ QUICK ANALYSIS")
    print("=" * 40)
    
    # Hot skills
    print("\n🔥 HOT SKILLS (last month):")
    hot_skills = get_hot_skills_last_month(csv_file, top_n=10)
    if hot_skills:
        for i, skill in enumerate(hot_skills['hot_skills'][:5], 1):
            print(f"{i}. {skill['skill']} ({skill['frequency']} jobs)")
    
    # Top programming languages
    print("\n💻 TOP PROGRAMMING LANGUAGES:")
    prog_skills = get_skills_by_category(csv_file, 'programming', top_n=5)
    if prog_skills and 'programming' in prog_skills:
        for skill in prog_skills['programming']['skills'][:5]:
            print(f"• {skill['skill']} ({skill['frequency']} jobs)")
    
    # Top AI/ML skills
    print("\n🤖 TOP AI/ML SKILLS:")
    ai_skills = get_skills_by_category(csv_file, 'ai_ml', top_n=5)
    if ai_skills and 'ai_ml' in ai_skills:
        for skill in ai_skills['ai_ml']['skills'][:5]:
            print(f"• {skill['skill']} ({skill['frequency']} jobs)")

if __name__ == "__main__":
    # Check if pandas is installed
    try:
        import pandas as pd
    except ImportError:
        print("⚠️  Need to install pandas:")
        print("   pip install pandas")
        exit(1)
    
    # Check command line parameters
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_analysis()
    else:
        main()
