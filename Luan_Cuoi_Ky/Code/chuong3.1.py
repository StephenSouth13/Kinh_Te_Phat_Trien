import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Tên file dữ liệu thô (File gốc từ World Bank)
file_data = "D:\\UEH\\Kinh_Te_Phat_Trien\\Luan_Cuoi_Ky\\P_Data_Extract_From_World_Development_Indicators\\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv" 
df_raw = pd.read_csv(file_data)

# ============================= ============================
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
# 2. PHÂN TÍCH ĐỊNH LƯỢNG (CAGR & MEAN)
# =========================================================
def calculate_cagr(start_value, end_value, start_year, end_year):
    if start_year >= end_year or start_value <= 0:
        return np.nan
    years = end_year - start_year
    return ((end_value / start_value) ** (1 / years) - 1) * 100

metrics = {}

for code, name in {'EN.GHG.CO2.ZG.AR5': 'CO2 Emissions', 'EG.FEC.RNEW.ZS': 'Renewable Energy'}.items():
    df_e = df_long[df_long['Series Code'] == code].dropna(subset=['Value']).copy()
    
    latest_year = df_e['Year'].max()
    start_year = df_e['Year'].min()
    
    df_latest = df_e[df_e['Year'] == latest_year]
    
    # Tính CAGR cho Việt Nam
    vn_latest = df_latest[df_latest['Country Name'] == 'Viet Nam']['Value'].iloc[0]
    vn_start = df_e[(df_e['Country Name'] == 'Viet Nam') & (df_e['Year'] == start_year)]['Value'].iloc[0]
    cagr = calculate_cagr(vn_start, vn_latest, start_year, latest_year)
    
    # Tính Trung bình ASEAN (trừ SG)
    mean_asean = df_latest[df_latest['Country Name'] != 'Singapore']['Value'].mean()
    
    metrics[code] = {
        'Name': name,
        'VN Latest Value': round(vn_latest, 2),
        'ASEAN Mean': round(mean_asean, 2),
        'VN CAGR': round(cagr, 2),
        'Year Range': f'{start_year}-{latest_year}',
        'Data': df_e # Lưu DataFrame cho plotting
    }

print("--- PHÂN TÍCH ĐỊNH LƯỢNG E ---")
print(f"CO2 Emissions (VN Latest={metrics['EN.GHG.CO2.ZG.AR5']['VN Latest Value']}%, ASEAN Mean={metrics['EN.GHG.CO2.ZG.AR5']['ASEAN Mean']}%)")
print(f"CO2 Emissions CAGR (2015-2023): {metrics['EN.GHG.CO2.ZG.AR5']['VN CAGR']}%")
print(f"Renewable Energy (VN Latest={metrics['EG.FEC.RNEW.ZS']['VN Latest Value']}%, ASEAN Mean={metrics['EG.FEC.RNEW.ZS']['ASEAN Mean']}%)")
print(f"Renewable Energy CAGR (2015-2021): {metrics['EG.FEC.RNEW.ZS']['VN CAGR']}%")


# =========================================================
# 3. VẼ BIỂU ĐỒ (VISUALIZATION)
# =========================================================

# --- A. CO2 Emissions Trend Plot ---
plt.figure(figsize=(12, 7))
df_co2 = metrics['EN.GHG.CO2.ZG.AR5']['Data']

for country in df_co2['Country Name'].unique():
    df_country = df_co2[df_co2['Country Name'] == country].sort_values(by='Year')
    
    if country == 'Viet Nam':
        plt.plot(df_country['Year'], df_country['Value'], label=country, color='red', linewidth=3, marker='o')
        last_value = df_country['Value'].iloc[-1] if not df_country.empty else np.nan
        plt.text(df_country['Year'].max(), last_value, f'VN ({int(last_value)})', color='red', fontsize=10, ha='left', va='center')
    else:
        plt.plot(df_country['Year'], df_country['Value'], label=country, alpha=0.7)

plt.title('Xu hướng Phát thải CO₂ (% thay đổi so với 1990) của Việt Nam và ASEAN', fontsize=14)
plt.xlabel('Năm', fontsize=12)
plt.ylabel('Phát thải CO₂ (% so với 1990)', fontsize=12)
plt.xticks(df_co2['Year'].unique(), rotation=45)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('co2_emissions_trend.png')
plt.close()


# --- B. Renewable Energy Trend Plot ---
plt.figure(figsize=(12, 7))
df_re = metrics['EG.FEC.RNEW.ZS']['Data']

for country in df_re['Country Name'].unique():
    df_country = df_re[df_re['Country Name'] == country].sort_values(by='Year')
    
    if country == 'Viet Nam':
        plt.plot(df_country['Year'], df_country['Value'], label=country, color='red', linewidth=3, marker='o')
        last_value_vn = df_country['Value'].iloc[-1] if not df_country.empty else np.nan
        plt.text(df_country['Year'].max(), last_value_vn, f'VN ({last_value_vn:.1f}%)', color='red', fontsize=10, ha='left', va='center')
    else:
        plt.plot(df_country['Year'], df_country['Value'], label=country, alpha=0.7)

plt.title('Xu hướng Tiêu thụ Năng lượng Tái tạo (% tổng tiêu thụ) của Việt Nam và ASEAN', fontsize=14)
plt.xlabel('Năm', fontsize=12)
plt.ylabel('Phần trăm (%)', fontsize=12)
plt.xticks(df_re['Year'].unique(), rotation=45)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('renewable_energy_trend.png')
plt.close()

print("\n🎉 Đã hoàn tất Mã Code 7. (Đầu ra: 2 Biểu đồ xu hướng và Số liệu thống kê).")