import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import numpy as np

# TÊN FILE THÔ (File đã xác nhận có dữ liệu Việt Nam)
file_data = "D:\\UEH\\Kinh_Te_Phat_Trien\\Luan_Cuoi_Ky\\P_Data_Extract_From_World_Development_Indicators\\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv" 
df_raw = pd.read_csv(file_data)

# =========================================================
# 1. LÀM SẠCH VÀ LỌC DỮ LIỆU CẦN THIẾT
# =========================================================
df_cleaned = df_raw.dropna(subset=['Series Code', 'Country Code', 'Country Name']).copy()

# Chuyển đổi từ Wide sang Long format (bắt buộc cho Time Series)
year_columns = [col for col in df_cleaned.columns if '[YR' in col]
df_long = pd.melt(df_cleaned, id_vars=['Country Name', 'Country Code', 'Series Name', 'Series Code'], value_vars=year_columns, var_name='Year', value_name='Value')

# Làm sạch Value và chuyển sang số thực
df_long['Value'] = df_long['Value'].replace('..', np.nan)
df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')


# 2. Lọc chuỗi thời gian của Việt Nam (Renewable Energy %)
re_code = 'EG.FEC.RNEW.ZS'
df_ts = df_long[
    (df_long['Country Name'] == 'Viet Nam') & 
    (df_long['Series Code'] == re_code)
].dropna(subset=['Value']).sort_values(by='Year')

ts_data = df_ts.set_index('Year')['Value']


# 3. KIỂM ĐỊNH ADF (BƯỚC ĐÃ CHẠY)
adf_result = adfuller(ts_data)
p_value = adf_result[1]
print("=============================================================")
print(f"| 4.2. KIỂM ĐỊNH TÍNH DỪNG (ADF): P-VALUE = {p_value:.4f}  |")
print("=============================================================")
if p_value > 0.05:
    print("=> Kết luận: Dữ liệu KHÔNG CÓ TÍNH DỪNG. Chọn d=1.")
    order = (1, 1, 0) # Sử dụng d=1 cho ARIMA(p, d, q)
else:
    print("=> Kết luận: Dữ liệu CÓ TÍNH DỪNG. Chọn d=0.")
    order = (1, 0, 0) # Trường hợp lý tưởng, nhưng không xảy ra


# 4. XÂY DỰNG VÀ DỰ BÁO MÔ HÌNH ARIMA(1, 1, 0)
model = ARIMA(ts_data, order=order)
model_fit = model.fit()

# 5. In tóm tắt kết quả (cho Mục 4.4)
print("\n--- 4.4. Tóm tắt Mô hình ARIMA(1, 1, 0) ---")
print(model_fit.summary())

# 6. Dự báo đến năm 2030 (9 bước dự báo, do dữ liệu kết thúc năm 2021)
forecast_steps = 9 
forecast_result = model_fit.get_forecast(steps=forecast_steps)
forecast_mean = forecast_result.predicted_mean
conf_int = forecast_result.conf_int()
last_year = ts_data.index.max()
forecast_years = range(last_year + 1, last_year + 1 + forecast_steps)

# 7. Kết quả Dự báo (cho Mục 4.4)
df_forecast = pd.DataFrame({
    'Năm': forecast_years,
    'Dự báo (Mean)': forecast_mean.values,
    'Giới hạn Dưới 95%': conf_int.iloc[:, 0].values,
    'Giới hạn Trên 95%': conf_int.iloc[:, 1].values
})
df_forecast['Dự báo (Mean)'] = df_forecast['Dự báo (Mean)'].round(2)
df_forecast['Giới hạn Dưới 95%'] = df_forecast['Giới hạn Dưới 95%'].round(2)
df_forecast['Giới hạn Trên 95%'] = df_forecast['Giới hạn Trên 95%'].round(2)

print("\n--- 4.4. Kết quả Dự báo Renewable Energy (%) đến 2030 ---")
print(df_forecast.to_markdown(index=False, numalign="left", stralign="left"))


# 8. Vẽ biểu đồ Dự báo (cho Mục 4.4)
plt.figure(figsize=(10, 6))
plt.plot(ts_data.index, ts_data.values, label='Dữ liệu Thực tế (2015-2021)', color='blue')
plt.plot(df_forecast['Năm'], df_forecast['Dự báo (Mean)'], label='Dự báo ARIMA(1, 1, 0)', color='red', linestyle='--')
plt.fill_between(df_forecast['Năm'], df_forecast['Giới hạn Dưới 95%'], df_forecast['Giới hạn Trên 95%'], color='red', alpha=0.1, label='Khoảng Tin cậy 95%')

plt.title('Dự báo Tỷ lệ Năng lượng Tái tạo của Việt Nam (2022-2030)', fontsize=14)
plt.xlabel('Năm', fontsize=12)
plt.ylabel('Renewable Energy Consumption (%)', fontsize=12)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('arima_forecast_renewable_energy.png')

print("\nĐã tạo biểu đồ Dự báo ARIMA (arima_forecast_renewable_energy.png).")