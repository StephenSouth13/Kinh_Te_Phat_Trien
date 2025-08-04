import pandas as pd
import matplotlib.pyplot as plt

# ===== 1. Đọc file CSV =====
df = pd.read_csv("vietnam_gdp.csv")

# ===== 2. Lọc dữ liệu theo Indicator Name =====
indicators = [
    "GDP growth (annual %)",
    "Gross fixed capital formation (annual % growth)"
]

df_filtered = df[df["Indicator Name"].isin(indicators)]

# ===== 3. Chọn cột năm =====
years = ['2020 [YR2020]', '2021 [YR2021]', '2022 [YR2022]', '2023 [YR2023]', '2024 [YR2024]']

# ===== 4. Chuyển đổi dữ liệu sang dạng số =====
df_filtered[years] = df_filtered[years].apply(pd.to_numeric, errors='coerce')

# ===== 5. Vẽ biểu đồ =====
plt.figure(figsize=(8, 5))

for _, row in df_filtered.iterrows():
    plt.plot(years, row[years], marker='o', label=row["Indicator Name"])

plt.title("Việt Nam - GDP growth & Gross fixed capital formation (2020–2024)")
plt.xlabel("Năm")
plt.ylabel("Tăng trưởng (%)")
plt.legend()
plt.grid(True)

# Hiển thị biểu đồ
plt.show()

# ===== 6. In dữ liệu và trung bình =====
print("\nDữ liệu sau khi lọc:")
print(df_filtered[["Indicator Name"] + years])

print("\nGiá trị trung bình mỗi chỉ số:")
for _, row in df_filtered.iterrows():
    mean_val = row[years].mean()
    print(f"{row['Indicator Name']}: {mean_val:.2f}%")
