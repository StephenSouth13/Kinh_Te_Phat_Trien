"""
main.py
Full pipeline:
- Read WDI-style Excel (1986-2024)
- Compute per-5-year metrics: gM, gT, (I/Y)_T, gM-gT, ICOR (ratio and incremental)
- Export CSVs, plots, maps
- Forecast next 5 years (2025-2029) for GDP growth and Gross capital formation
- Print conclusions
"""

import os
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Forecasting
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Mapping
import geopandas as gpd

# -------------------------
# CONFIG
# -------------------------
FILE_PATH = "P_Data_Extract_From_World_Development_Indicators.xlsx"  # <- Thay tên file Excel của bạn
OUTPUT_DIR = Path("output_wdi_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

# Indicators to use (case-insensitive search)
IND_GDP = "GDP growth (annual %)"
IND_GCF = "Gross capital formation (% of GDP)"

YEARS_FROM = 1986
YEARS_TO = 2024
FORECAST_HORIZON = 5  # dự báo 5 năm (2025-2029)

# -------------------------
# Helpers
# -------------------------
def ensure_cols_years(cols, start=YEARS_FROM, end=YEARS_TO):
    """Return list of year column names that are present in cols (may contain '1986 [YR1986]' etc.)"""
    years = []
    for y in range(start, end+1):
        for c in cols:
            if str(y) in str(c):
                years.append(c)
                break
    return years

def period_5yr(year):
    start = (int(year) // 5) * 5
    return f"{start}-{start+4}"

def safe_icor(i_y_pct, g_pct):
    """ICOR approx = (I/Y) / g  where g as decimal (g_pct in %). Return np.nan when invalid."""
    if pd.isna(i_y_pct) or pd.isna(g_pct):
        return np.nan
    if abs(g_pct) < 1e-6:
        return np.nan
    return (i_y_pct / 100.0) / (g_pct / 100.0)  # -> unitless

# -------------------------
# 1) Read & identify year columns
# -------------------------
print("1) Reading file:", FILE_PATH)
df_raw = pd.read_excel(FILE_PATH)

# identify year-like columns present
year_cols = ensure_cols_years(df_raw.columns, YEARS_FROM, YEARS_TO)
if not year_cols:
    raise SystemExit("Không tìm thấy cột năm trong file. Kiểm tra tên cột (cần chứa 1986..2024).")

# meta columns = those not year_cols
meta_cols = [c for c in df_raw.columns if c not in year_cols]
print(f"Detected meta columns: {meta_cols}")
print(f"Detected {len(year_cols)} year columns from {YEARS_FROM} to {YEARS_TO} (may include bracketed names).")

# Keep only meta + year cols
df = df_raw[meta_cols + year_cols].copy()

# Replace World Bank missing marker
df.replace("..", np.nan, inplace=True)

# melt -> long
df_long = df.melt(id_vars=meta_cols, value_vars=year_cols, var_name="Year_raw", value_name="Value")
df_long["Year"] = df_long["Year_raw"].astype(str).str.extract(r"(\d{4})").astype(float).astype(int)
df_long = df_long[(df_long["Year"] >= YEARS_FROM) & (df_long["Year"] <= YEARS_TO)].copy()

# numeric
df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")

# -------------------------
# 2) Extract the two indicators
# -------------------------
print("2) Filtering indicators...")
mask_gdp = df_long["Series Name"].str.contains("GDP growth", case=False, na=False)
mask_gcf = df_long["Series Name"].str.contains("Gross capital formation", case=False, na=False)

df_gdp = df_long[mask_gdp].copy()
df_gcf = df_long[mask_gcf].copy()

if df_gdp.empty or df_gcf.empty:
    raise SystemExit("Không tìm thấy một trong hai chỉ số GDP hoặc Gross capital formation. Kiểm tra tên 'Series Name' trong file.")

# keep useful columns and rename
df_gdp = df_gdp.rename(columns={"Country Name": "Country", "Value": "GDP_growth"})[["Country", "Country Code", "Year", "GDP_growth"]]
df_gcf = df_gcf.rename(columns={"Country Name": "Country", "Value": "GCF_percent"})[["Country", "Country Code", "Year", "GCF_percent"]]

# -------------------------
# 3) Merge annual series and compute additional annual fields
# -------------------------
print("3) Merging annual series...")
df_ann = pd.merge(df_gdp, df_gcf, on=["Country", "Country Code", "Year"], how="outer", validate="1:1")
df_ann = df_ann.sort_values(["Country", "Year"]).reset_index(drop=True)

# compute annual delta Investment & delta GDP for later incremental ICOR per country-year
df_ann["Delta_GCF_pct"] = df_ann.groupby("Country")["GCF_percent"].diff()  # difference in % points
df_ann["Delta_GDP_growth"] = df_ann.groupby("Country")["GDP_growth"].diff()  # difference in growth percentage points

# -------------------------
# 4) Aggregate to 5-year periods (period label e.g., 1990-1994)
# -------------------------
print("4) Aggregating to 5-year periods...")
df_ann["Period"] = df_ann["Year"].apply(period_5yr)

# We'll compute per period: gM (mean of GDP_growth), gT (GDP growth in year max), (I/Y)_T (GCF_percent in year max)
def compute_period_metrics(group):
    # group is rows for a country & period (years in that 5-year bucket)
    years = group["Year"].dropna().unique()
    if len(group) == 0:
        return pd.Series({
            "gM": np.nan, "gT": np.nan, "(I/Y)_T": np.nan,
            "gM_minus_gT": np.nan, "ICOR_ratio": np.nan, "ICOR_incremental": np.nan,
            "n_obs": 0
        })
    gM = group["GDP_growth"].mean(skipna=True)
    # pick gT and IY_T from the **latest available year** in the group
    latest_idx = group["Year"].idxmax()
    gT = group.loc[latest_idx, "GDP_growth"]
    IyT = group.loc[latest_idx, "GCF_percent"]
    gm_minus_gt = gM - gT
    icor_ratio = safe_icor(IyT, gM)  # using period-average gM as denominator (common approach)
    # incremental ICOR for the period: sum delta I over sum delta Y across period years (use group diffs)
    # We'll compute: sum(ΔI) / sum(ΔY) where ΔI in absolute units approximated by %points * Y? Because we only have %GCF, use approximation:
    # Here we use Δ(GCF%) / Δ(GDPgrowth) as a rough incremental metric (not perfect). We'll aggregate year diffs present in group.
    deltaI = group["Delta_GCF_pct"].sum(skipna=True)
    deltaY = group["Delta_GDP_growth"].sum(skipna=True)
    icor_incremental = np.nan
    if pd.notna(deltaI) and pd.notna(deltaY) and abs(deltaY) > 1e-6:
        icor_incremental = (deltaI/100.0) / (deltaY/100.0)  # similar unitless ratio
    return pd.Series({
        "gM": gM,
        "gT": gT,
        "(I/Y)_T": IyT,
        "gM_minus_gT": gm_minus_gt,
        "ICOR_ratio": icor_ratio,
        "ICOR_incremental": icor_incremental,
        "n_obs": group["Year"].nunique()
    })

period_summary = df_ann.groupby(["Country", "Country Code", "Period"]).apply(compute_period_metrics).reset_index()

# Save period summary
period_summary.to_csv(OUTPUT_DIR / "period_summary_5yr.csv", index=False)
print("Saved period_summary_5yr.csv")

# -------------------------
# 5) Export annual merged series too
# -------------------------
df_ann.to_csv(OUTPUT_DIR / "annual_merged_series_1986_2024.csv", index=False)
print("Saved annual_merged_series_1986_2024.csv")

# -------------------------
# 6) Plots per country: (a) annual series, (b) period summary line+bar
# -------------------------
print("6) Drawing plots per country...")
countries = df_ann["Country"].unique()

for c in countries:
    df_c_ann = df_ann[df_ann["Country"] == c].set_index("Year").sort_index()
    df_c_per = period_summary[period_summary["Country"] == c].sort_values("Period")
    # skip if empty
    if df_c_ann["GDP_growth"].dropna().empty:
        continue

    # Annual timeseries plot
    plt.figure(figsize=(10,6))
    plt.plot(df_c_ann.index, df_c_ann["GDP_growth"], marker='o', label='GDP growth (%)')
    plt.plot(df_c_ann.index, df_c_ann["GCF_percent"], marker='s', label='GCF (% GDP)')
    plt.title(f"{c} — Annual GDP growth & GCF (1986-2024)")
    plt.xlabel("Year")
    plt.ylabel("Percent")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{c}_annual_series.png")
    plt.close()

    # Period summary plot
    plt.figure(figsize=(10,6))
    if not df_c_per.empty:
        plt.plot(df_c_per["Period"], df_c_per["gM"], marker='o', label='gM (avg 5y)')
        plt.plot(df_c_per["Period"], df_c_per["gT"], marker='s', label='gT (last year of period)')
        plt.bar(df_c_per["Period"], df_c_per["(I/Y)_T"], alpha=0.25, label='(I/Y)_T (%)')
        plt.title(f"{c} — 5-year period summary")
        plt.xlabel("Period")
        plt.ylabel("Percent / Units")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"{c}_period_summary.png")
    plt.close()

print("Plots saved to", OUTPUT_DIR)

# -------------------------
# 7) Map: choropleth of latest ICOR_ratio by country
# -------------------------
print("7) Drawing world map of latest ICOR_ratio for countries present...")
# Prepare latest period per country
latest_period_of_country = period_summary.sort_values("Period").groupby("Country").tail(1)
# We need ISO3 codes to merge with geopandas world; use Country Code from file (usually ISO3)
latest_period_of_country = latest_period_of_country.rename(columns={"Country Code": "ISO_A3"})

# load geopandas world
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Some ISO codes in naturalearth are uppercase, ensure match
latest_period_of_country["ISO_A3"] = latest_period_of_country["ISO_A3"].astype(str).str.upper()

map_df = world.merge(latest_period_of_country, left_on="iso_a3", right_on="ISO_A3", how="right")

# Plot choropleth
if not map_df.empty:
    fig, ax = plt.subplots(1, 1, figsize=(12,6))
    map_df.plot(column="ICOR_ratio", ax=ax, legend=True, missing_kwds={"color": "lightgrey"}, cmap="RdYlBu")
    ax.set_title("Latest ICOR_ratio by country (period latest available)")
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "map_icor_ratio_latest.png")
    plt.close()
    print("Map saved:", OUTPUT_DIR / "map_icor_ratio_latest.png")
