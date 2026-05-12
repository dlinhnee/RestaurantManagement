import streamlit as st
import mysql.connector
import pandas as pd
import bcrypt
from datetime import datetime

# --- 1. DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "mysql-3c1b790c-vudieulinh305-ebb6.k.aivencloud.com",
    "port": 25428,
    "user": "avnadmin",
    "password": "AVNS_AIQlh70s2tSBuu4XrKE", 
    "database": "RestaurantManagement",
    "ssl_disabled": False
}
def get_db_connection():
    try:
        # Sử dụng dictionary 'ssl' để truyền tham số bảo mật thay vì ssl_mode trực tiếp
        return mysql.connector.connect(
            **DB_CONFIG,
            ssl_disabled=False
        )
    except Exception as e:
        # Nếu vẫn lỗi, thử cách kết nối cơ bản nhất (Aiven đôi khi tự nhận diện SSL)
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Exception as e2:
            st.error(f"Final Connection Error: {e2}")
            return None
# --- 2. SECURITY & AUTHENTICATION  ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- 3. PAGE UI SETUP ---
st.set_page_config(page_title="Restaurant Management", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- 4. LOGIN & REGISTRATION TABS ---
if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        st.header("🔑 Staff Login")
        user_in = st.text_input("Username", key="login_user")
        pass_in = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                # ANTI SQL INJECTION 
                cursor.execute("SELECT password, position FROM employees WHERE username = %s", (user_in,))
                user = cursor.fetchone()
                conn.close()
                if user and check_password(pass_in, user['password']):
                    st.session_state.logged_in = True
                    st.session_state.user_role = user['position']
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab_register:
        st.header("📝 Staff Registration")
        with st.form("reg_form"):
            new_name = st.text_input("Full Name")
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "cashier", "waiter"])
            if st.form_submit_button("Create Account"):
                hashed = hash_password(new_pass)
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO employees (full_name, username, password, position, hire_date) VALUES (%s,%s,%s,%s,%s)",
                                       (new_name, new_user, hashed, new_role, datetime.now().date()))
                        conn.commit()
                        st.success("Account created! Please log in.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()

# --- 5. MAIN APPLICATION CONTENT ---
else:
    st.sidebar.title(f"Role: {st.session_state.user_role.upper()}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # CẬP NHẬT THANH MENU ĐIỀU HƯỚNG
        # ==========================================
        # Thêm "Customer Management" vào danh sách menu chung
        menu = ["Tables & Reservations", "Menu Management", "Billing & Invoices", "Customer Management"]
        
        # Admin có thêm menu xem Báo cáo
        if st.session_state.user_role == 'admin':
            menu.append("Admin Reports")
            
        choice = st.sidebar.radio("Navigation", menu)
        conn = get_db_connection()

        # ==========================================
        # 1. MODULE: CUSTOMER MANAGEMENT (MỚI)
        # ==========================================
        if choice == "Customer Management":
            st.header("👥 Quản lý Khách hàng")
            t1, t2 = st.tabs(["Danh sách Khách hàng", "Thêm Khách hàng mới"])
            
            with t1:
                df_customers = pd.read_sql("SELECT customer_id, name, phone, tier, points FROM customers", conn)
                st.dataframe(df_customers, use_container_width=True)
                
            with t2:
                with st.form("add_customer_form"):
                    c_name = st.text_input("Tên khách hàng (*)")
                    c_phone = st.text_input("Số điện thoại")
                    c_email = st.text_input("Email")
                    c_address = st.text_input("Địa chỉ")
                    
                    if st.form_submit_button("Thêm Khách Hàng"):
                        if c_name:
                            cursor = conn.cursor()
                            try:
                                cursor.execute(
                                    "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                                    (c_name, c_phone, c_email, c_address)
                                )
                                conn.commit()
                                st.success(f"✅ Đã thêm khách hàng {c_name} thành công!")
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                        else:
                            st.warning("Vui lòng nhập tên khách hàng!")

        # ==========================================
        # 2. MODULE: TABLES & RESERVATIONS (ĐÃ SỬA TRANSACTION)
        # ==========================================
        elif choice == "Tables & Reservations":
            st.header("🪑 Quản lý Đặt bàn")
            t1, t2 = st.tabs(["Trạng thái Bàn", "Tạo Đặt bàn (Transaction)"])
            
            with t1:
                df_tables = pd.read_sql("SELECT table_id, table_number, status, capacity FROM tables", conn)
                st.dataframe(df_tables, use_container_width=True)
                
            with t2:
                st.info("💡 Lưu ý: Khi đặt bàn thành công, Trigger trong DB sẽ tự động chuyển trạng thái bàn thành 'Reserved'.")
                cust_id = st.number_input("Mã Khách hàng (Customer ID)", min_value=1, step=1)
                table_id = st.number_input("Mã Bàn (Table ID)", min_value=1, step=1)
                guests = st.slider("Số lượng khách", 1, 20)
                
                if st.button("Xác nhận Đặt bàn"):
                    cursor = conn.cursor()
                    try:
                        conn.start_transaction()
                        # Bước 1: Lưu thông tin vào bảng reservations
                        cursor.execute(
                            "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                            (cust_id, datetime.now(), guests)
                        )
                        new_res_id = cursor.lastrowid # Lấy ID vừa tạo
                        
                        # Bước 2: Lưu vào bảng trung gian reservation_detail (Quan hệ M:N)
                        cursor.execute(
                            "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                            (new_res_id, table_id)
                        )
                        conn.commit()
                        st.success(f"✅ Đã đặt bàn {table_id} thành công! Trigger đã tự động khóa bàn.")
                    except mysql.connector.Error as err:
                        conn.rollback()
                        st.error(f"❌ Có lỗi xảy ra, đã ROLLBACK: {err}")

        # ==========================================
        # 3. MODULE: MENU MANAGEMENT (BỔ SUNG THÊM MÓN)
        # ==========================================
        elif choice == "Menu Management":
            st.header("🍴 Thực đơn Nhà hàng")
            t1, t2 = st.tabs(["Xem Thực đơn", "Thêm Món (Chỉ Admin)"])
            
            with t1:
                df_menu = pd.read_sql("SELECT dish_id, dish_name, price, is_available FROM menu_items", conn)
                st.dataframe(df_menu, use_container_width=True)
                
            with t2:
                if st.session_state.user_role == 'admin':
                    with st.form("add_dish_form"):
                        dish_name = st.text_input("Tên món ăn")
                        price = st.number_input("Giá bán", min_value=0.0, format="%.2f")
                        cat_id = st.number_input("Mã Danh mục (Category ID)", min_value=1, step=1)
                        
                        if st.form_submit_button("Thêm Món"):
                            cursor = conn.cursor()
                            try:
                                cursor.execute(
                                    "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                    (dish_name, price, cat_id)
                                )
                                conn.commit()
                                st.success("✅ Đã thêm món mới vào thực đơn!")
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                else:
                    st.warning("⚠️ Chỉ tài khoản Admin mới có quyền thêm món ăn mới.")

        # ==========================================
        # 4. MODULE: BILLING & INVOICES (TRANSACTION LẬP HÓA ĐƠN & PROCEDURE)
        # ==========================================
        elif choice == "Billing & Invoices":
            st.header("🧾 Hóa đơn & Thanh toán")
            t1, t2 = st.tabs(["Danh sách Hóa đơn", "Lập Hóa đơn Mới (Transaction)"])
            
            with t1:
                query = """
                    SELECT i.invoice_id, c.name AS customer_name, i.total_amount, i.order_type, i.payment_date
                    FROM invoices i
                    LEFT JOIN customers c ON i.customer_id = c.customer_id
                    ORDER BY i.invoice_id DESC
                """
                df_invoices = pd.read_sql(query, conn)
                st.dataframe(df_invoices, use_container_width=True)
                
            with t2:
                st.subheader("Thanh toán (Sử dụng Transaction & Procedure)")
                # Form tạo hóa đơn đơn giản cho báo cáo
                col1, col2 = st.columns(2)
                with col1:
                    inv_cust_id = st.number_input("Khách hàng ID", min_value=1, step=1, key="inv_c")
                    inv_table_id = st.number_input("Bàn ID", min_value=1, step=1, key="inv_t")
                with col2:
                    dish_1 = st.number_input("Món ăn 1 (Dish ID)", min_value=1, step=1)
                    dish_2 = st.number_input("Món ăn 2 (Dish ID) - Tùy chọn", min_value=0, step=1)
                
                if st.button("Tạo Hóa Đơn & Tính Tiền"):
                    cursor = conn.cursor(dictionary=True)
                    try:
                        conn.start_transaction()
                        
                        # Bước 1: Tạo hóa đơn mới
                        cursor.execute(
                            "INSERT INTO invoices (customer_id, table_id, payment_date, order_type) VALUES (%s, %s, %s, %s)",
                            (inv_cust_id, inv_table_id, datetime.now(), 'Dine-in')
                        )
                        new_invoice_id = cursor.lastrowid
                        
                        # Bước 2: Lấy giá tiền món 1 và Insert vào chi tiết hóa đơn
                        cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_1,))
                        price_1 = cursor.fetchone()['price']
                        cursor.execute(
                            "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                            (new_invoice_id, dish_1, 1, price_1, price_1)
                        )
                        
                        # Bước 3: Nếu có nhập món 2 thì Insert tiếp (Gộp executemany)
                        if dish_2 > 0:
                            cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_2,))
                            price_2 = cursor.fetchone()['price']
                            cursor.execute(
                                "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                                (new_invoice_id, dish_2, 1, price_2, price_2)
                            )
                        
                        # Bước 4: Chạy Stored Procedure để CSDL tự tính tổng tiền cho hóa đơn vừa tạo
                        cursor.callproc('CalculateInvoiceTotal', [new_invoice_id])
                        
                        # Bước 5: Giải phóng bàn ăn
                        cursor.execute("UPDATE tables SET status = 'Available' WHERE table_id = %s", (inv_table_id,))
                        
                        # Bước 6: Lưu giao dịch
                        conn.commit()
                        st.success(f"✅ Đã tạo Hóa đơn #{new_invoice_id} thành công! Stored Procedure đã tự động tính tổng tiền.")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Giao dịch thất bại, đã Rollback. Lỗi: {e}")

        # ==========================================
        # 5. MODULE: ADMIN REPORTS (SỬ DỤNG VIEW & CHART)
        # ==========================================
        elif choice == "Admin Reports":
            st.header("📊 Báo cáo Quản trị (Admin Dashboard)")
            
            st.subheader("🏆 Các món ăn bán chạy nhất (Lấy từ SQL VIEW)")
            try:
                # Gọi VIEW đã thiết kế trong MySQL
                df_top_dishes = pd.read_sql("SELECT * FROM View_TopSellingDishes LIMIT 10", conn)
                
                # Vẽ biểu đồ cột bằng Streamlit
                st.bar_chart(df_top_dishes.set_index('dish_name'))
                
                # In bảng số liệu
                st.dataframe(df_top_dishes, use_container_width=True)
            except Exception as e:
                st.error(f"Chưa thể tải báo cáo. Vui lòng đảm bảo bạn đã chạy code tạo VIEW trong MySQL. Lỗi: {e}")

        if conn:
            conn.close()
