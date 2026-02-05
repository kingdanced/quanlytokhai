import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản Lý Tờ Khai", layout="wide")
st.title("🚀 Hệ Thống Điền Tờ Khai (Chế độ Chủ động)")

# --- HÀM TRÍCH XUẤT DỮ LIỆU ---
def lay_gia_tri_theo_tu_khoa(df, tu_khoa, sau_dong_chu=None):
    bat_dau_tim = False if sau_dong_chu else True
    for r in range(len(df)):
        row_str = " ".join([str(x) for x in df.iloc[r]])
        if sau_dong_chu and sau_dong_chu in row_str:
            bat_dau_tim = True
            continue
        if bat_dau_tim:
            for c in range(len(df.columns)):
                cell_val = str(df.iloc[r, c]).strip()
                if tu_khoa == cell_val or (len(tu_khoa) > 2 and tu_khoa in cell_val):
                    for offset in range(1, 10):
                        if c + offset < len(df.columns):
                            val = str(df.iloc[r, c + offset]).strip()
                            if val != "" and val.lower() != "nan":
                                return val
    return ""

def trich_xuat_du_lieu(file_buffer):
    df = pd.read_excel(file_buffer, header=None).fillna("")
    ma_dn = lay_gia_tri_theo_tu_khoa(df, "Mã", sau_dong_chu="Người xuất khẩu")
    if not ma_dn:
        ma_dn = lay_gia_tri_theo_tu_khoa(df, "Mã", sau_dong_chu="Người nhập khẩu")
    so_tk = lay_gia_tri_theo_tu_khoa(df, "Số tờ khai")
    ngay_raw = lay_gia_tri_theo_tu_khoa(df, "Ngày đăng ký")
    dia_diem_luu_kho = lay_gia_tri_theo_tu_khoa(df, "Địa điểm lưu kho")
    ma_hq = dia_diem_luu_kho[:4] if dia_diem_luu_kho else ""
    ngay_tk = ngay_raw[:10] if ngay_raw else ""
    return ma_dn, so_tk, ngay_tk, ma_hq

# --- GIAO DIỆN STREAMLIT ---
uploaded_files = st.file_uploader("Tải file Excel (chọn 1 hoặc nhiều file)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    data_list = []
    for f in uploaded_files:
        d = trich_xuat_du_lieu(f)
        data_list.append({"File": f.name, "MST": d[0], "Số TK": d[1], "Ngày": d[2], "Mã HQ": d[3]})
    
    df_tong_hop = pd.DataFrame(data_list)
    st.subheader("📋 Danh sách dữ liệu bóc tách")
    st.dataframe(df_tong_hop, use_container_width=True)

    # Chọn tờ khai muốn điền
    selected_file = st.selectbox("Chọn tờ khai để điền vào web:", df_tong_hop["File"])

    if st.button("🔥 Mở trình duyệt & Điền Form"):
        row = df_tong_hop[df_tong_hop["File"] == selected_file].iloc[0]
        
        with st.status("Đang khởi động Chrome...", expanded=True) as status:
            options = Options()
            options.add_experimental_option("detach", True) # Giữ trình duyệt sau khi chạy
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://pus.customs.gov.vn/faces/ContainerBarcode")
            driver.maximize_window()

            wait = WebDriverWait(driver, 20)
            try:
                # Chờ các ô nhập liệu xuất hiện
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
                inputs = driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = [i for i in inputs if i.is_displayed() and i.get_attribute("type") == "text"]
                
                if len(visible_inputs) >= 4:
                    st.write(f"📝 Đang điền dữ liệu cho file: {selected_file}")
                    vals = [row["MST"], row["Số TK"], row["Mã HQ"], row["Ngày"]]
                    for idx, v in enumerate(vals):
                        driver.execute_script("arguments[0].value = arguments[1];", visible_inputs[idx], v)
                    
                    status.update(label="✅ Đã điền xong! Hãy tự nhấn nút 'Lấy thông tin'.", state="complete")
                    st.success("Hệ thống đã điền xong thông tin. Bạn hãy kiểm tra lại và nhấn nút 'Lấy thông tin' trên trình duyệt Chrome nhé!")
                else:
                    st.error("❌ Không tìm thấy đủ các ô nhập liệu trên trang web.")
            except Exception as e:
                st.error(f"Lỗi Selenium: {e}")