else:
    print("No matching countries for map (ISO mismatch?) — check Country Code values.")

# -------------------------
# 8) Forecasting (annual) 2025-2029 for GDP_growth and GCF_percent per country
#    We'll use ExponentialSmoothing (simple and robust); save forecasts and forecast plots
# -------------------------
print("8) Forecasting next 5 years for each country (ExponentialSmoothing)...")
forecast_rows = []
for c in countries:
    s_ann = df_ann[df_ann["Country"] == c].sort_values("Year")
    if s_ann["GDP_growth"].dropna().shape[0] < 10:
        # too few points for stable forecast; skip or use naive mean
        continue

    # GDP growth model
    y_gdp = s_ann.set_index("Year")["GDP_growth"].astype(float)
    y_gcf = s_ann.set_index("Year")["GCF_percent"].astype(float)

    # fit model for GDP if at least 8 non-na values
    try:
        model_gdp = ExponentialSmoothing(y_gdp.dropna(), trend="add", seasonal=None, damped_trend=True)
        fit_gdp = model_gdp.fit(optimized=True)
        f_gdp = fit_gdp.forecast(FORECAST_HORIZON)
    except Exception:
        # fallback to last value repeated
        last = y_gdp.dropna().iloc[-1]
        f_gdp = pd.Series([last]*FORECAST_HORIZON, index=range(y_gdp.index.max()+1, y_gdp.index.max()+1+FORECAST_HORIZON))

    try:
        model_gcf = ExponentialSmoothing(y_gcf.dropna(), trend="add", seasonal=None, damped_trend=True)
        fit_gcf = model_gcf.fit(optimized=True)
        f_gcf = fit_gcf.forecast(FORECAST_HORIZON)
    except Exception:
        last = y_gcf.dropna().iloc[-1] if not y_gcf.dropna().empty else np.nan
        f_gcf = pd.Series([last]*FORECAST_HORIZON, index=range(y_gcf.index.max()+1, y_gcf.index.max()+1+FORECAST_HORIZON))

    # save rows
    for yr, val_gdp in f_gdp.items():
        val_gcf = f_gcf.get(yr, np.nan)
        forecast_rows.append({
            "Country": c,
            "Year": int(yr),
            "Forecast_GDP_growth": float(val_gdp) if pd.notna(val_gdp) else np.nan,
            "Forecast_GCF_percent": float(val_gcf) if pd.notna(val_gcf) else np.nan
        })

    # plot forecast + historical
    plt.figure(figsize=(10,6))
    plt.plot(y_gdp.index, y_gdp.values, label="GDP_growth (hist)", marker='o')
    plt.plot(f_gdp.index, f_gdp.values, label="GDP_growth (forecast)", marker='o', linestyle='--')
    plt.title(f"{c} — GDP growth: historical + forecast")
    plt.xlabel("Year"); plt.ylabel("%")
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{c}_forecast_gdp.png")
    plt.close()

    plt.figure(figsize=(10,6))
    plt.plot(y_gcf.index, y_gcf.values, label="GCF% (hist)", marker='s')
    plt.plot(f_gcf.index, f_gcf.values, label="GCF% (forecast)", marker='s', linestyle='--')
    plt.title(f"{c} — Gross capital formation (% GDP): historical + forecast")
    plt.xlabel("Year"); plt.ylabel("%")
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{c}_forecast_gcf.png")
    plt.close()

