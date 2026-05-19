import streamlit as st
import hashlib
import mysql.connector
import pandas as pd
from datetime import datetime

# --- 1. DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "mysql-3c1b790c-vudieulinh305-ebb6.k.aivencloud.com",
    "port": 25428,
    "user": "avnadmin",
    "password": "AVNS_AIQlh70s2tSBuu4XrKE",
    "database": "RestaurantManagement" 
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG, ssl_disabled=False)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- 2. SECURITY & AUTHENTICATION ---
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password(password, hashed):
    return hash_password(password) == hashed



# --- THÊM ĐOẠN NÀY VÀO ĐÂY (KHOẢNG DÒNG 27) ---
def change_password_db(username, old_password, new_password):
    """Hàm kiểm tra mật khẩu cũ và cập nhật mật khẩu mới"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # 1. Kiểm tra mật khẩu cũ
            cursor.execute("SELECT password FROM employees WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password(old_password, user["password"]):
                # 2. Mã hóa mật khẩu mới và update
                new_password_hash = hash_password(new_password)
                cursor.execute(
                    "UPDATE employees SET password = %s WHERE username = %s",
                    (new_password_hash, username)
                )
                conn.commit()
                return True, "Password updated successfully!"
            else:
                return False, "Incorrect old password."
        except Exception as e:
            return False, f"Database error: {e}"
        finally:
            cursor.close()
            conn.close()
    return False, "Database connection failed."


# --- 3. PAGE UI SETUP ---
st.set_page_config(page_title="Restaurant Management", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
# --- 4. LOGIN TABS ---
if not st.session_state.logged_in:
    tab_login = st.tabs(["Login"])
    
    st.header("Staff Login")
    user_in = st.text_input("Username", key="login_user")
    pass_in = st.text_input("Password", type="password", key="login_pass")
    if st.button("Sign In"):
        conn = get_db_connection()

        if conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT password, position FROM employees WHERE username = %s",
                (user_in,),
            )
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password(pass_in, user["password"]):
                st.session_state.logged_in = True
                st.session_state.user_role = user["position"]
                st.rerun()
            else:
                st.error("Invalid credentials.")
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
    menu = [
        "Change Password",
        "Tables & Reservations",
        "Menu Management",
        "Billing & Invoices",
        "Customer Management",
    ]

    if st.session_state.user_role == "admin":
        menu.append("Admin Reports")

    choice = st.sidebar.radio("Navigation", menu)
    conn = get_db_connection()

    # ==========================================
    # MODULE 1: CUSTOMER MANAGEMENT
    # ==========================================
    if choice == "Customer Management":
        st.header("Customer Management")
        t1, t2, t3 = st.tabs(
            ["Customer List", "Add New Customer", "Search & Update Customer"]
        )

        # TAB 1: HIỂN THỊ DANH SÁCH
        with t1:
            df_customers = pd.read_sql(
                "SELECT customer_id, name, phone, email, address, tier, points, join_date FROM customers ORDER BY points DESC",
                conn,
            )
            st.dataframe(df_customers, use_container_width=True)

        # TAB 2: THÊM KHÁCH HÀNG MỚI
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
                                (c_name, c_phone, c_email, c_address),
                            )
                            conn.commit()
                            st.success(
                                f"Customer '{c_name}' added successfully!"
                            )
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning(
                            "Please enter both Customer Name and Phone Number!"
                        )

        # TAB 3: TÌM KIẾM BẰNG SĐT VÀ CẬP NHẬT TOÀN DIỆN
        with t3:
            st.subheader("Search & Update Customer Profile")
            search_phone = st.text_input(
                "Enter Customer Phone Number to search:"
            )

            if search_phone:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM customers WHERE phone = %s", (search_phone,)
                )
                customer = cursor.fetchone()

                if customer:
                    st.success(f"Found Customer: **{customer['name']}**")

                    # Form cập nhật dữ liệu cũ
                    with st.form("update_customer_form"):
                        st.markdown("**Update Information & Points**")
                        u_name = st.text_input(
                            "Full Name (*)", value=customer["name"]
                        )
                        u_phone = st.text_input(
                            "Phone (*)", value=customer["phone"]
                        )
                        u_email = st.text_input(
                            "Email",
                            value=customer["email"]
                            if customer["email"]
                            else "",
                        )
                        u_address = st.text_input(
                            "Address",
                            value=customer["address"]
                            if customer["address"]
                            else "",
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            u_points = st.number_input(
                                "Total Reward Points",
                                value=int(customer["points"]),
                                step=1,
                            )
                        with col2:
                            tiers = ["Standard", "Gold", "Platinum"]
                            current_tier_index = (
                                tiers.index(customer["tier"])
                                if customer["tier"] in tiers
                                else 0
                            )
                            u_tier = st.selectbox(
                                "Membership Tier",
                                tiers,
                                index=current_tier_index,
                            )

                        if st.form_submit_button("Update Customer"):
                            if not u_name or not u_phone:
                                st.error("Name and Phone cannot be empty!")
                            else:
                                try:
                                    cursor.execute(
                                        """
                                        UPDATE customers 
                                        SET name=%s, phone=%s, email=%s, address=%s, points=%s, tier=%s 
                                        WHERE customer_id=%s
                                    """,
                                        (
                                            u_name,
                                            u_phone,
                                            u_email,
                                            u_address,
                                            u_points,
                                            u_tier,
                                            customer["customer_id"],
                                        ),
                                    )
                                    conn.commit()
                                    st.success(
                                        "Customer profile updated successfully!"
                                    )
                                except Exception as e:
                                    st.error(f" Error: {e}")
                else:
                    st.warning("No customer found with this phone number.")

    # ==========================================
    # 2. MODULE: TABLES & RESERVATIONS
    # ==========================================
    elif choice == "Tables & Reservations":
        st.header("Table & Reservation Management")
        t1, t2, t3 = st.tabs(
            ["Table Status", "Create Reservation", "Add New Table (Admin)"]
        )

        with t1:
            df_tables = pd.read_sql(
                "SELECT table_number, status, capacity FROM tables", conn
            )
            st.dataframe(df_tables, use_container_width=True)

        with t2:
            st.info(
                "Note: Type Phone Number to search for existing customers or create a new one."
            )

            r_phone = st.text_input("Customer Phone (*)")
            r_name = st.text_input("Customer Name (Required if new customer)")

            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT table_id, table_number, capacity FROM tables WHERE status = 'Available'"
            )
            avail_tables = cursor.fetchall()

            if avail_tables:
                table_options = {
                    f"Table {t['table_number']} (Capacity: {t['capacity']})": t
                    for t in avail_tables
                }
                selected_table_label = st.selectbox(
                    "Select Available Table", list(table_options.keys())
                )
                selected_table = table_options[selected_table_label]

                guests = st.number_input("Number of Guests", min_value=1, step=1)

                if st.button("Confirm Booking"):
                    if not r_phone:
                        st.warning("Please enter the customer's phone number!")
                    elif guests > selected_table["capacity"]:
                        st.error(
                            f"Cannot book! Table {selected_table['table_number']} only has a capacity of {selected_table['capacity']} guests."
                        )
                    else:
                        try:
                            conn.start_transaction()

                            # 1. Tìm khách hàng theo SĐT
                            cursor.execute(
                                "SELECT customer_id, name FROM customers WHERE phone = %s",
                                (r_phone,),
                            )
                            existing_cust = cursor.fetchone()

                            if existing_cust:
                                final_cust_id = existing_cust["customer_id"]
                                st.success(
                                    f"Found returning customer: {existing_cust['name']}"
                                )
                            else:
                                if not r_name:
                                    st.warning(
                                        "New phone number detected! Please enter the Customer Name to create a profile."
                                    )
                                    st.stop()
                                # 2. Tạo khách hàng mới
                                cursor.execute(
                                    "INSERT INTO customers (name, phone) VALUES (%s, %s)",
                                    (r_name, r_phone),
                                )
                                final_cust_id = cursor.lastrowid
                                st.success(
                                    f"New customer profile created for '{r_name}'"
                                )

                            # 3. Tạo lịch đặt bàn
                            cursor.execute(
                                "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                                (final_cust_id, datetime.now(), guests),
                            )
                            new_res_id = cursor.lastrowid

                            # 4. Lưu chi tiết bàn đặt
                            cursor.execute(
                                "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                                (new_res_id, selected_table["table_id"]),
                            )
                            conn.commit()
                            st.success(
                                f"Table {selected_table['table_number']} booked successfully for {guests} guests!"
                            )
                        except Exception as err:
                            conn.rollback()
                            st.error(f"Transaction failed: {err}")
            else:
                st.warning("No tables are currently available.")

        with t3:
            if st.session_state.user_role == "admin":
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT MAX(table_number) AS max_num FROM tables")
                result = cursor.fetchone()
                next_table_num = (result['max_num'] + 1) if result['max_num'] else 1
                
                st.info(f"The system detected that the next available Table Number is: **{next_table_num}**")
                
                # 2. Form table
                with st.form("add_table_form"):
                    # Cài đặt value = số bàn tiếp theo và khóa ô nhập (disabled=True)
                    new_table_no = st.number_input(
                        "New Table Number (Auto-generated)", value=next_table_num, disabled=True
                    )
                    new_capacity = st.number_input(
                        "Seating Capacity", min_value=1, step=1, value=4
                    )
                    
                    if st.form_submit_button("Add Table"):
                        try:
                            cursor.execute(
                                "INSERT INTO tables (table_number, status, capacity) VALUES (%s, 'Available', %s)",
                                (new_table_no, new_capacity),
                            )
                            conn.commit()
                            st.success(
                                f"Table #{new_table_no} added successfully!"
                            )
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning(
                    "Only Admin accounts have permission to add new tables."
                )

    # ==========================================
    # 3. MODULE: MENU MANAGEMENT
    # ==========================================
    elif choice == "Menu Management":
        st.header("🍴Food & Beverage Menu")
        t1, t2, t3 = st.tabs(
            ["View Menu", "Add New Dish (Admin)", "Edit Dish (Admin)"]
        )

        with t1:
            df_menu = pd.read_sql(
                "SELECT dish_id, dish_name, price, is_available FROM menu_items",
                conn,
            )
            df_menu["is_available"] = df_menu["is_available"].map(
                {1: "Yes (Available)", 0: "No (Out of Stock)"}
            )
            st.dataframe(df_menu, use_container_width=True)

        with t2:
            if st.session_state.user_role == "admin":
                with st.form("add_dish_form"):
                    dish_name = st.text_input("Dish Name")
                    price = st.number_input(
                        "Price (VND)", min_value=0, step=1000, format="%d"
                    )
                    cat_id = st.number_input("Category ID", min_value=1, step=1)

                    if st.form_submit_button("Add Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                (dish_name, price (VND), cat_id),
                            )
                            conn.commit()
                            st.success(
                                "New dish added to the menu successfully!"
                            )
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning(
                    "Only Admin accounts have permission to add new menu items."
                )

        with t3:
            if st.session_state.user_role == "admin":
                st.subheader("Update Price and Availability")
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT dish_id, dish_name, price, is_available FROM menu_items")
                dishes = cursor.fetchall()
                
                if dishes:
                    dish_options = {f"#{d['dish_id']} - {d['dish_name']} (Current: {int(d['price']):,} VND)": d for d in dishes}
                    
                    selected_dish_label = st.selectbox("Select Dish to Update", list(dish_options.keys()))
                    selected_dish = dish_options[selected_dish_label]
                    e_dish_id = selected_dish['dish_id']
                    
                    # 3. Form cập nhật thông tin
                    with st.form("edit_dish_form"):
                        e_price = st.number_input(
                            "New Price (VND)", 
                            min_value=0, 
                            step=1000, 
                            value=int(selected_dish['price']), 
                            format="%d"
                        )

                        e_avail = st.selectbox(
                            "Status",
                            options=[1],
                            index=0 if selected_dish['is_available'] == 1 else 1,
                            format_func=lambda x: "Available" if x == 1 else "Out of Stock"
                        )

                        if st.form_submit_button("Update Dish"):
                            try:
                                update_cursor = conn.cursor()
                                update_cursor.execute(
                                    "UPDATE menu_items SET price = %s, is_available = %s WHERE dish_id = %s",
                                    (e_price, e_avail, e_dish_id),
                                )
                                conn.commit()
                                st.success(f"Dish '{selected_dish['dish_name']}' updated successfully!")
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    st.info("No dishes found in the database. Please add a dish first.")
            else:
                st.warning(
                    "Only Admin accounts have permission to edit menu items."
                )

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
            st.subheader("Create New Invoice")
            cursor = conn.cursor(dictionary=True)
            st.markdown("Customer Search")
            cust_phone = st.text_input("Enter Customer Phone Number (Press Enter to search):")
            
            customer_id = None
            if cust_phone:
                cursor.execute("SELECT customer_id, name, points, tier FROM customers WHERE phone = %s", (cust_phone,))
                cust_info = cursor.fetchone()
                
                if cust_info:
                    customer_id = cust_info['customer_id']
                    st.success(f"**Found Customer:** {cust_info['name']} | **Tier:** {cust_info['tier']} | **Current Points: {cust_info['points']} pts**")
                else:
                    st.warning("Customer not found. Proceeding as a Walk-in Guest (No points accumulation).")

            st.markdown("---")
            st.markdown("Order Details")
            
            # Truy vấn menu 
            cursor.execute("SELECT dish_id, dish_name, price FROM menu_items WHERE is_available = 1")
            menu_items = cursor.fetchall()
            menu_options = {f"{item['dish_name']} - {int(item['price']):,} VND": item for item in menu_items}

            # lưu số lượng (món) đang được order, khởi tạo là 1
            if 'item_count' not in st.session_state:
                st.session_state.item_count = 1

            def add_dish_row():
                st.session_state.item_count += 1

            order_items = []
            
            for i in range(st.session_state.item_count):
                col1, col2 = st.columns(2) 
                
                with col1:
                    selected_dish_label = st.selectbox(f"Dish {i+1}", options=list(menu_options.keys()), key=f"dish_{i}")
                with col2:
                    qty = st.number_input(f"Qty {i+1}", min_value=1, step=1, value=1, key=f"qty_{i}")
                
                dish_info = menu_options[selected_dish_label]
                order_items.append({
                    "dish_id": dish_info['dish_id'],
                    "price": dish_info['price'],
                    "quantity": qty
                })
            
            # Add dish (add_dish_row)
            st.button("Add Another Dish", on_click=add_dish_row)
            
            st.markdown("---")
            order_type = st.selectbox("Order Type", ["Dine-in", "Takeaway", "Delivery"])
          
            if st.button("Generate Invoice & Checkout", type="primary"):
                try:
                    total_amount = sum(item['price'] * item['quantity'] for item in order_items)
                    
                    cursor.execute("""
                        INSERT INTO invoices (customer_id, total_amount, payment_date, order_type, delivery_status) 
                        VALUES (%s, %s, %s, %s, 'Delivered')
                    """, (customer_id, total_amount, datetime.now(), order_type))
                    
                    new_invoice_id = cursor.lastrowid
                    
                    for item in order_items:
                        line_subtotal = item['price'] * item['quantity']
                        cursor.execute("""
                            INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (new_invoice_id, item['dish_id'], item['quantity'], item['price'], line_subtotal))
                    
                    conn.commit()
                    
                    # Reset
                    st.session_state.item_count = 1
                    
                    st.success(f"Invoice #{new_invoice_id} created successfully! Grand Total: **{int(total_amount):,} VND**")
                    
                except Exception as e:
                    st.error(f"Error creating invoice: {e}")
                    conn.rollback()


    # 5. MODULE: ADMIN REPORTS
    elif choice == "Admin Reports":
        st.header("Admin Dashboard & Reports")

        if st.session_state.user_role != "admin":
            st.error(
                "Access Denied. You do not have permission to view this page."
            )
        else:
            t1, t2 = st.tabs(["Daily Revenue & Visits", "Top Selling Dishes"])

            with t1:
                st.subheader("Revenue & Customer Visits")
                rev_query = """
                    SELECT DATE(payment_date) AS Date, SUM(total_amount) AS Daily_Revenue, COUNT(invoice_id) AS Daily_Visits
                    FROM invoices
                    WHERE payment_date IS NOT NULL
                    GROUP BY DATE(payment_date)
                    ORDER BY Date
                """
                df_rev = pd.read_sql(rev_query, conn)

                if not df_rev.empty:
                    df_rev["Date"] = pd.to_datetime(df_rev["Date"]).dt.date

                    total_rev = int(df_rev["Daily_Revenue"].sum())
                    total_visits = int(df_rev["Daily_Visits"].sum())

                    col1, col2 = st.columns(2)
                    col1.metric("Total Revenue", f"{total_rev:,} VND")
                    col2.metric("Total Customer Visits", f"{total_visits} Invoices")

                    st.markdown("---")
                    st.markdown("**Daily Revenue Trend (VND)**")
                    st.line_chart(df_rev.set_index("Date")["Daily_Revenue"])

                    st.markdown("**Daily Customer Visits**")
                    st.bar_chart(df_rev.set_index("Date")["Daily_Visits"])
                else:
                    st.info("No revenue data available yet.")

            with t2:
                st.subheader("Top 5 Best-Selling Dishes")
                st.info(
                    "Data is fetched dynamically from the Database View: 'View_TopSellingDishes'"
                )

                df_top = pd.read_sql(
                    "SELECT * FROM View_TopSellingDishes LIMIT 5", conn
                )

                if not df_top.empty:
                    df_top.rename(
                        columns={
                            "dish_name": "Dish Name",
                            "total_sold": "Quantity Sold",
                        },
                        inplace=True,
                    )

                    colA, colB = st.columns([5, 6])
                    with colA:
                        st.dataframe(
                            df_top, use_container_width=True, hide_index=True
                        )
                    with colB:
                        st.bar_chart(df_top.set_index("Dish Name")["Quantity Sold"])
                else:
                    st.info("No sales data available yet.")

    # ==========================================
    # MODULE: CHANGE PASSWORD (THÊM VÀO KHOẢNG DÒNG 342)
    # ==========================================
    elif choice == "🔒 Change Password":
        st.header("🔒 Change Your Password")
        st.caption("For security purposes, please do not share your password with anyone.")
        
        with st.form("change_password_form", clear_on_submit=True):
            old_pass = st.text_input("Old Password", type="password")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm New Password", type="password")
            
            submit_btn = st.form_submit_button("Update Password", type="primary")
            
            if submit_btn:
                if not old_pass or not new_pass or not confirm_pass:
                    st.error("Please fill in all fields.")
                elif new_pass == old_pass:
                    st.warning("New password cannot be the same as the old password.")
                elif new_pass != confirm_pass:
                    st.error("New password and Confirm password do not match.")
                elif len(new_pass) < 6:
                    st.warning("New password should be at least 6 characters long.")
                else:
                    current_user = st.session_state.get("login_user")
                    success, message = change_password_db(current_user, old_pass, new_pass)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)

    if conn:
        conn.close()

    if conn:
        conn.close()


