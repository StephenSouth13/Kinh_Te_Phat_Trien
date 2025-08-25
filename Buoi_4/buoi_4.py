# buoi_4.py
import pandas as pd
import matplotlib.pyplot as plt
import os

# =========================
# 1. Đọc dữ liệu
# =========================
file_path = "NCKT_!.xlsx"
xl = pd.ExcelFile(file_path)
print("📂 Sheets có trong file:", xl.sheet_names)

# Sheet chính
df = xl.parse("Data")
print("📊 Kích thước sheet Data:", df.shape)

# =========================
# 2. Tiền xử lý
# =========================
print("📑 Các cột trong Data:", df.columns.tolist())

# Bỏ cột thừa nếu có
df_keep = df.drop(columns=["Country Code"], errors="ignore")

# Đặt Country Name làm index
df_gdp = df_keep.set_index("Country Name")

# Lấy danh sách năm (các cột toàn số)
years = [c for c in df_gdp.columns if str(c).isdigit()]
years = sorted(years)
print("📅 Các năm:", years[:5], "...", years[-5:])

# =========================
# 3. Việt Nam
# =========================
vn = df_gdp.loc["Vietnam", years].astype(float)
vn.to_csv("vietnam_growth_table_1985_2024.csv")
print("✅ Xuất CSV: vietnam_growth_table_1985_2024.csv")

plt.figure(figsize=(10,5))
plt.plot(years, vn, marker="o", label="Vietnam")
plt.title("Tăng trưởng GDP Việt Nam (1985–2024)")
plt.xlabel("Năm")
plt.ylabel("% tăng trưởng")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("vn_growth.png", dpi=300)
plt.close()
print("✅ Xuất ảnh: vn_growth.png")

# =========================
# 4. 7 quốc gia khác (China, Indonesia, Japan, Korea, Malaysia, Philippines, Thailand)
# =========================
countries = ["China", "Indonesia", "Japan", "Korea, Rep.", "Malaysia", "Philippines", "Thailand"]

df7 = df_gdp.loc[countries, years].astype(float).T  # transpose để Year × Country
df7.to_csv("seven_countries_growth_panel_1985_2024.csv")
print("✅ Xuất CSV: seven_countries_growth_panel_1985_2024.csv")

plt.figure(figsize=(12,6))
for c in countries:
    plt.plot(years, df7[c], label=c)
plt.title("So sánh tăng trưởng GDP (1985–2024)")
plt.xlabel("Năm")
plt.ylabel("% tăng trưởng")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("seven_countries_growth.png", dpi=300)
plt.close()
print("✅ Xuất ảnh: seven_countries_growth.png")

# =========================
# 5. Trung bình nhóm 7 quốc gia
# =========================
avg7 = df7.mean(axis=1)
avg7.to_csv("avg_7countries_growth_1985_2024.csv")
print("✅ Xuất CSV: avg_7countries_growth_1985_2024.csv")

plt.figure(figsize=(10,5))
plt.plot(years, avg7, color="red", linewidth=2.5, label="Average of 7 countries")
plt.title("Tăng trưởng GDP trung bình 7 quốc gia (1985–2024)")
plt.xlabel("Năm")
plt.ylabel("% tăng trưởng")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("avg_7countries_growth.png", dpi=300)
plt.close()
print("✅ Xuất ảnh: avg_7countries_growth.png")

# =========================
# 6. Tổng kết
# =========================
print("\n🎯 Kết quả chính:")
print(f"Trung bình Việt Nam 1985–2024: {vn.mean():.3f}%")
print(f"Trung bình 7 quốc gia 1985–2024: {avg7.mean():.3f}%")
