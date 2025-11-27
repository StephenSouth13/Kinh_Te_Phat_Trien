import pandas as pd
import numpy as np

# Tên file dữ liệu thô (có sẵn trong Phụ lục)
file_data = "D:\\UEH\\Kinh_Te_Phat_Trien\\Luan_Cuoi_Ky\\P_Data_Extract_From_World_Development_Indicators\\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv"

# 1. Đọc file CSV và làm sạch các dòng thiếu metadata quan trọng
df = pd.read_csv(file_data)
df_cleaned = df.dropna(subset=['Series Code', 'Country Code', 'Country Name']).copy()

# 2. Xác định các cột năm và Chuyển đổi từ định dạng Wide sang Long
# Các cột năm được nhận diện qua chuỗi '[YR'
year_columns = [col for col in df_cleaned.columns if '[YR' in col]

df_long = pd.melt(
    df_cleaned,
    id_vars=['Country Name', 'Country Code', 'Series Name', 'Series Code'],
    value_vars=year_columns,
    var_name='Year',
    value_name='Value'
)

# 3. Làm sạch cột 'Year' và 'Value'
# Trích xuất 4 chữ số năm từ tên cột (ví dụ: '2015 [YR2015]')
df_long['Year'] = df_long['Year'].str.extract(r'(\d{4})').astype(int)

# Thay thế giá trị thiếu '..' bằng NaN (Not a Number)
df_long['Value'] = df_long['Value'].replace('..', np.nan) 

# Chuyển đổi cột 'Value' sang kiểu số thực (float)
df_long['Value'] = pd.to_numeric(df_long['Value'])

# 4. Lưu DataFrame sạch cho phân tích (Dùng trong Chương 3, 4, 5)
df_long.to_csv("esg_analysis_long.csv", index=False)

print("Quy trình chuẩn hóa dữ liệu hoàn tất. Dữ liệu sẵn sàng cho phân tích.")