# save forecast
df_forecast = pd.DataFrame(forecast_rows)
df_forecast.to_csv(OUTPUT_DIR / "forecast_annual_2025_2029.csv", index=False)
print("Saved forecast_annual_2025_2029.csv")

# -------------------------
# 9) Auto conclusions (simple heuristic)
# -------------------------
print("\n9) Generating automatic conclusions (heuristic):\n")
summary_lines = []
for c in countries:
    per_c = period_summary[period_summary["Country"] == c].sort_values("Period")
    if per_c.empty:
        continue
    latest = per_c.tail(1).iloc[0]
    gm = latest["gM"]
    gt = latest["gT"]
    iy = latest["(I/Y)_T"]
    icor_r = latest["ICOR_ratio"]
    icor_inc = latest["ICOR_incremental"]

    # heuristics
    trend_desc = "tăng" if (not pd.isna(gt) and not pd.isna(gm) and gt > gm) else "giảm" if (not pd.isna(gt) and not pd.isna(gm)) else "không rõ"
    icor_desc = "ICOR thấp (hiệu quả vốn cao)" if (pd.notna(icor_r) and icor_r < 3) else ("ICOR trung bình" if (pd.notna(icor_r) and icor_r < 6) else ("ICOR cao (hiệu quả đầu tư thấp)" if pd.notna(icor_r) else "ICOR không xác định"))
    line = f"- {c} ({latest['Period']}): gM={gm:.2f}%  gT={gt:.2f}%  (I/Y)_T={iy:.2f}%  => xu hướng: {trend_desc}. {icor_desc} (ICOR_ratio={icor_r if not pd.isna(icor_r) else 'NaN'})."
    summary_lines.append(line)
    print(line)

# also dump text summary file
with open(OUTPUT_DIR / "auto_conclusion.txt", "w", encoding="utf-8") as f:
    f.write("AUTO CONCLUSIONS\n\n")
    f.write("\n".join(summary_lines))

print("\nAll outputs saved in folder:", OUTPUT_DIR.resolve())
print("Files of interest:")
for p in sorted(OUTPUT_DIR.iterdir()):
    print(" -", p.name)



# Link dữ liệu mới
url = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip"

# Đọc trực tiếp từ URL (GeoPandas hỗ trợ)
world = gpd.read_file(url)

world = world.merge(latest_icor_df, left_on='ADMIN', right_on='Country Name', how='left')
fig, ax = plt.subplots(1, 1, figsize=(15, 8))
world.plot(column='ICOR_ratio', cmap='coolwarm', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
plt.title("Bản đồ ICOR các nước", fontsize=16)
plt.savefig("output_wdi_analysis/world_icor_map.png", dpi=300)
plt.close()


# growth in Viet Nam

# End
