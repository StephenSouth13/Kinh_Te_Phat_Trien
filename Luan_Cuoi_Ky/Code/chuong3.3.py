import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Tên file dữ liệu thô (File gốc từ World Bank)
file_data = "D:\\UEH\\Kinh_Te_Phat_Trien\\Luan_Cuoi_Ky\\P_Data_Extract_From_World_Development_Indicators\\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv" 
df_raw = pd.read_csv(file_data)

# =========================================================
# 1. CHUẨN HÓA DỮ LIỆU THÔ (Wide -> Long)
# =========================================================
df_cleaned = df_raw.dropna(subset=['Series Code', 'Country Code', 'Country Name']).copy()
year_columns = [col for col in df_cleaned.columns if '[YR' in col]

df_long = pd.melt(df_cleaned, 
                  id_vars=['Country Name', 'Country Code', 'Series Name', 'Series Code'], 
                  value_vars=year_columns, 
                  var_name='Year', 
                  value_name='Value')

df_long['Year'] = df_long['Year'].str.extract(r'(\d{4})').astype(int)
df_long['Value'] = df_long['Value'].replace('..', np.nan)
df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')


# =========================================================
# 2. HÀM VẼ BIỂU ĐỒ SO SÁNH (BAR CHART)
# =========================================================
def plot_comparison_bar(df, code, title, ylabel, filename, ymin=None, ymax=None):
    df_indicator = df[df['Series Code'] == code].copy()
    
    df_valid = df_indicator.dropna(subset=['Value'])
    if df_valid.empty: return
    
    # Lấy năm gần nhất có dữ liệu cho hầu hết các nước
    year_counts = df_valid.groupby('Year')['Country Name'].count()
    latest_year = year_counts[year_counts >= 3].index.max()
    if pd.isna(latest_year): latest_year = df_valid['Year'].max()
    
    df_latest = df_indicator[df_indicator['Year'] == latest_year].dropna(subset=['Value'])
    df_plot = df_latest.sort_values(by='Value', ascending=False)
    
    if df_plot.empty: return
    
    mean_value = df_plot['Value'].mean()
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(df_plot['Country Name'], df_plot['Value'], 
                   color=['red' if c == 'Viet Nam' else 'skyblue' for c in df_plot['Country Name']])
    
    plt.axhline(mean_value, color='gray', linestyle='--', linewidth=1, label=f'Trung bình ASEAN ({mean_value:.2f})')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (ymax * 0.01 if ymax else 0.01), 
                 f'{yval:.2f}', ha='center', va='bottom')

    plt.title(f'{title} (Năm {latest_year})', fontsize=14)
    plt.xlabel('Quốc gia', fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    
    if ymin is not None and ymax is not None:
        plt.ylim(ymin, ymax)
        
    plt.xticks(rotation=0)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    
    print(f"\n--- Thống kê {code} (Năm {latest_year}) ---")
    print(df_plot[['Country Name', 'Value']].to_markdown(index=False, numalign="left", stralign="left"))


# =========================================================
# 3. GỌI HÀM CHO CÁC CHỈ TIÊU G (Mục 3.3)
# =========================================================

# Government Effectiveness (GE.EST)
plot_comparison_bar(df_long, 'GE.EST', 'So sánh Hiệu quả Chính phủ (GE)', 'Estimate (±2.5)', 
                    'gov_effectiveness_comparison.png', ymin=-0.5, ymax=2.5)
# Regulatory Quality (RQ.EST)
plot_comparison_bar(df_long, 'RQ.EST', 'So sánh Chất lượng Điều tiết (RQ)', 'Estimate (±2.5)', 
                    'regulatory_quality_comparison.png', ymin=-0.5, ymax=2.5)
# Control of Corruption (CC.PER.RNK)
plot_comparison_bar(df_long, 'CC.PER.RNK', 'So sánh Kiểm soát Tham nhũng (CC)', 'Percentile Rank (0-100)', 
                    'control_corruption_comparison.png', ymin=0, ymax=100)