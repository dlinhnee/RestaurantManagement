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


def self_reset_password_db(username):
    """Allows staff to self-reset password to '123456' using Username only"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT employee_id FROM employees WHERE username = %s", 
                (username,)
            )
            emp = cursor.fetchone()
            
            if emp:
                default_password_hash = hash_password("123456")
                cursor.execute(
                    "UPDATE employees SET password = %s WHERE employee_id = %s",
                    (default_password_hash, emp["employee_id"])
                )
                conn.commit()
                return True, "Password has been successfully reset to default '123456'!"
            else:
                return False, "Username does not exist."
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
    tab_login, tab_forgot = st.tabs(["Staff Login", "Forgot Password"])
    
    with tab_login:
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

    with tab_forgot:
        st.header("Reset Password")
        st.info("Enter your registered Username to reset your password back to default.")
        
        with st.form("forgot_password_form"):
            reset_username = st.text_input("Enter Username to Reset")
            submit_reset = st.form_submit_button("Reset Password to Default")
            
            if submit_reset:
                if not reset_username:
                    st.warning("Please enter your Username!")
                else:
                    success, message = self_reset_password_db(reset_username)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                        
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
    # MODULE: CHANGE PASSWORD
    # ==========================================
    if choice == "Change Password":
        st.header("Change Password")
        with st.form("change_password_form"):
            cp_username = st.text_input("Confirm Your Username")
            cp_old = st.text_input("Old Password", type="password")
            cp_new = st.text_input("New Password", type="password")
            # THÊM Ô NHẬP XÁC NHẬN MẬT KHẨU MỚI
            cp_confirm = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password"):
                if not cp_username or not cp_old or not cp_new or not cp_confirm:
                    st.warning("All fields are required!")
                # KIỂM TRA XEM MẬT KHẨU MỚI VÀ XÁC NHẬN CÓ TRÙNG NHAU KHÔNG
                elif cp_new != cp_confirm:
                    st.error("New password and confirm password do not match!")
                else:
                    success, msg = change_password_db(cp_username, cp_old, cp_new)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

    # ==========================================
    # MODULE 1: CUSTOMER MANAGEMENT
    # ==========================================
    elif choice == "Customer Management":
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
        t1, t2, t3 = st.tabs(["Table Status", "Book a Table", "Reservation Details"])

        # TAB 1: VIEW CURRENT SLOTS STATUS
        with t1:
            df_tables = pd.read_sql(
                "SELECT table_number, status, capacity FROM tables", conn
            )
            st.dataframe(df_tables, use_container_width=True)

        # TAB 2: SMART CREATION WITH AUTO-CUSTOMER LOOKUP
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
                        tx_cursor = conn.cursor(dictionary=True)
                        try:
                            conn.autocommit = False

                            # 1. Search for customer profile by Phone
                            tx_cursor.execute(
                                "SELECT customer_id, name FROM customers WHERE phone = %s",
                                (r_phone,),
                            )
                            existing_cust = tx_cursor.fetchone()

                            if existing_cust:
                                final_cust_id = existing_cust["customer_id"]
                                st.success(f"Found returning customer: {existing_cust['name']}")
                            else:
                                if not r_name:
                                    st.warning("New phone number detected! Please enter the Customer Name to create a profile.")
                                    st.stop()
                                
                                # 2. Create new missing customer data split
                                tx_cursor.execute(
                                    "INSERT INTO customers (name, phone) VALUES (%s, %s)",
                                    (r_name, r_phone),
                                )
                                final_cust_id = tx_cursor.lastrowid
                                st.success(f"New customer profile created for '{r_name}'")

                            # 3. Create reservation baseline record entry
                            tx_cursor.execute(
                                "INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES (%s, %s, %s)",
                                (final_cust_id, datetime.now(), guests),
                            )
                            new_res_id = tx_cursor.lastrowid

                            # 4. Save intersection key indices relation link mappings
                            tx_cursor.execute(
                                "INSERT INTO reservation_detail (reservation_id, table_id) VALUES (%s, %s)",
                                (new_res_id, selected_table["table_id"]),
                            )
                            
                            conn.commit()
                            st.success(f"Table {selected_table['table_number']} booked successfully for {guests} guests!")
                            st.rerun()
                            
                        except Exception as err:
                            conn.rollback()
                            st.error(f"Transaction failed: {err}")
                        finally:
                            tx_cursor.close()
                            conn.autocommit = True
            else:
                st.warning("No tables are currently available.")

        # TAB 3: MERGED INTERACTIVE LIVE LOGVIEW & RECORD DELETION
        with t3:
            st.subheader("Reservation Details")
            
            # 1. Fetch live contextual grid reports
            query_reservations = """
                SELECT 
                    r.reservation_id AS 'Res ID',
                    t.table_number AS 'Table No.', 
                    c.name AS 'Customer Name', 
                    c.phone AS 'Phone Number', 
                    r.reservation_time AS 'Time', 
                    r.guest_count AS 'Guests'
                FROM reservations r
                JOIN customers c ON r.customer_id = c.customer_id
                JOIN reservation_detail rd ON r.reservation_id = rd.reservation_id
                JOIN tables t ON rd.table_id = t.table_id
                ORDER BY r.reservation_time DESC
            """
            df_reservations = pd.read_sql(query_reservations, conn)
            st.dataframe(df_reservations, use_container_width=True)

            st.markdown("---") 
            
            # 2. Cancel function entry processing area
            st.subheader("Cancel a Reservation")
            cancel_res_id = st.number_input("Enter Res ID to Cancel (from the table above)", min_value=1, step=1, key="res_cancel_input_field")
            
            if st.button("Cancel Booking", type="primary"):
                cancel_cursor = conn.cursor()
                try:
                    conn.autocommit = False
                    
                    # Track which table records are bound before dumping entity instances
                    cancel_cursor.execute("SELECT table_id FROM reservation_detail WHERE reservation_id = %s", (cancel_res_id,))
                    tables_to_free = cancel_cursor.fetchall()
                    
                    # Update back state definitions to clear occupied locks out
                    for tb in tables_to_free:
                        cancel_cursor.execute("UPDATE tables SET status = 'Available' WHERE table_id = %s", (tb[0],))
                    
                    # Structural removal
                    cancel_cursor.execute("DELETE FROM reservation_detail WHERE reservation_id = %s", (cancel_res_id,))
                    cancel_cursor.execute("DELETE FROM reservations WHERE reservation_id = %s", (cancel_res_id,))
                    
                    conn.commit()
                    st.success(f"Reservation #{cancel_res_id} has been canceled. Tables are now Available!")
                    st.rerun()
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error canceling reservation: {e}")
                finally:
                    cancel_cursor.close()
                    conn.autocommit = True

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
                        "Price (VND)", min_value=0, step=1000, value=25000, format="%d"
                    )
                    cat_id = st.number_input("Category ID", min_value=1, step=1)

                    if st.form_submit_button("Add Dish"):
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO menu_items (dish_name, price, category_id) VALUES (%s, %s, %s)",
                                (dish_name, price, cat_id),
                            )
                            conn.commit()
                            st.success(
                                "New dish added to the menu successfully!"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            cursor.close()
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
                            options=[1, 0],
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
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                update_cursor.close()
                else:
                    st.info("No dishes found in the database. Please add a dish first.")
                
                cursor.close()
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
            cust_info = None
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
            
            st.button("Add Another Dish", on_click=add_dish_row)
            
            st.markdown("---")
            order_type = st.selectbox("Order Type", ["Dine-in", "Takeaway", "Delivery"])
          
            # 1. CALCULATE ORIGINAL SUBTOTAL BEFORE DISCOUNT
            original_total = sum(item['price'] * item['quantity'] for item in order_items)
            st.write(f"**Subtotal:** {int(original_total):,} VND")

            # 2. LOYALTY POINT REDEMPTION LOGIC
            points_to_redeem = 0
            discount_amount = 0
            current_points = cust_info['points'] if cust_info else 0

            if customer_id and current_points > 0:
                max_points_allowed = min(current_points, int(original_total / 100))
                
                points_to_redeem = st.number_input(
                    f"Enter points to redeem (Max: {max_points_allowed} pts, Available: {current_points} pts)", 
                    min_value=0, 
                    max_value=max_points_allowed, 
                    step=1
                )
                discount_amount = points_to_redeem * 100

            # 3. CALCULATE GRAND TOTAL & NEW EARNED POINTS
            final_total = original_total - discount_amount
            earned_points = int(final_total // 1000) 

            if points_to_redeem > 0:
                st.write(f"**Discount (Redeemed Points):** - {int(discount_amount):,} VND")
            
            st.markdown(f"### **Grand Total:** {int(final_total):,} VND")
            if customer_id:
                st.caption(f"*(Customer will redeem {points_to_redeem} pts and earn {earned_points} new pts from this invoice)*")

            # 4. CHECKOUT & UPDATE DATABASE
            if st.button("Generate Invoice & Checkout", type="primary"):
                try:
                    cursor = conn.cursor()
                    conn.start_transaction() 
                    
                    # A. Insert into Invoices table
                    cursor.execute("""
                        INSERT INTO invoices (customer_id, total_amount, payment_date, order_type, delivery_status) 
                        VALUES (%s, %s, %s, %s, 'Delivered')
                    """, (customer_id, final_total, datetime.now(), order_type))
                    
                    new_invoice_id = cursor.lastrowid
                    
                    # B. Insert into Invoice_Details table
                    for item in order_items:
                        line_subtotal = item['price'] * item['quantity']
                        cursor.execute("""
                            INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (new_invoice_id, item['dish_id'], item['quantity'], item['price'], line_subtotal))
                    
                    # C. Update Customer Points
                    if customer_id:
                        cursor.execute("""
                            UPDATE customers 
                            SET points = points - %s + %s 
                            WHERE customer_id = %s
                        """, (points_to_redeem, earned_points, customer_id))
                    
                    conn.commit()
                    st.session_state.item_count = 1
                    st.success(f"Invoice #{new_invoice_id} created successfully! Grand Total: **{int(final_total):,} VND**")
                    st.rerun()
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error creating invoice: {e}")
                finally:
                    cursor.close()

    # ==========================================
    # 5. MODULE: ADMIN REPORTS
    # ==========================================
    elif choice == "Admin Reports":
        st.header("Admin Dashboard & Reports")

        if st.session_state.user_role != "admin":
            st.error("Access Denied. You do not have permission to view this page.")
        else:
            t1, t2 = st.tabs(["Daily Revenue & Visits", "Top Selling Dishes"])

            with t1:
                st.subheader("Revenue & Customer Visits")
                rev_query = """
                    SELECT DATE(payment_date) AS Date, SUM(total_amount) AS Daily_Revenue, COUNT(invoice_id) AS Daily_Visits
                    FROM invoices
                    GROUP BY DATE(payment_date)
                    ORDER BY Date DESC
                """
                df_rev = pd.read_sql(rev_query, conn)
                st.dataframe(df_rev, use_container_width=True)

            with t2:
                st.subheader("Top Selling Dishes")
                top_query = """
                    SELECT m.dish_name AS `Dish Name`, SUM(id.quantity) AS `Total Qty Sold`
                    FROM invoice_details id
                    JOIN menu_items m ON id.dish_id = m.dish_id
                    GROUP BY m.dish_id, m.dish_name
                    ORDER BY `Total Qty Sold` DESC
                """
                df_top = pd.read_sql(top_query, conn)
                st.dataframe(df_top, use_container_width=True)
