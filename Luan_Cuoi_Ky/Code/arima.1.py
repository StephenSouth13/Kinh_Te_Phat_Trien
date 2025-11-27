import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
warnings.filterwarnings("ignore")

# ============ Cấu hình ===================
DATA_FILE = r"D:\UEH\Kinh_Te_Phat_Trien\Luan_Cuoi_Ky\P_Data_Extract_From_World_Development_Indicators\2e666c17-c1b6-45ef-99cc-0fa89d21f0ef_Data.csv"
PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

FORECAST_END_YEAR = 2030
MIN_OBS = 8  # số quan sát tối thiểu

# ================= Load dữ liệu ===================
print("Load data...")
df_raw = pd.read_csv(DATA_FILE)
df_cleaned = df_raw.dropna(subset=['Series Code', 'Country Code', 'Country Name'])
year_columns = [c for c in df_cleaned.columns if '[YR' in c]

df_long = pd.melt(df_cleaned, 
                  id_vars=['Country Name','Country Code','Series Name','Series Code'], 
                  value_vars=year_columns, 
                  var_name='Year', value_name='Value')
df_long['Value'] = pd.to_numeric(df_long['Value'].replace('..', np.nan), errors='coerce')
df_long['Year'] = df_long['Year'].str.extract(r'(\d{4})').astype(float)
df_long.dropna(subset=['Year'], inplace=True)
df_long['Year'] = df_long['Year'].astype(int)

# ================= HÀM HỖ TRỢ ===================
def check_stationarity(series, name=""):
    """ADF & KPSS"""
    series_clean = series.dropna()
    if len(series_clean) < MIN_OBS:
        print(f"Không đủ dữ liệu (ít hơn {MIN_OBS} quan sát) cho {name}. Bỏ qua.")
        return None
    adf_res = adfuller(series_clean)
    kpss_res = kpss(series_clean, nlags="auto")
    print(f"{name} - ADF p-value: {adf_res[1]:.4f}, KPSS p-value: {kpss_res[1]:.4f}")
    return series_clean

def plot_series_and_acf(series, name):
    series_clean = series.dropna()
    if len(series_clean) < MIN_OBS:
        return
    lags = min(20, len(series_clean)//2)  # giới hạn lags ≤50% mẫu
    fig, axes = plt.subplots(1,2,figsize=(12,4))
    plot_acf(series_clean, ax=axes[0], lags=lags)
    plot_pacf(series_clean, ax=axes[1], lags=lags, method='ywm')
    axes[0].set_title("ACF")
    axes[1].set_title("PACF")
    fig.tight_layout()
    fn2 = os.path.join(PLOT_DIR, f"{name}_acf_pacf.png")
    fig.savefig(fn2)
    plt.close(fig)
    print(f"Đã lưu ACF/PACF: {fn2}")

def forecast_series(series, method="ETS"):
    series_clean = series.dropna()
    last_year = series_clean.index[-1]
    steps = FORECAST_END_YEAR - last_year
    if steps <= 0:
        print("Dữ liệu đã đến hoặc vượt quá năm dự báo.")
        return None

    if method.upper() == "ARIMA":
        model = ARIMA(series_clean, order=(1,1,0))
        fit = model.fit()
        forecast_values = fit.forecast(steps)
        conf_int = fit.get_forecast(steps).conf_int()
        lower = conf_int.iloc[:,0]
        upper = conf_int.iloc[:,1]
    elif method.upper() == "ETS":
        fit = ExponentialSmoothing(series_clean, trend=None, seasonal=None, initialization_method="estimated").fit()
        forecast_values = fit.forecast(steps)
        # ETS không có get_prediction, tạo CI ±10% giả định
        lower = forecast_values*0.9
        upper = forecast_values*1.1
    else:
        raise ValueError("Method must be ARIMA or ETS")

    forecast_df = pd.DataFrame({
        "Năm": range(last_year+1, FORECAST_END_YEAR+1),
        "Dự báo (Mean)": forecast_values.values,
        "Giới hạn Dưới 90%": lower.values,
        "Giới hạn Trên 90%": upper.values
    })
    return forecast_df

def plot_forecast(series, forecast_df, name):
    plt.figure(figsize=(10,6))
    series.plot(marker='o', label='Lịch sử')
    plt.plot(forecast_df['Năm'], forecast_df['Dự báo (Mean)'], linestyle='--', marker='o', color='orange', label='Dự báo ETS')
    plt.fill_between(forecast_df['Năm'], forecast_df['Giới hạn Dưới 90%'], forecast_df['Giới hạn Trên 90%'], color='grey', alpha=0.2, label='CI ±10%')
    plt.title(f"Dự báo {name} đến {FORECAST_END_YEAR}")
    plt.xlabel("Năm")
    plt.ylabel(name)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    fn = os.path.join(PLOT_DIR, f"{name}_forecast.png")
    plt.savefig(fn)
    plt.close()
    print(f"Đã lưu biểu đồ dự báo: {fn}")

# ================= XỬ LÝ CÁC CHỈ SỐ ===================
indicators = {
    "EG.FEC.RNEW.ZS": "Renewable Energy (%)",
    "EN.ATM.CO2E.PC.ZG": "CO2 per Capita Change (%)",
    "HD.HCI.OVRL": "Human Capital Index",
    "SP.DYN.LE00.IN": "Life Expectancy"
}

for code, pretty in indicators.items():
    print(f"\n=== XỬ LÝ: {code} ({pretty}) ===")
    df_tmp = df_long[(df_long['Country Name']=='Viet Nam') & (df_long['Series Code']==code)].sort_values('Year')
    if df_tmp.empty:
        print(f"Không tìm thấy dữ liệu cho {pretty}")
        continue
    ts_data = pd.Series(df_tmp['Value'].values, index=df_tmp['Year'])
    series_clean = check_stationarity(ts_data, pretty)
    if series_clean is None:
        continue
    plot_series_and_acf(series_clean, pretty)
    forecast_df = forecast_series(series_clean, method="ETS")
    if forecast_df is not None:
        print(forecast_df.to_markdown(index=False, floatfmt=".2f"))
        plot_forecast(series_clean, forecast_df, pretty)
        # Xuất ra Excel
        excel_fn = os.path.join(PLOT_DIR, f"{pretty.replace(' ','_')}_forecast.xlsx")
        forecast_df.to_excel(excel_fn, index=False)
        print(f"Đã xuất Excel: {excel_fn}")
