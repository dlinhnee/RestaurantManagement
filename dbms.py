import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error

# --- DATABASE CONNECTION ---
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Dieulinh2022!', 
            database='RestaurantManagement'
        )
        return conn
    except Error as e:
        st.error(f"MySQL Connection Error: {e}")
        return None

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Restaurant Management System", layout="wide")

# --- LOGIN & SECURITY (Requirement: User Roles) ---
def check_auth():
    st.sidebar.title("System Login")
    user_role = st.sidebar.selectbox("Select Role", ["Admin", "Cashier", "Waiter"])
    username = st.sidebar.text_input("Username", value="Linh")
    return user_role if username else None

role = check_auth()

if role:
    st.title(f"Restaurant System - {role} Portal")
    
    # --- NAVIGATION MENU (Requirement: Main Functionalities) ---
    tabs = ["Dashboard", "Tables", "Reservations", "Menu", "Billing", "Customers"]
    choice = st.selectbox("Navigate to Section:", tabs)
    
    conn = connect_db()
    if conn:
        # 1. DASHBOARD (Requirement: Reporting & Views)
        if choice == "Dashboard":
            st.header("Business Analytics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Calculate Revenue using SQL SUM (Requirement: Reporting)
                # Sửa TotalAmount thành total_amount và Invoices thành invoices
                rev_df = pd.read_sql("SELECT SUM(total_amount) as Revenue FROM invoices", conn)
                st.metric("Total Revenue", f"${rev_df['Revenue'][0]:,.2f}")
            
            with col2:
                # Display Available Tables using the View created (Requirement: Views)
                avail_df = pd.read_sql("SELECT COUNT(*) as Count FROM View_TableStatus WHERE Status = 'Available'", conn)
                st.metric("Available Tables", avail_df['Count'][0])
                
            with col3:
                # Reporting on Customer Visits
                visit_df = pd.read_sql("SELECT COUNT(*) as Visits FROM Reservations", conn)
                st.metric("Total Reservations", visit_df['Visits'][0])

            st.subheader("Top Selling Dishes")
            # Query optimizing using Indexes (Requirement: Performance Tuning)
            top_dishes = pd.read_sql("""
                SELECT m.DishName, SUM(id.Quantity) as Sold 
                FROM MenuItems m 
                JOIN InvoiceDetails id ON m.DishID = id.DishID 
                GROUP BY m.DishName ORDER BY Sold DESC LIMIT 5
            """, conn)
            st.bar_chart(top_dishes.set_index('DishName'))

        # 2. TABLES MANAGEMENT
        elif choice == "Tables":
            st.header("Table Status Management")
            df_tables = pd.read_sql("SELECT * FROM Tables", conn)
            st.dataframe(df_tables, use_container_width=True)
            
            if role == "Admin":
                with st.expander("Add New Table"):
                    t_num = st.number_input("Table Number", min_value=1)
                    if st.button("Add Table"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Tables (TableNumber, Status) VALUES (%s, 'Available')", (t_num,))
                        conn.commit()
                        st.success(f"Table {t_num} added!")
                        st.rerun()

        # 3. RESERVATIONS (Requirement: Reservation System)
        elif choice == "Reservations":
            st.header("Table Reservations")
            col_a, col_b = st.columns([1, 2])
            
            with col_a:
                st.subheader("New Booking")
                cust_id = st.number_input("Customer ID", min_value=1)
                table_id = st.number_input("Table ID", min_value=1)
                guests = st.number_input("Guest Count", min_value=1)
                res_date = st.date_input("Reservation Date")
                
                if st.button("Confirm Booking"):
                    cursor = conn.cursor()
                    query = "INSERT INTO Reservations (CustomerID, TableID, DateTime, GuestCount) VALUES (%s, %s, %s, %s)"
                    cursor.execute(query, (cust_id, table_id, res_date, guests))
                    conn.commit()
                    st.success("Booking confirmed! Table status updated via Trigger.") #
            
            with col_b:
                st.subheader("Current Schedule")
                df_res = pd.read_sql("SELECT * FROM Reservations ORDER BY DateTime DESC", conn)
                st.table(df_res)

        # 4. MENU MANAGEMENT
        elif choice == "Menu":
            st.header("Menu Items")
            df_menu = pd.read_sql("SELECT * FROM MenuItems", conn)
            st.data_editor(df_menu, key="menu_editor") # Requirement: Edit dishes
            
            if role == "Admin":
                with st.expander("Add New Dish"):
                    d_name = st.text_input("Dish Name")
                    d_price = st.number_input("Price ($)", min_value=0.0)
                    if st.button("Add to Menu"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO MenuItems (DishName, Price) VALUES (%s, %s)", (d_name, d_price))
                        conn.commit()
                        st.success(f"{d_name} added!")
                        st.rerun()

        # 5. BILLING (Requirement: Invoices & Procedures)
        elif choice == "Billing":
            st.header("Billing & Payments")
            
            with st.form("payment_form"):
                inv_id = st.number_input("Invoice ID", min_value=1)
                submit_pay = st.form_submit_button("Process Payment")
                
                if submit_pay:
                    cursor = conn.cursor()
                    # Calculate VAT using UDF (Requirement: User Defined Functions)
                    cursor.execute("SELECT TotalAmount FROM Invoices WHERE InvoiceID = %s", (inv_id,))
                    result = cursor.fetchone()
                    if result:
                        base_val = result[0]
                        cursor.execute("SELECT CalculateVAT(%s)", (base_val,)) #
                        final_val = cursor.fetchone()[0]
                        
                        st.write(f"Base Amount: ${base_val:,.2f}")
                        st.write(f"Total with VAT (10%): ${final_val:,.2f}")
                        
                        # Automate status update via Procedure (Requirement: Stored Procedures)
                        cursor.callproc('ProcessPayment', [inv_id]) #
                        conn.commit()
                        st.success("Payment successful! Table is now Available.")
                    else:
                        st.error("Invoice ID not found.")

        # 6. CUSTOMER MANAGEMENT
        elif choice == "Customers":
            st.header("Customer Directory")
            df_cust = pd.read_sql("SELECT * FROM Customers", conn)
            st.dataframe(df_cust, use_container_width=True)
            
            with st.expander("Register New Customer"):
                name = st.text_input("Full Name")
                phone = st.text_input("Phone Number")
                addr = st.text_input("Address")
                if st.button("Register"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Customers (CustomerName, PhoneNumber, Address) VALUES (%s, %s, %s)", (name, phone, addr))
                    conn.commit()
                    st.success("Customer registered!")
                    st.rerun()

        conn.close()

