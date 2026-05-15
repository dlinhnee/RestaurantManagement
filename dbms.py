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
            # Tìm đến khoảng dòng 71
            if st.form_submit_button("Create Account"):
                # --- ĐOẠN SỬA BẮT ĐẦU TẠI ĐÂY ---
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
    
    # Admin gets an extra report menu
    if st.session_state.user_role == 'admin':
        menu.append("Admin Reports")
        
    choice = st.sidebar.radio("Navigation", menu)
    conn = get_db_connection()

    # ==========================================
    # 1. MODULE: CUSTOMER MANAGEMENT
    # ==========================================
    if choice == "Customer Management":
        st.header("👥 Customer Management")
        t1, t2 = st.tabs(["Customer List", "Add New Customer"])
        
        with t1:
            df_customers = pd.read_sql("SELECT customer_id, name, phone, tier, points FROM customers", conn)
            st.dataframe(df_customers, use_container_width=True)
            
        with t2:
            with st.form("add_customer_form"):
                c_name = st.text_input("Customer Name (*)")
                c_phone = st.text_input("Phone Number")
                c_email = st.text_input("Email")
                c_address = st.text_input("Address")
                
                if st.form_submit_button("Add Customer"):
                    if c_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                                (c_name, c_phone, c_email, c_address)
                            )
                            conn.commit()
                            st.success(f"✅ Customer '{c_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Please enter the customer name!")

    # ==========================================
    # 2. MODULE: TABLES & RESERVATIONS
    # ==========================================
    elif choice == "Tables & Reservations":
        st.header("🪑 Table & Reservation Management")
        t1, t2 = st.tabs(["Table Status", "Create Reservation (Transaction)"])
        
        with t1:
            df_tables = pd.read_sql("SELECT table_id, table_number, status, capacity FROM tables", conn)
            st.dataframe(df_tables, use_container_width=True)
            
        with t2:
            st.info("💡 Note: Upon successful booking, the Database Trigger will automatically change the table status to 'Reserved'.")
            cust_id = st.number_input("Customer ID", min_value=1, step=1)
            table_id = st.number_input("Table ID", min_value=1, step=1)
            guests = st.slider("Number of Guests", 1, 20)
            
            if st.button("Confirm Booking"):
                cursor = conn.cursor()
                try:
                    conn.start_transaction()
                    # Step 1: Insert into reservations
                    cursor.execute(
                        "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                        (cust_id, datetime.now(), guests)
                    )
                    new_res_id = cursor.lastrowid 
                    
                    # Step 2: Insert into reservation_detail (M:N relationship)
                    cursor.execute(
                        "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                        (new_res_id, table_id)
                    )
                    conn.commit()
                    st.success(f"✅ Table {table_id} booked successfully! Trigger automatically locked the table.")
                except mysql.connector.Error as err:
                    conn.rollback()
                    st.error(f"❌ Transaction failed, ROLLBACK executed: {err}")

    # ==========================================
    # 3. MODULE: MENU MANAGEMENT 
    # ==========================================
    elif choice == "Menu Management":
        st.header("🍴 Food & Beverage Menu")
        t1, t2 = st.tabs(["View Menu", "Add New Dish (Admin Only)"])
        
        with t1:
            df_menu = pd.read_sql("SELECT dish_id, dish_name, price, is_available FROM menu_items", conn)
            st.dataframe(df_menu, use_container_width=True)
            
        with t2:
            if st.session_state.user_role == 'admin':
                with st.form("add_dish_form"):
                    dish_name = st.text_input("Dish Name")
                    price = st.number_input("Price", min_value=0.0, format="%.2f")
                    cat_id = st.number_input("Category ID", min_value=1, step=1)
                    
                    if st.form_submit_button("Add Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                (dish_name, price, cat_id)
                            )
                            conn.commit()
                            st.success("✅ New dish added to the menu successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Only Admin accounts have permission to add new menu items.")

    # ==========================================
    # 4. MODULE: BILLING & INVOICES
    # ==========================================
    elif choice == "Billing & Invoices":
        st.header("🧾 Billing & Invoices")
        t1, t2 = st.tabs(["Invoice List", "Generate New Invoice (Transaction)"])
        
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
            st.subheader("Checkout (Using Transaction & Procedure)")
            col1, col2 = st.columns(2)
            with col1:
                inv_cust_id = st.number_input("Customer ID", min_value=1, step=1, key="inv_c")
                inv_table_id = st.number_input("Table ID", min_value=1, step=1, key="inv_t")
            with col2:
                dish_1 = st.number_input("Dish 1 (Dish ID)", min_value=1, step=1)
                dish_2 = st.number_input("Dish 2 (Dish ID) - Optional", min_value=0, step=1)
            
            if st.button("Generate Invoice & Calculate Total"):
                cursor = conn.cursor(dictionary=True)
                try:
                    conn.start_transaction()
                    
                    # Step 1: Create Invoice
                    cursor.execute(
                        "INSERT INTO invoices (customer_id, table_id, payment_date, order_type) VALUES (%s, %s, %s, %s)",
                        (inv_cust_id, inv_table_id, datetime.now(), 'Dine-in')
                    )
                    new_invoice_id = cursor.lastrowid
                    
                    # Step 2: Add invoice details
                    cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_1,))
                    price_1 = cursor.fetchone()['price']
                    cursor.execute(
                        "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                        (new_invoice_id, dish_1, 1, price_1, price_1)
                    )
                    
                    if dish_2 > 0:
                        cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_2,))
                        price_2 = cursor.fetchone()['price']
                        cursor.execute(
                            "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                            (new_invoice_id, dish_2, 1, price_2, price_2)
                        )
                    
                    # Step 3: Calculate total amount using Stored Procedure
                    cursor.callproc('CalculateInvoiceTotal', [new_invoice_id])
                    
                    # Step 4: Free the table
                    cursor.execute("UPDATE tables SET status = 'Available' WHERE table_id = %s", (inv_table_id,))
                    
                    conn.commit()
                    st.success(f"✅ Invoice #{new_invoice_id} generated successfully! Stored Procedure calculated the total amount.")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Transaction failed, ROLLBACK executed. Error: {e}")

    # ==========================================
    # 5. MODULE: ADMIN REPORTS
    # ==========================================
    elif choice == "Admin Reports":
        st.header("📊 Admin Dashboard")
        st.subheader("🏆 Top Selling Dishes (Fetched from SQL VIEW)")
        try:
            df_top_dishes = pd.read_sql("SELECT * FROM View_TopSellingDishes LIMIT 10", conn)
            st.bar_chart(df_top_dishes.set_index('dish_name'))
            st.dataframe(df_top_dishes, use_container_width=True)
        except Exception as e:
            st.error(f"Report loading error: {e}")

    if conn:
        conn.close()
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
    # 1. MODULE: CUSTOMER MANAGEMENT
    # ==========================================
    if choice == "Customer Management":
        st.header("👥 Customer Management")
        t1, t2, t3 = st.tabs(["Customer List", "Add New Customer", "Update Customer Points"])
        
        with t1:
            df_customers = pd.read_sql("SELECT customer_id, name, phone, tier, points FROM customers", conn)
            st.dataframe(df_customers, use_container_width=True)
            
        with t2:
            with st.form("add_customer_form"):
                c_name = st.text_input("Customer Name (*)")
                c_phone = st.text_input("Phone Number")
                c_email = st.text_input("Email")
                c_address = st.text_input("Address")
                
                if st.form_submit_button("Add Customer"):
                    if c_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                                (c_name, c_phone, c_email, c_address)
                            )
                            conn.commit()
                            st.success(f"✅ Customer '{c_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Please enter the customer name!")
                        
        with t3:
            st.subheader("Reward Loyalty Points")
            with st.form("update_customer_form"):
                u_cust_id = st.number_input("Customer ID", min_value=1, step=1)
                u_points = st.number_input("Points to Add", min_value=1, step=1)
                
                if st.form_submit_button("Update Points"):
                    cursor = conn.cursor()
                    try:
                        cursor.execute("UPDATE customers SET points = points + %s WHERE customer_id = %s", (u_points, u_cust_id))
                        conn.commit()
                        st.success(f"✅ Points successfully added to Customer #{u_cust_id}!")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ==========================================
    # 2. MODULE: TABLES & RESERVATIONS
    # ==========================================
    elif choice == "Tables & Reservations":
        st.header("🪑 Table & Reservation Management")
        t1, t2, t3 = st.tabs(["Table Status", "Create Reservation", "Add New Table (Admin)"])
        
        with t1:
            df_tables = pd.read_sql("SELECT table_id, table_number, status, capacity FROM tables", conn)
            st.dataframe(df_tables, use_container_width=True)
            
        with t2:
            st.info("💡 Note: Upon successful booking, the Database Trigger will automatically change the table status to 'Reserved'.")
            cust_id = st.number_input("Customer ID", min_value=1, step=1)
            table_id = st.number_input("Table ID", min_value=1, step=1)
            guests = st.slider("Number of Guests", 1, 20)
            
            if st.button("Confirm Booking"):
                cursor = conn.cursor()
                try:
                    conn.start_transaction()
                    cursor.execute(
                        "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                        (cust_id, datetime.now(), guests)
                    )
                    new_res_id = cursor.lastrowid 
                    
                    cursor.execute(
                        "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                        (new_res_id, table_id)
                    )
                    conn.commit()
                    st.success(f"✅ Table {table_id} booked successfully! Trigger automatically locked the table.")
                except mysql.connector.Error as err:
                    conn.rollback()
                    st.error(f"❌ Transaction failed, ROLLBACK executed: {err}")
                    
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
                            st.success(f"✅ Table #{new_table_no} added successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Only Admin accounts have permission to add new tables.")

    # ==========================================
    # 3. MODULE: MENU MANAGEMENT 
    # ==========================================
    elif choice == "Menu Management":
        st.header("🍴 Food & Beverage Menu")
        t1, t2, t3 = st.tabs(["View Menu", "Add New Dish (Admin)", "Edit Dish (Admin)"])
        
        with t1:
            df_menu = pd.read_sql("SELECT dish_id, dish_name, price, is_available FROM menu_items", conn)
            st.dataframe(df_menu, use_container_width=True)
            
        with t2:
            if st.session_state.user_role == 'admin':
                with st.form("add_dish_form"):
                    dish_name = st.text_input("Dish Name")
                    price = st.number_input("Price", min_value=0.0, format="%.2f")
                    cat_id = st.number_input("Category ID", min_value=1, step=1)
                    
                    if st.form_submit_button("Add Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                (dish_name, price, cat_id)
                            )
                            conn.commit()
                            st.success("✅ New dish added to the menu successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Only Admin accounts have permission to add new menu items.")
                
        with t3:
            if st.session_state.user_role == 'admin':
                with st.form("edit_dish_form"):
                    st.subheader("Update Price and Availability")
                    e_dish_id = st.number_input("Dish ID to Update", min_value=1, step=1)
                    e_price = st.number_input("New Price", min_value=0.0, format="%.2f")
                    e_avail = st.selectbox("Status", [2], format_func=lambda x: "Available (1)" if x == 1 else "Out of Stock (0)")
                    
                    if st.form_submit_button("Update Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "UPDATE menu_items SET price = %s, is_available = %s WHERE dish_id = %s",
                                (e_price, e_avail, e_dish_id)
                            )
                            conn.commit()
                            st.success(f"✅ Dish #{e_dish_id} updated successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Only Admin accounts have permission to edit menu items.")

    # ==========================================
    # 4. MODULE: BILLING & INVOICES
    # ==========================================
    elif choice == "Billing & Invoices":
        st.header("🧾 Billing & Invoices")
        t1, t2 = st.tabs(["Invoice List", "Generate New Invoice (Transaction)"])
        
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
            st.subheader("Checkout (Using Transaction & Procedure)")
            col1, col2 = st.columns(2)
            with col1:
                inv_cust_id = st.number_input("Customer ID", min_value=1, step=1, key="inv_c")
                inv_table_id = st.number_input("Table ID", min_value=1, step=1, key="inv_t")
            with col2:
                dish_1 = st.number_input("Dish 1 (Dish ID)", min_value=1, step=1)
                dish_2 = st.number_input("Dish 2 (Dish ID) - Optional", min_value=0, step=1)
            
            if st.button("Generate Invoice & Calculate Total"):
                cursor = conn.cursor(dictionary=True)
                try:
                    conn.start_transaction()
                    
                    cursor.execute(
                        "INSERT INTO invoices (customer_id, table_id, payment_date, order_type) VALUES (%s, %s, %s, %s)",
                        (inv_cust_id, inv_table_id, datetime.now(), 'Dine-in')
                    )
                    new_invoice_id = cursor.lastrowid
                    
                    cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_1,))
                    price_1 = cursor.fetchone()['price']
                    cursor.execute(
                        "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                        (new_invoice_id, dish_1, 1, price_1, price_1)
                    )
                    
                    if dish_2 > 0:
                        cursor.execute("SELECT price FROM menu_items WHERE dish_id = %s", (dish_2,))
                        price_2 = cursor.fetchone()['price']
                        cursor.execute(
                            "INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES (%s, %s, %s, %s, %s)",
                            (new_invoice_id, dish_2, 1, price_2, price_2)
                        )
                    
                    cursor.callproc('CalculateInvoiceTotal', [new_invoice_id])
                    cursor.execute("UPDATE tables SET status = 'Available' WHERE table_id = %s", (inv_table_id,))
                    
                    conn.commit()
                    st.success(f"✅ Invoice #{new_invoice_id} generated successfully! Procedure calculated the total amount.")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Transaction failed, ROLLBACK executed. Error: {e}")

    # ==========================================
    # 5. MODULE: ADMIN REPORTS
    # ==========================================
    elif choice == "Admin Reports":
        st.header("📊 Admin Dashboard")
        
        st.subheader("💰 Daily Revenue & Customer Visits")
        try:
            # Truy vấn Gom nhóm Doanh thu và Lượt khách theo Ngày
            rev_query = """
                SELECT DATE(payment_date) AS Date, SUM(total_amount) AS Daily_Revenue, COUNT(invoice_id) AS Daily_Visits
                FROM invoices
                WHERE payment_date IS NOT NULL
                GROUP BY DATE(payment_date)
                ORDER BY Date
            """
            df_rev = pd.read_sql(rev_query, conn)
            
            if not df_rev.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Revenue Trend ($)**")
                    st.line_chart(df_rev.set_index('Date')['Daily_Revenue'])
                with col2:
                    st.write("**Customer Visits**")
                    st.bar_chart(df_rev.set_index('Date')['Daily_Visits'])
            else:
                st.info("No revenue data available yet. Please generate some invoices first.")
        except Exception as e:
            st.error(f"Revenue report loading error: {e}")

        st.markdown("---")
        st.subheader("🏆 Top Selling Dishes (Fetched from SQL VIEW)")
        try:
            df_top_dishes = pd.read_sql("SELECT * FROM View_TopSellingDishes LIMIT 10", conn)
            st.bar_chart(df_top_dishes.set_index('dish_name'))
            st.dataframe(df_top_dishes, use_container_width=True)
        except Exception as e:
            st.error(f"Top dishes report loading error: {e}")

    if conn:
        conn.close()

