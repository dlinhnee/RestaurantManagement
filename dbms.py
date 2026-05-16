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
        st.header("Staff Login")
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
            # Tìm đến khoảng dòng 71
            if st.form_submit_button("Create Account"):
                if not new_pass or new_pass.strip() == "":
                    st.error("⚠️ Password is required!")
                elif len(new_pass) < 6:
                    st.warning("⚠️ Password must be at least 6 characters long.")
                elif new_name and new_user:
                    hashed = hash_password(new_pass)
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO employees (full_name, username, password, position, hire_date) VALUES (%s,%s,%s,%s,%s)",
                                (new_name, new_user, hashed, new_role, datetime.now().date())
                            )
                            conn.commit()
                            st.success("✅ Account created! Please log in.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
                else:
                    st.warning("Please fill in Full Name and Username.")


# --- 5. MAIN APPLICATION CONTENT ---
else:
    # Sidebar
    st.sidebar.title(f"Role: {st.session_state.user_role.upper()}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ==========================================
    # NAVIGATION MENU
    # ==========================================
    menu = ["Tables & Reservations", "Menu Management", "Billing & Invoices", "Customer Management"]
    
   if st.session_state.user_role == 'admin':
        menu.append("Admin Reports")
        
    choice = st.sidebar.radio("Navigation", menu)
    conn = get_db_connection()

   # ==========================================
    # MODULE 1: CUSTOMER MANAGEMENT
    # ==========================================
    elif choice == "Customer Management":
        st.header("Customer Management")
        t1, t2, t3 = st.tabs(["Customer List", "Add New Customer", "Search & Update Customer"])
        
        # TAB 1: HIỂN THỊ DANH SÁCH (Bổ sung thêm Email và Address)
        with t1:
            df_customers = pd.read_sql("SELECT customer_id, name, phone, email, address, tier, points, join_date FROM customers ORDER BY points DESC", conn)
            st.dataframe(df_customers, use_container_width=True)
            
        # TAB 2: THÊM KHÁCH HÀNG MỚI (Bắt buộc nhập Tên và SĐT)
        with t2:
            st.subheader("Add New Customer")
            with st.form("add_customer_form"):
                c_name = st.text_input("Customer Name (*)")
                c_phone = st.text_input("Phone Number (*)")
                c_email = st.text_input("Email")
                c_address = st.text_input("Address")
                
                if st.form_submit_button("Add Customer"):
                    if c_name and c_phone:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                                (c_name, c_phone, c_email, c_address)
                            )
                            conn.commit()
                            st.success(f"Customer '{c_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Please enter both Customer Name and Phone Number!")
                        
        # TAB 3: TÌM KIẾM BẰNG SĐT VÀ CẬP NHẬT TOÀN DIỆN
        with t3:
            st.subheader("Search & Update Customer Profile")
            search_phone = st.text_input("Enter Customer Phone Number to search:")
            
            if search_phone:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM customers WHERE phone = %s", (search_phone,))
                customer = cursor.fetchone()
                
                if customer:
                    st.success(f"Found Customer: **{customer['name']}**")
                    
                    # Form cập nhật: Tự động điền dữ liệu cũ vào form để nhân viên dễ sửa
                    with st.form("update_customer_form"):
                        st.markdown("**Update Information & Points**")
                        u_name = st.text_input("Full Name (*)", value=customer['name'])
                        u_phone = st.text_input("Phone (*)", value=customer['phone'])
                        u_email = st.text_input("Email", value=customer['email'] if customer['email'] else "")
                        u_address = st.text_input("Address", value=customer['address'] if customer['address'] else "")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            # Sửa trực tiếp số điểm tổng (thay vì nhập số điểm muốn cộng thêm)
                            u_points = st.number_input("Total Reward Points", value=int(customer['points']), step=1)
                        with col2:
                            tiers = ["Standard", "Gold", "Platinum"]
                            current_tier_index = tiers.index(customer['tier']) if customer['tier'] in tiers else 0
                            u_tier = st.selectbox("Membership Tier", tiers, index=current_tier_index)
                            
                        if st.form_submit_button("Update Customer"):
                            if not u_name or not u_phone:
                                st.error("Name and Phone cannot be empty!")
                            else:
                                try:
                                    # Lệnh UPDATE tác động lên toàn bộ trường dữ liệu
                                    cursor.execute("""
                                        UPDATE customers 
                                        SET name=%s, phone=%s, email=%s, address=%s, points=%s, tier=%s 
                                        WHERE customer_id=%s
                                    """, (u_name, u_phone, u_email, u_address, u_points, u_tier, customer['customer_id']))
                                    conn.commit()
                                    st.success("Customer profile updated successfully!")
                                except Exception as e:
                                    st.error(f" Error: {e}")
                else:
                    st.warning("No customer found with this phone number.")

   # ==========================================
    # 2. MODULE: TABLES & RESERVATIONS
    # ==========================================
    elif choice == "Tables & Reservations":
        st.header("🪑Table & Reservation Management")
        t1, t2, t3 = st.tabs(["Table Status", "Create Reservation", "Add New Table (Admin)"])
        
        with t1:
            # Ẩn table_id đi cho đỡ rối, chỉ hiện table_number cho nhân viên xem
            df_tables = pd.read_sql("SELECT table_number, status, capacity FROM tables", conn)
            st.dataframe(df_tables, use_container_width=True)
            
        with t2:
            st.info("Note: Type Phone Number to search for existing customers or create a new one.")
            
            r_phone = st.text_input("Customer Phone (*)")
            r_name = st.text_input("Customer Name (Required if new customer)")
            
            # Chọn bàn theo table_number (thực tế hơn là chọn ID)
            # Lấy danh sách các bàn đang Available
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT table_id, table_number, capacity FROM tables WHERE status = 'Available'")
            avail_tables = cursor.fetchall()
            
            if avail_tables:
                table_options = {f"Table {t['table_number']} (Capacity: {t['capacity']})": t for t in avail_tables}
                selected_table_label = st.selectbox("Select Available Table", list(table_options.keys()))
                selected_table = table_options[selected_table_label]
                
                guests = st.number_input("Number of Guests", min_value=1, step=1)
                
                if st.button("Confirm Booking"):
                    if not r_phone:
                        st.warning("Please enter the customer's phone number!")
                    elif guests > selected_table['capacity']:
                        # Báo lỗi nếu vượt quá sức chứa
                        st.error(f"Cannot book! Table {selected_table['table_number']} only has a capacity of {selected_table['capacity']} guests.")
                    else:
                        try:
                            conn.start_transaction()
                            
                            # 1. Tìm khách hàng theo số điện thoại
                            cursor.execute("SELECT customer_id, name FROM customers WHERE phone = %s", (r_phone,))
                            existing_cust = cursor.fetchone()
                            
                            if existing_cust:
                                final_cust_id = existing_cust['customer_id']
                                st.success(f"Found returning customer: {existing_cust['name']}")
                            else:
                                if not r_name:
                                    st.warning("New phone number detected! Please enter the Customer Name to create a profile.")
                                    st.stop()
                                # 2. Tạo khách hàng mới nếu không tìm thấy
                                cursor.execute("INSERT INTO customers (name, phone) VALUES (%s, %s)", (r_name, r_phone))
                                final_cust_id = cursor.lastrowid
                                st.success(f"New customer profile created for '{r_name}'")
                            
                            # 3. Tạo lịch đặt bàn
                            cursor.execute(
                                "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                                (final_cust_id, datetime.now(), guests)
                            )
                            new_res_id = cursor.lastrowid 
                            
                            # 4. Lưu chi tiết bàn đặt (Kích hoạt Trigger)
                            cursor.execute(
                                "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                                (new_res_id, selected_table['table_id'])
                            )
                            conn.commit()
                            st.success(f"Table {selected_table['table_number']} booked successfully for {guests} guests!")
                        except Exception as err:
                            conn.rollback()
                            st.error(f"Transaction failed: {err}")
            else:
                st.warning("No tables are currently available.")
                    
        with t3:
            if st.session_state.user_role == 'admin':
                with st.form("add_table_form"):
                    new_table_no = st.number_input("New Table Number", min_value=1, step=1)
                    new_capacity = st.number_input("Seating Capacity", min_value=1, step=1)
                    if st.form_submit_button("Add Table"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO tables (table_number, capacity) VALUES (%s, %s)", (new_table_no, new_capacity))
                            conn.commit()
                            st.success(f"Table #{new_table_no} added successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("Only Admin accounts have permission to add new tables.")

   # ==========================================
    # 3. MODULE: MENU MANAGEMENT 
    # ==========================================
    elif choice == "Menu Management":
        st.header("🍴Food & Beverage Menu")
        t1, t2, t3 = st.tabs(["View Menu", "Add New Dish (Admin)", "Edit Dish (Admin)"])
        
        with t1:
            df_menu = pd.read_sql("SELECT dish_id, dish_name, price, is_available FROM menu_items", conn)
            
            df_menu['is_available'] = df_menu['is_available'].map({1: 'Yes (Available)', 0: 'No (Out of Stock)'})
            
            st.dataframe(df_menu, use_container_width=True)
            
        with t2:
            if st.session_state.user_role == 'admin':
                with st.form("add_dish_form"):
                    dish_name = st.text_input("Dish Name")
                    price = st.number_input("Price (VND)", min_value=0, step=1000, format="%d")
                    cat_id = st.number_input("Category ID", min_value=1, step=1)
                    
                    if st.form_submit_button("Add Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                (dish_name, price, cat_id)
                            )
                            conn.commit()
                            st.success("New dish added to the menu successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("Only Admin accounts have permission to add new menu items.")
                
        with t3:
            if st.session_state.user_role == 'admin':
                with st.form("edit_dish_form"):
                    st.subheader("Update Price and Availability")
                    e_dish_id = st.number_input("Dish ID to Update", min_value=1, step=1)
                    e_price = st.number_input("New Price (VND)", min_value=0, step=1000, format="%d")
                    
                    e_avail = st.selectbox("Status", options=[3], format_func=lambda x: "Available" if x == 1 else "Out of Stock")
                    
                    if st.form_submit_button("Update Dish"):
                        cursor = conn.cursor()
                        try:
                            # Python sẽ ngầm lấy giá trị 1 hoặc 0 tương ứng với chữ để lưu lại vào DB
                            cursor.execute(
                                "UPDATE menu_items SET price = %s, is_available = %s WHERE dish_id = %s",
                                (e_price, e_avail, e_dish_id)
                            )
                            conn.commit()
                            st.success(f" Dish #{e_dish_id} updated successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("Only Admin accounts have permission to edit menu items.")
   # ==========================================
    # 4. MODULE: BILLING & INVOICES
    # ==========================================
    elif choice == "Billing & Invoices":
        st.header("🧾 Billing & Invoices")
        t1, t2 = st.tabs(["Invoice List", "Generate New Invoice (Checkout)"])
        
        with t1:
            query = """
                SELECT i.invoice_id AS `Invoice #`, c.name AS `Customer`, 
                       i.total_amount AS `Total (VND)`, i.order_type AS `Type`, i.payment_date AS `Date`
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.customer_id
                ORDER BY i.invoice_id DESC
            """
            df_invoices = pd.read_sql(query, conn)
            st.dataframe(df_invoices, use_container_width=True)
            
        with t2:
            st.subheader("Checkout & Payment")
            cursor = conn.cursor(dictionary=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Customer & Table Info**")
                inv_phone = st.text_input("Customer Phone (*)", key="inv_phone")
                inv_name = st.text_input("Customer Name (If new)", key="inv_name")
                
                cursor.execute("SELECT table_id, table_number FROM tables")
                tables = cursor.fetchall()
                if tables:
                    table_options = {f"Table {t['table_number']}": t['table_id'] for t in tables}
                    table_label = st.selectbox("Select Table", list(table_options.keys()))
                    inv_table_id = table_options[table_label]
                else:
                    st.error("No tables found in Database!")
                
                # --- THÊM TÍNH NĂNG NHẬP ĐIỂM ĐỔI KHUYẾN MÃI ---
                st.markdown("**Loyalty Program**")
                points_to_use = st.number_input("Points to Redeem (1 Point = 1,000 VND)", min_value=0, step=1)

            with col2:
                st.markdown("**Order Details**")
                cursor.execute("SELECT dish_id, dish_name, price FROM menu_items WHERE is_available = 1")
                dishes = cursor.fetchall()
                
                if dishes:
                    dish_options = {f"{d['dish_name']} ({int(d['price']):,} VND)": d for d in dishes}
                    dish_options["None (Skip)"] = None 
                    
                    d1_label = st.selectbox("Select Dish 1 (*)", [k for k in dish_options.keys() if k != "None (Skip)"], key="d1")
                    qty1 = st.number_input("Quantity 1", min_value=1, step=1, key="q1")
                    dish1 = dish_options[d1_label]
                    
                    d2_label = st.selectbox("Select Dish 2 (Optional)", list(dish_options.keys()), index=len(dish_options)-1, key="d2")
                    qty2 = st.number_input("Quantity 2", min_value=1, step=1, key="q2") if d2_label != "None (Skip)" else 0
                    dish2 = dish_options[d2_label] if d2_label != "None (Skip)" else None
                else:
                    st.error("Menu is empty or out of stock!")
            
            if st.button("Generate Invoice & Checkout"):
                if not inv_phone:
                    st.warning("Please enter the customer's phone number!")
                else:
                    try:
                        conn.start_transaction()
                        
                        # 1. KIỂM TRA KHÁCH HÀNG & SỐ ĐIỂM HỢP LỆ
                        cursor.execute("SELECT customer_id, name, points FROM customers WHERE phone = %s", (inv_phone,))
                        existing_cust = cursor.fetchone()
                        
                        if existing_cust:
                            final_cust_id = existing_cust['customer_id']
                            # Kiểm tra xem khách có đủ điểm để trừ không
                            if points_to_use > existing_cust['points']:
                                st.error(f"Not enough points! {existing_cust['name']} only has {existing_cust['points']} points.")
                                conn.rollback()
                                st.stop()
                        else:
                            if points_to_use > 0:
                                st.error("New customers have 0 points to redeem. Please set points to 0.")
                                conn.rollback()
                                st.stop()
                            if not inv_name:
                                st.warning("New phone number detected! Please enter the Customer Name.")
                                st.stop()
                                
                            cursor.execute("INSERT INTO customers (name, phone) VALUES (%s, %s)", (inv_name, inv_phone))
                            final_cust_id = cursor.lastrowid
                            st.success(f"New customer profile created for '{inv_name}'")
                        
                        # 2. TẠO HÓA ĐƠN
                        cursor.execute(
                            "INSERT INTO invoices (customer_id, table_id, payment_date, order_type) VALUES (%s, %s, %s, %s)",
                            (final_cust_id, inv_table_id, datetime.now(), 'Dine-in')
                        )
                        new_invoice_id = cursor.lastrowid
                        
                        # 3. THÊM CHI TIẾT MÓN ĂN VÀO HÓA ĐƠN
                        cursor.execute(
                            "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                            (new_invoice_id, dish1['dish_id'], qty1, dish1['price'], dish1['price'] * qty1)
                        )
                        if dish2:
                            cursor.execute(
                                "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                                (new_invoice_id, dish2['dish_id'], qty2, dish2['price'], dish2['price'] * qty2)
                            )
                        
                        # 4. TÍNH TỔNG TIỀN VÀ TRỪ TIỀN KHUYẾN MÃI
                        cursor.callproc('CalculateInvoiceTotal', [new_invoice_id])
                        
                        discount_amount = points_to_use * 1000
                        if discount_amount > 0:
                            # Update lại tổng tiền hóa đơn sau khi đã gọi Procedure
                            cursor.execute("UPDATE invoices SET total_amount = total_amount - %s WHERE invoice_id = %s", (discount_amount, new_invoice_id))
                        
                        # 5. GIẢI PHÓNG BÀN
                        cursor.execute("UPDATE tables SET status = 'Available' WHERE table_id = %s", (inv_table_id,))
                        
                        # 6. CẬP NHẬT LẠI VÍ ĐIỂM CỦA KHÁCH: Trừ điểm đã dùng, cộng 10 điểm cho hóa đơn mới
                        cursor.execute("UPDATE customers SET points = points - %s + 10 WHERE customer_id = %s", (points_to_use, final_cust_id))
                        
                        conn.commit()
                        
                        # Lấy tổng tiền cuối cùng để hiển thị cho thu ngân
                        cursor.execute("SELECT total_amount FROM invoices WHERE invoice_id = %s", (new_invoice_id,))
                        final_total = int(cursor.fetchone()['total_amount'])
                        
                        st.success(f"Invoice #{new_invoice_id} generated successfully! Table is now free.")
                        st.success(f"Final Total to Pay: {final_total:,} VND")
                        
                        if points_to_use > 0:
                            st.info(f"Customer redeemed {points_to_use} points for a discount of {discount_amount:,} VND.")
                        st.info("Added 10 bonus points for this purchase!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Transaction failed, ROLLBACK executed. Error: {e}")

   # ==========================================
    # 5. MODULE: ADMIN REPORTS
    # ==========================================
    elif choice == "Admin Reports":
        st.header("Admin Dashboard & Reports")
        
        # Kiểm tra quyền truy cập
        if st.session_state.user_role != 'admin':
            st.error("Access Denied. You do not have permission to view this page.")
        else:
            t1, t2 = st.tabs(["Daily Revenue & Visits", "Top Selling Dishes"])
            
            # TAB 1: DOANH THU & LƯỢT KHÁCH (Nhóm theo ngày)
            with t1:
                st.subheader("Revenue & Customer Visits")
                # Dùng hàm DATE() để gom nhóm chuẩn xác theo ngày
                rev_query = """
                    SELECT DATE(payment_date) AS Date, SUM(total_amount) AS Daily_Revenue, COUNT(invoice_id) AS Daily_Visits
                    FROM invoices
                    WHERE payment_date IS NOT NULL
                    GROUP BY DATE(payment_date)
                    ORDER BY Date
                """
                df_rev = pd.read_sql(rev_query, conn)
                
                if not df_rev.empty:
                    # Ép kiểu ngày tháng cho biểu đồ hiển thị đẹp
                    df_rev['Date'] = pd.to_datetime(df_rev['Date']).dt.date
                    
                    # Tính tổng kết để hiển thị lên thẻ Metric
                    total_rev = int(df_rev['Daily_Revenue'].sum())
                    total_visits = int(df_rev['Daily_Visits'].sum())
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Total Revenue", f"{total_rev:,} VND")
                    col2.metric("Total Customer Visits", f"{total_visits} Invoices")
                    
                    st.markdown("---")
                    st.markdown("**Daily Revenue Trend (VND)**")
                    st.line_chart(df_rev.set_index('Date')['Daily_Revenue'])
                    
                    st.markdown("**Daily Customer Visits**")
                    st.bar_chart(df_rev.set_index('Date')['Daily_Visits'])
                else:
                    st.info("No revenue data available yet.")
                    
            # TAB 2: MÓN ĂN BÁN CHẠY NHẤT (Sử dụng Database View)
            with t2:
                st.subheader("Top 5 Best-Selling Dishes")
                st.info("Data is fetched dynamically from the Database View: 'View_TopSellingDishes'")
                
                # Gọi trực tiếp VIEW từ MySQL lên để lấy điểm cộng
                df_top = pd.read_sql("SELECT * FROM View_TopSellingDishes LIMIT 5", conn)
                
                if not df_top.empty:
                    # Đổi tên cột cho đẹp
                    df_top.rename(columns={'dish_name': 'Dish Name', 'total_sold': 'Quantity Sold'}, inplace=True)
                    
                    colA, colB = st.columns([5, 6])
                    with colA:
                        st.dataframe(df_top, use_container_width=True, hide_index=True)
                    with colB:
                        st.bar_chart(df_top.set_index('Dish Name')['Quantity Sold'])
                else:
                    st.info("No sales data available yet.")

    if conn:
        conn.close()

