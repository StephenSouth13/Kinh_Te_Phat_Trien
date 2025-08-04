import pandas as pd
import matplotlib.pyplot as plt

file_path = "vietnam_data_with_meta.csv"

# ==== 1. Đọc file CSV dạng raw để tách 2 phần ====
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Xác định vị trí metadata
meta_start = None
for i, line in enumerate(lines):
    if line.startswith("Code,License Type"):
        meta_start = i
        break

# Tách dữ liệu & metadata
data_lines = lines[:meta_start-1]  # trừ dòng trống trước metadata
meta_lines = lines[meta_start:]

# Lưu tạm ra file riêng
with open("data_only.csv", "w", encoding="utf-8") as f:
    f.writelines(data_lines)

with open("meta_only.csv", "w", encoding="utf-8") as f:
    f.writelines(meta_lines)

# ==== 2. Đọc 2 file này ====
df_data = pd.read_csv("data_only.csv")
df_meta = pd.read_csv("meta_only.csv")

# ==== 3. Lọc 2 chỉ số ====
indicators = [
    "GDP growth (annual %)",
    "Gross fixed capital formation (annual % growth)"
]
df_data = df_data[df_data["Series Name"].isin(indicators)]

# ==== 4. Ghép metadata ====
df = df_data.merge(
    df_meta[["Indicator Name", "Long definition"]],
    left_on="Series Name",
    right_on="Indicator Name",
    how="left"
)

# ==== 5. Chọn các cột năm ====
years = ['2020 [YR2020]', '2021 [YR2021]', '2022 [YR2022]', '2023 [YR2023]', '2024 [YR2024]']
df[years] = df[years].apply(pd.to_numeric, errors='coerce')

# ==== 6. Tính ICOR ====
gdp_growth = df[df["Series Name"] == "GDP growth (annual %)"][years].values.flatten()
gfcf_growth = df[df["Series Name"] == "Gross fixed capital formation (annual % growth)"][years].values.flatten()
icor = gfcf_growth / gdp_growth

# ==== 7. Vẽ biểu đồ ====
plt.figure(figsize=(9, 5))
plt.plot(years, gdp_growth, marker='o', label="GDP growth (%)")
plt.plot(years, gfcf_growth, marker='o', label="Gross fixed capital formation growth (%)")
plt.plot(years, icor, marker='o', label="ICOR (≈ GFCF growth / GDP growth)")

plt.title("Việt Nam - GDP, GFCF & ICOR (2020–2024)")
plt.xlabel("Năm")
plt.ylabel("Giá trị")
plt.grid(True)
plt.legend()
plt.show()

# ==== 8. In bảng số liệu ====
df_icor = pd.DataFrame({
    "Năm": [y.split()[0] for y in years],
    "GDP growth (%)": gdp_growth,
    "GFCF growth (%)": gfcf_growth,
    "ICOR": icor
})
print(df_icor)
