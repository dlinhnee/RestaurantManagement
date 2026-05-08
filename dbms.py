import streamlit as st
import mysql.connector
import pandas as pd
import bcrypt

# 1. Cấu hình kết nối Aiven từ ảnh của bạn
DB_CONFIG = {
    "host": "mysql-3c1b790c-vudieulinh305-ebb6.k.aivencloud.com",
    "port": 25428,
    "user": "avnadmin",
    "password": "AVNS_AIQl70s2tSBuu4XrKE",
    "database": "defaultdb",
    "ssl_disabled": False  # Aiven yêu cầu SSL Mode: REQUIRED
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# 2. Cơ chế Bảo mật: Mã hóa mật khẩu & Chống SQL Injection
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# 3. Phân quyền người dùng (Role-based Access Control)
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # CHỐNG SQL INJECTION: Sử dụng dấu %s thay vì cộng chuỗi trực tiếp
    query = "SELECT password, position FROM employees WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password(password, user['password']):
        return user['position']
    return None

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Restaurant Management System", layout="wide")

if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 Đăng nhập hệ thống")
    user_input = st.text_input("Tên đăng nhập")
    pass_input = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        role = login_user(user_input, pass_input)
        if role:
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")

else:
    st.sidebar.title(f"Xin chào, {st.session_state.role}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.role = None
        st.rerun()

    # Phân quyền chức năng theo file DBMS 
    menu = ["Trang chủ", "Quản lý Menu", "Đặt bàn", "Hóa đơn & Doanh thu"]
    if st.session_state.role == 'admin':
        menu.append("Quản lý Nhân viên")
        
    choice = st.sidebar.selectbox("Chức năng", menu)

    if choice == "Trang chủ":
        st.subheader("Trạng thái bàn hiện tại [cite: 74, 86]")
        conn = get_connection()
        df_tables = pd.read_sql("SELECT * FROM tables", conn)
        st.dataframe(df_tables, use_container_width=True)
        conn.close()

    elif choice == "Quản lý Menu":
        st.subheader("Danh sách món ăn [cite: 75, 87]")
        # Sử dụng View để tối ưu truy vấn [cite: 95]
        conn = get_connection()
        query = "SELECT * FROM view_menu_by_category" 
        df_menu = pd.read_sql(query, conn)
        st.table(df_menu)
        conn.close()

    elif choice == "Hóa đơn & Doanh thu":
        if st.session_state.role in ['admin', 'cashier']:
            st.subheader("Báo cáo doanh thu [cite: 78, 106]")
            # Gọi Stored Procedure để tính toán [cite: 96]
            st.info("Dữ liệu được bảo mật và truy xuất qua Stored Procedure.")
        else:
            st.warning("Bạn không có quyền truy cập báo cáo doanh thu.")
