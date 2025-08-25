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

# Chuẩn hóa tên VN
vn_name = "Vietnam"
if vn_name not in df_gdp.index and "Viet Nam" in df_gdp.index:
    vn_name = "Viet Nam"

if vn_name not in df_gdp.index:
    raise ValueError("⚠️ Không tìm thấy dữ liệu Việt Nam trong file!")

# ==============================
# 3. Lấy dữ liệu VN
# ==============================
vn_data = pd.to_numeric(df_gdp.loc[vn_name, years], errors="coerce")

# ==============================
# 4. Tính trung bình
# ==============================
vn_avg = vn_data.mean()
print("\n🇻🇳 Tăng trưởng kinh tế trung bình Việt Nam (1985–2024):")
print(f"{vn_avg:.2f} %")

# Lưu ra CSV
out_csv = "vn_growth.csv"
vn_data.to_csv(out_csv, header=["GDP Growth (%)"])
print(f"✅ Đã lưu dữ liệu: {out_csv}")

# ==============================
# 5. Vẽ biểu đồ
# ==============================
plt.figure(figsize=(12, 6))
plt.plot(vn_data.index, vn_data.values, marker="o", linestyle="-", color="b", label="Việt Nam")
plt.axhline(vn_avg, color="r", linestyle="--", label=f"Trung bình {vn_avg:.2f}%")

plt.title("GDP Growth of Vietnam (1985–2024)", fontsize=16, weight="bold")
plt.xlabel("Năm")
plt.ylabel("GDP Growth (%)")
plt.xticks(rotation=45)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()

# Lưu biểu đồ
out_png = "vn_growth.png"
plt.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"✅ Đã lưu biểu đồ: {out_png}")

plt.show()
