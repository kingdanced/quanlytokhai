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

# --- GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Tờ Khai", layout="wide")
st.title("🚀 Tra Cứu Tờ Khai Online")

# (Các hàm trích xuất dữ liệu giữ nguyên như cũ...)
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
    if not ma_dn: ma_dn = lay_gia_tri_theo_tu_khoa(df, "Mã", sau_dong_chu="Người nhập khẩu")
    so_tk = lay_gia_tri_theo_tu_khoa(df, "Số tờ khai")
    ngay_raw = lay_gia_tri_theo_tu_khoa(df, "Ngày đăng ký")
    dia_diem_luu_kho = lay_gia_tri_theo_tu_khoa(df, "Địa điểm lưu kho")
    ma_hq = dia_diem_luu_kho[:4] if dia_diem_luu_kho else ""
    ngay_tk = ngay_raw[:10] if ngay_raw else ""
    return [ma_dn, so_tk, ngay_tk, ma_hq]

uploaded_files = st.file_uploader("Tải file Excel", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    data_list = []
    for f in uploaded_files:
        res = trich_xuat_du_lieu(f)
        data_list.append({"File": f.name, "MST": res[0], "Số TK": res[1], "Ngày": res[2], "Mã HQ": res[3]})
    
    df_result = pd.DataFrame(data_list)
if uploaded_files:
    # Tất cả các dòng dưới đây phải được thụt lề vào 4 khoảng trắng
    data_list = []  
    for f in uploaded_files:
        res = trich_xuat_du_lieu(f)
        data_list.append({
            "File": f.name, 
            "MST": res[0], 
            "Số TK": res[1], 
            "Ngày": res[2], 
            "Mã HQ": res[3]
        })
    
    df_result = pd.DataFrame(data_list)
    # Tiếp tục các lệnh hiển thị...

    # --- HIỂN THỊ DỌC ---
    st.subheader("📋 Chi tiết thông tin trích xuất")
    
    # Cho người dùng chọn file trước
    target_file = st.selectbox("Chọn file muốn kiểm tra & chạy:", df_result["File"])
    
    # Lấy dữ liệu của file được chọn
    row = df_result[df_result["File"] == target_file].iloc[0]

    # Tạo giao diện hiển thị dọc bằng Markdown và Columns
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"""
        **Mã số thuế:** **Số tờ khai:** **Ngày đăng ký:** **Mã Hải quan:**
        """)
    with col2:
        st.success(f"""
        {row['MST']}  
        {row['Số TK']}  
        {row['Ngày']}  
        {row['Mã HQ']}
        """)

    if st.button("🔥 Chạy trên Server"):
        # Giữ nguyên phần code Selenium của bạn ở đây...

    if st.button("🔥 Chạy trên Server"):
        row = df_result[df_result["File"] == target_file].iloc[0]
        
        # --- ĐÂY LÀ CHỖ THÊM CODE MỚI ---
        options = Options()
        options.add_argument("--headless") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")

        try:
            # Thử khởi tạo theo môi trường Linux của Streamlit Cloud
            try:
                service = Service("/usr/bin/chromium-browser")
                driver = webdriver.Chrome(service=service, options=options)
            except:
                driver = webdriver.Chrome(options=options)
            
            driver.get("https://pus.customs.gov.vn/faces/ContainerBarcode")
            
            # Điền form ẩn (Headless)
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
            inputs = driver.find_elements(By.TAG_NAME, "input")
            visible_inputs = [i for i in inputs if i.is_displayed() and i.get_attribute("type") == "text"]

            if len(visible_inputs) >= 4:
                vals = [row["MST"], row["Số TK"], row["Mã HQ"], row["Ngày"]]
                for idx, v in enumerate(vals):
                    driver.execute_script("arguments[0].value = arguments[1];", visible_inputs[idx], v)
                
                st.success("✅ Server đã điền xong dữ liệu ngầm!")
                st.warning("⚠️ Lưu ý: Vì chạy ẩn trên mạng nên bạn sẽ không thấy trình duyệt hiện ra để nhập Captcha.")
            
            driver.quit() # Đóng trình duyệt ẩn
        except Exception as e:
            st.error(f"Lỗi khởi tạo trình duyệt trên Cloud: {e}")



