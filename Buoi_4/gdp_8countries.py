import pandas as pd
import matplotlib.pyplot as plt
import os

# ==============================
# 1. Đọc dữ liệu
# ==============================
file_path = "NCKT_!.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ Không tìm thấy file: {file_path}")

df = pd.read_excel(file_path, sheet_name="Data")

# ==============================
# 2. Tiền xử lý
# ==============================
years = [col for col in df.columns if col.startswith(tuple(str(y) for y in range(1960, 2030)))]
if not years:
    raise ValueError("⚠️ Không tìm thấy cột năm!")

df_gdp = df[df["Series Name"].str.contains("GDP growth", case=False, na=False)].copy()
df_gdp = df_gdp.set_index("Country Name")

# ==============================
# 3. Danh sách nước
# ==============================
countries = [
    "China", "Thailand", "Indonesia", "Malaysia",
    "Philippines", "Singapore", "Japan", "Korea, Rep."
]

special_entities = ["World", "ASEAN members"]
all_entities = countries + special_entities

# ==============================
# 4. Tạo DataFrame chứa dữ liệu
# ==============================
data = pd.DataFrame()

for c in all_entities:
    if c in df_gdp.index:
        data[c] = pd.to_numeric(df_gdp.loc[c, years], errors="coerce")
    else:
        print(f"⚠️ Không tìm thấy: {c}")

# ==============================
# 5. Tính trung bình
# ==============================
avg_growth = data.mean()
print("\n📊 Tăng trưởng trung bình (%):")
print(avg_growth.round(2))

# Lưu CSV
out_csv = "other_countries_growth.csv"
data.to_csv(out_csv)
print(f"✅ Đã lưu dữ liệu: {out_csv}")

# ==============================
# 6. Vẽ biểu đồ
# ==============================
plt.figure(figsize=(14, 7))

# Vẽ 8 nước
for c in countries:
    if c in data.columns:
        plt.plot(data.index, data[c], linestyle="-", alpha=0.8, label=c)

# Vẽ World & ASEAN nổi bật
for c in special_entities:
    if c in data.columns:
        plt.plot(data.index, data[c], linestyle="--", linewidth=2.5, label=c)

plt.title("GDP Growth Comparison (1985–2024) - Other Countries", fontsize=16, weight="bold")
plt.xlabel("Year")
plt.ylabel("GDP Growth (%)")
plt.xticks(rotation=45)
plt.legend(loc="best")
plt.grid(True, linestyle="--", alpha=0.6)

# Lưu ảnh
out_png = "other_countries_growth.png"
plt.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"✅ Đã lưu biểu đồ: {out_png}")

plt.show()
