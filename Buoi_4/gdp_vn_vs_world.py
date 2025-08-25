import pandas as pd
import matplotlib.pyplot as plt
import os

# ==============================
# 1. Đọc dữ liệu
# ==============================
file_path = "NCKT_!.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ Không tìm thấy file: {file_path}")

xls = pd.ExcelFile(file_path)
print("📂 Sheets có trong file:", xls.sheet_names)

df = pd.read_excel(file_path, sheet_name="Data")
print("📊 Kích thước sheet Data:", df.shape)

# ==============================
# 2. Tiền xử lý
# ==============================
years = [col for col in df.columns if col.startswith(tuple(str(y) for y in range(1960, 2030)))]
if not years:
    raise ValueError("⚠️ Không tìm thấy cột năm!")

df_gdp = df[df["Series Name"].str.contains("GDP growth", case=False, na=False)].copy()
df_gdp = df_gdp.set_index("Country Name")

# ==============================
# 3. Lấy dữ liệu các nước
# ==============================
countries = [
    "Vietnam", "China", "Thailand", "Indonesia", 
    "Malaysia", "Philippines", "Singapore", 
    "Japan", "Korea, Rep."
]

# Chuẩn hóa: nếu "Vietnam" không có thì dùng "Viet Nam"
if "Vietnam" not in df_gdp.index and "Viet Nam" in df_gdp.index:
    countries[0] = "Viet Nam"

special_entities = ["World", "ASEAN members"]  # Thêm World + ASEAN

all_entities = countries + special_entities

# Tạo DataFrame chứa tất cả
data = pd.DataFrame()

for c in all_entities:
    if c in df_gdp.index:
        data[c] = pd.to_numeric(df_gdp.loc[c, years], errors="coerce")
    else:
        print(f"⚠️ Không tìm thấy: {c}")

# ==============================
# 4. Tính toán trung bình
# ==============================
avg_growth = data.mean()
print("\n📊 Tăng trưởng trung bình (%):")
print(avg_growth.round(2))

# Lưu kết quả ra CSV
out_csv = "countries_growth.csv"
data.to_csv(out_csv)
print(f"✅ Đã lưu dữ liệu: {out_csv}")

# ==============================
# 5. Vẽ biểu đồ so sánh
# ==============================
plt.figure(figsize=(14, 7))

for c in countries:
    if c in data.columns:
        plt.plot(data.index, data[c], linestyle="-", marker="", alpha=0.8, label=c)

# Vẽ World & ASEAN nổi bật
for c in special_entities:
    if c in data.columns:
        plt.plot(data.index, data[c], linestyle="--", linewidth=2.5, label=c)

# Vẽ đường trung bình VN
vn_avg = avg_growth[countries[0]]
plt.axhline(vn_avg, color="r", linestyle=":", label=f"{countries[0]} Avg {vn_avg:.2f}%")

plt.title(f"GDP Growth Comparison (1985–2024)", fontsize=16, weight="bold")
plt.xlabel("Year")
plt.ylabel("GDP Growth (%)")
plt.xticks(rotation=45)
plt.legend(loc="best")
plt.grid(True, linestyle="--", alpha=0.6)

# Lưu ảnh
out_png = "gdp_comparison.png"
plt.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"✅ Đã lưu biểu đồ: {out_png}")

plt.show()
