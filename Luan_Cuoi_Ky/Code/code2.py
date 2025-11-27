import pandas as pd
import numpy as np

# =========================================================
# 1. FILE NGUỒN DỮ LIỆU
# =========================================================
file_data = r"D:\UEH\Kinh_Te_Phat_Trien\Luan_Cuoi_Ky\P_Data_Extract_From_World_Development_Indicators\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv"

df = pd.read_csv(file_data)

# =========================================================
# 2. LOẠI BỎ DÒNG KHÔNG ĐẦY ĐỦ METADATA
# =========================================================
df_cleaned = df.dropna(subset=['Series Code', 'Country Code', 'Country Name']).copy()

# =========================================================
# 3. CHỌN 6 QUỐC GIA ASEAN TRONG NGHIÊN CỨU
# =========================================================
asean6 = [
    'Vietnam',
    'Thailand',
    'Malaysia',
    'Indonesia',
    'Philippines',
    'Singapore'
]

df_cleaned = df_cleaned[df_cleaned['Country Name'].isin(asean6)]

# =========================================================
# 4. DANH SÁCH 22 BIẾN ESG CHUẨN (E, S, G)
# =========================================================
esg_series = [
    # ---- Governance ----
    'CC.EST',  # Control of Corruption
    'GE.EST',  # Government Effectiveness 
    'RQ.EST',  # Regulatory Quality
    'RL.EST',  # Rule of Law
    'VA.EST',  # Voice & Accountability
    'PV.EST',  # Political Stability
    
    # ---- Environmental ----
    'EN.ATM.CO2E.KT',    # CO2 emissions (kt)
    'EN.ATM.METH.ZG',    # Methane emissions % vs 1990
    'PM25.MEAN',         # custom check / fallback if exists
    'EG.FEC.RNEW.ZS',    # Renewable energy (% final)
    'EG.ELC.RNEW.ZS',    # Renewable electricity output (%)
    'AG.LND.FRST.ZS',    # Forest area (% land)
    'EG.USE.PCAP.KG.OE', # Energy use per capita
    
    # ---- Social ----
    'SP.DYN.LE00.IN',     # Life Expectancy
    'HD.HCI.OVRL',        # Human Capital Index
    'SE.SEC.ENRR',        # School enrollment (secondary)
    'SI.POV.GINI',        # Gini Index
    'SL.TLF.ACTI.ZS',     # Labor force participation
    'SI.POV.NAHC',        # Poverty national line
    'SI.POV.LMIC.GP',     # Poverty $4.20/day
]

# Bộ lọc series tồn tại trong file
exist_series = df_cleaned['Series Code'].unique().tolist()
final_series = [s for s in esg_series if s in exist_series]

df_cleaned = df_cleaned[df_cleaned['Series Code'].isin(final_series)]

# =========================================================
# 5. CHỌN CỘT NĂM (2010–2023 HOẶC >= 2015)
# =========================================================
year_columns = [col for col in df_cleaned.columns if '[YR' in col]
# lọc chỉ lấy năm >= 2015
year_columns = [col for col in year_columns if int(col[:4]) >= 2015]

# =========================================================
# 6. CHUYỂN WIDE → LONG FORMAT
# =========================================================
df_long = pd.melt(
    df_cleaned,
    id_vars=['Country Name', 'Country Code', 'Series Name', 'Series Code'],
    value_vars=year_columns,
    var_name='Year',
    value_name='Value'
)

# =========================================================
# 7. LÀM SẠCH YEAR + VALUE
# =========================================================
df_long['Year'] = df_long['Year'].str.extract(r"(\d{4})").astype(int)

df_long['Value'] = df_long['Value'].replace('..', np.nan)
df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')

# =========================================================
# 8. XOÁ DỮ LIỆU TRỐNG HOÀN TOÀN
# =========================================================
df_long = df_long.dropna(subset=['Value'])

# =========================================================
# 9. LƯU FILE CHUẨN HÓA
# =========================================================
output_file = "esg_asean6_2015_2023_clean.csv"
df_long.to_csv(output_file, index=False)

print("🎉 Dữ liệu ESG (ASEAN6 – 2015-2023) đã xử lý hoàn tất!")
print(f"File lưu tại: {output_file}")

print("\nThông tin tổng quát:")
print(df_long.head())
print(df_long.tail())
print("\nCác biến đã được load:")
print(final_series)
