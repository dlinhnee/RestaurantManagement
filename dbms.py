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
    "database": "defaultdb",
    "ssl_disabled": False
}

def get_db_connection():
    try:
        return mysql.connector.connect(
            **DB_CONFIG,
            ssl_mode='REQUIRED' # Bắt buộc phải có dòng này cho Aiven
        )
    except Exception as e:
        st.error(f"Connection Error: {e}")
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

    menu = ["Tables & Reservations", "Menu Management", "Billing & Invoices"]
    if st.session_state.user_role == 'admin':
        menu.append("Admin Reports")
    
    choice = st.sidebar.radio("Navigation", menu)
    conn = get_db_connection()

    # --- MODULE: TABLES & RESERVATIONS [cite: 74, 76] ---
    if choice == "Tables & Reservations":
        st.header("🪑 Table & Reservation Management")
        t1, t2 = st.tabs(["Table Status", "Book a Table"])
        
        with t1:
            df_tables = pd.read_sql("SELECT table_number, status, capacity FROM tables", conn)
            st.dataframe(df_tables, use_container_width=True)

        with t2:
            st.subheader("New Reservation")
            # Based on your SQL: (customer_id, reservation_time, guest_count)
            cust_id = st.number_input("Customer ID", min_value=1)
            table_id = st.number_input("Table ID", min_value=1)
            guests = st.slider("Guest Count", 1, 20)
            if st.button("Confirm Booking"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                               (cust_id, datetime.now(), guests))
                conn.commit()
                st.success(f"Table {table_id} booked successfully!")

    # --- MODULE: MENU MANAGEMENT [cite: 75] ---
    elif choice == "Menu Management":
        st.header("🍴 Food & Beverage Menu")
        df_menu = pd.read_sql("SELECT dish_name, price, is_available FROM menu_items", conn)
        st.table(df_menu)

    # --- MODULE: BILLING & INVOICES [cite: 77, 89] ---
    elif choice == "Billing & Invoices":
        st.header("🧾 Invoice & Delivery Tracking")
        # Joining for detailed view
        query = """
            SELECT i.invoice_id, c.name, i.total_amount, i.order_type, i.delivery_status 
            FROM invoices i 
            JOIN customers c ON i.customer_id = c.customer_id
        """
        df_invoices = pd.read_sql(query, conn)
        st.dataframe(df_invoices, use_container_width=True)

    if conn: conn.close()
