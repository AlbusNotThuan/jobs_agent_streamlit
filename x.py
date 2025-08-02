
import pandas as pd
import streamlit as st
import numpy as np
# Đọc dữ liệu từ file mới
df = pd.read_csv('job_skills_posted_date.csv')


# Lấy danh sách kỹ năng có số lượng > 50
skill_counts = df['skill_name'].value_counts()
filtered_skills = sorted(skill_counts[skill_counts > 400].index)



# Giao diện chọn skill ở sidebar dạng radio (hiển thị toàn bộ)

st.title("Phân tích kỹ năng theo thời gian (job_skills_posted_date.csv)")
selected_skill = st.sidebar.radio("Chọn kỹ năng:", filtered_skills)

if selected_skill:
    skill_df = df[df['skill_name'] == selected_skill].copy()
    skill_count = skill_df.groupby('posted_date').size()
    total_jobs = skill_count.sum()
    st.write(f"Tổng số job cần kỹ năng '{selected_skill}': {total_jobs}")
    st.write(f"Số lượng '{selected_skill}' theo ngày đăng:")
    st.line_chart(skill_count)

    # Biểu đồ số lượng theo tuần (12 tuần gần nhất)
    skill_df['posted_date'] = pd.to_datetime(skill_df['posted_date']).dt.tz_localize(None)
    now = pd.Timestamp.now(tz=None)
    skill_df['week'] = skill_df['posted_date'].dt.to_period('W').apply(lambda r: r.start_time)
    count_by_week = skill_df.groupby('week').size().sort_index()
    last_week = now.to_period('W').start_time
    week_range = [last_week - pd.Timedelta(weeks=i) for i in reversed(range(12))]
    count_by_week = count_by_week.reindex(week_range, fill_value=0)
    st.write(f"Số lượng '{selected_skill}' theo tuần (12 tuần gần nhất, mỗi nhóm 7 ngày):")
    st.line_chart(count_by_week)

    # Tính score tăng dần
    
    x = 0.1
    skill_df['days_since_posted'] = (now - skill_df['posted_date']).dt.days
    skill_df['score'] = np.exp(-x * skill_df['days_since_posted'])
    score_by_week = skill_df.groupby('week')['score'].sum().sort_index()
    score_by_week = score_by_week.reindex(week_range, fill_value=0)
    cumulative_score_week = score_by_week.cumsum()
    st.write(f"Biểu đồ tổng score tăng dần theo tuần (12 tuần gần nhất, mỗi nhóm 7 ngày) cho kỹ năng '{selected_skill}' (score = e^(-x * (now - posted_date)), x=0.1):")
    st.line_chart(cumulative_score_week)

    # Biểu đồ score theo tuần (không cộng dồn)
    st.write(f"Biểu đồ score theo tuần (12 tuần gần nhất, mỗi nhóm 7 ngày) cho kỹ năng '{selected_skill}' (score = e^(-x * (now - posted_date)), x=0.1):")
    st.line_chart(score_by_week)