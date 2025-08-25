import pandas as pd
import matplotlib.pyplot as plt
import os

# === Đường dẫn file Excel ===
file_path = r"D:\Code linh tinh\KINHTEPHATTRIEN\Kinh_Te_Phat_Trien\Buoi_4\NCKT_!.xlsx"
sheet_name = "Data"

# === Chỉ tiêu cần lấy ===
target_indicators = {
    "NE.GDI.TOTL.KD": "Gross capital formation (constant 2015 US$)",
    "NE.GDI.TOTL.ZS": "Gross capital formation (% of GDP)",
    "NY.GNS.ICTR.ZS": "Gross savings (% of GDP)"
}

# === Đọc dữ liệu ===
df = pd.read_excel(file_path, sheet_name=sheet_name)

print("Các cột dữ liệu:", df.columns.tolist())

# Lọc dữ liệu Việt Nam
df_vn = df[df["Country Name"] == "Vietnam"]

# Chỉ giữ các chỉ tiêu quan tâm
df_vn = df_vn[df_vn["Series Code"].isin(target_indicators.keys())]

# Giữ lại từ 1985 đến 2024
year_cols = [col for col in df_vn.columns if col.startswith(tuple(str(y) for y in range(1985, 2025)))]

# Chuyển từ wide → long
df_long = df_vn.melt(
    id_vars=["Country Name", "Series Name", "Series Code"],
    value_vars=year_cols,
    var_name="Year",
    value_name="Value"
)

# Chuẩn hóa năm: "1985 [YR1985]" → 1985
df_long["Year"] = df_long["Year"].str.extract(r"(\d{4})").astype(int)

# Pivot bảng cho dễ đọc
df_pivot = df_long.pivot_table(
    index="Year",
    columns="Series Name",
    values="Value"
)

# === Xuất ra file dữ liệu CSV ===
output_csv = "investment_ratio_vietnam.csv"
df_pivot.to_csv(output_csv, encoding="utf-8-sig")
print(f"Đã xuất dữ liệu ra {output_csv}")

# === Vẽ biểu đồ ===
plt.figure(figsize=(12, 6))
for col in df_pivot.columns:
    plt.plot(df_pivot.index, df_pivot[col], marker="o", label=col)

plt.title("Investment & Savings Indicators - Vietnam (1985-2024)", fontsize=14, weight="bold")
plt.xlabel("Year")
plt.ylabel("Value")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()

# Lưu ảnh
output_png = "investment_ratio_vietnam.png"
plt.savefig(output_png, dpi=300)
plt.show()

print(f"Đã lưu biểu đồ ra {output_png}")
