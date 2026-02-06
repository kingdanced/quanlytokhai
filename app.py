import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Tờ Khai", layout="wide")
st.title("🚀 Tra Cứu Tờ Khai Online")

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
    return [ma_dn, so_tk, ngay_tk, ma_hq]

uploaded_files = st.file_uploader("Tải file Excel", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    data_list = []
    for f in uploaded_files:
        res = trich_xuat_du_lieu(f)
        data_list.append({"
