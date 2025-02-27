import streamlit as st
import pandas as pd
import sqlite3
import os
import random
import string

# Customer database path
CUSTOMERS_DB_PATH = 'data/customer_database.db'

def ensure_customer_database():
    """Checks if the customer database exists and has data"""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Check if database file exists
    if not os.path.exists(CUSTOMERS_DB_PATH):
        st.warning("Customer database not found.")
        st.info("Click the button below to generate a database with 1000 sample customers.")
        
        if st.button("Generate Customer Database"):
            generate_customer_data()
            st.success("Customer database generated successfully! Refresh the page to see the data.")
            return False
        return False
    
    # Check if database has data
    try:
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
        cursor = conn.cursor()
        
        # Check if customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        if not cursor.fetchone():
            st.warning("Customer database structure is invalid.")
            if st.button("Recreate Customer Database"):
                generate_customer_data()
                st.success("Customer database recreated successfully! Refresh the page to see the data.")
                return False
            return False
        
        # Check if table has records
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            st.warning("Customer database is empty.")
            if st.button("Generate Customer Data"):
                generate_customer_data()
                st.success("Customer data generated successfully! Refresh the page to see the data.")
                return False
            return False
        
        return True
    except Exception as e:
        st.error(f"Error checking customer database: {e}")
        if st.button("Recreate Customer Database"):
            generate_customer_data()
            st.success("Customer database recreated successfully! Refresh the page to see the data.")
        return False

def generate_customer_data():
    """Generates a new customer database with 1000 records"""
    try:
        # Remove existing database if it exists
        if os.path.exists(CUSTOMERS_DB_PATH):
            os.remove(CUSTOMERS_DB_PATH)
        
        # Create a new database
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute('''
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            email TEXT NOT NULL,
            mobile_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Simple data for generation
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
                       "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                      "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
        mobile_types = ["iOS", "Android"]
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
        
        # Generate customer data
        customer_data = []
        for i in range(1000):
            customer_id = f"CUST{i+1:06d}"
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            customer_name = f"{first_name} {last_name}"
            mobile_number = f"+1{''.join(random.choices(string.digits, k=10))}"
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{random.choice(email_domains)}"
            mobile_type = random.choice(mobile_types)
            
            customer_data.append((customer_id, customer_name, mobile_number, email, mobile_type))
        
        # Insert data in batches
        batch_size = 100
        for i in range(0, len(customer_data), batch_size):
            batch = customer_data[i:i+batch_size]
            cursor.executemany(
                "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
                batch
            )
            conn.commit()
        
        # Add 3 real customers
        real_customers = [
            ("CUST901001", "John Smith", "+12025550123", "john.smith@example.com", "iOS"),
            ("CUST901002", "Mary Johnson", "+16505551234", "mary.johnson@example.com", "Android"),
            ("CUST901003", "Robert Davis", "+13125552345", "robert.davis@example.com", "iOS")
        ]
        
        for customer in real_customers:
            try:
                cursor.execute(
                    "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
                    customer
                )
            except sqlite3.IntegrityError:
                # If ID exists, try with a different ID
                pass
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        st.error(f"Error generating customer database: {e}")
        return False

def load_customers_data(conn, filters=None):
    """Load customer data with optional filters"""
    query = "SELECT * FROM customers"
    params = []
    
    if filters:
        conditions = []
        
        if filters.get('customer_name'):
            conditions.append("customer_name LIKE ?")
            params.append(f"%{filters['customer_name']}%")
        
        if filters.get('mobile_type'):
            conditions.append("mobile_type = ?")
            params.append(filters['mobile_type'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    return pd.read_sql_query(query, conn, params=params)

def get_customers_filter_options(conn):
    """Get available filter options"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT mobile_type FROM customers")
    mobile_types = [row[0] for row in cursor.fetchall()]
    return {'mobile_types': mobile_types}

def add_real_customer(conn, customer_name, mobile_number, email, mobile_type):
    """Add a real customer to the database"""
    cursor = conn.cursor()
    
    # Generate a new customer_id
    cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
    max_id_result = cursor.fetchone()[0]
    
    if max_id_result is None:
        max_id = 0
    else:
        max_id = int(max_id_result)
    
    new_id = max_id + 1
    customer_id = f"CUST{new_id:06d}"
    
    # Insert the new customer
    cursor.execute(
        "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
        (customer_id, customer_name, mobile_number, email, mobile_type)
    )
    conn.commit()
    return customer_id

def show_customers_tab():
    """Display the customers tab UI"""
    st.header("Customer Database")
    
    # Ensure customer database exists and has data
    if not ensure_customer_database():
        return
    
    # Connect to the database
    try:
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.subheader("Filter Customers")
        
        # Get filter options
        try:
            filter_options = get_customers_filter_options(conn)
            
            # Create filters
            customer_name_filter = st.text_input("Search by Name")
            
            if filter_options['mobile_types']:
                selected_mobile_type = st.selectbox("Mobile Type", ["All"] + filter_options['mobile_types'])
            else:
                selected_mobile_type = "All"
            
            # Apply filters
            filters = {}
            if customer_name_filter:
                filters['customer_name'] = customer_name_filter
            if selected_mobile_type != "All":
                filters['mobile_type'] = selected_mobile_type
            
            if st.button("Reset Filters"):
                filters = {}
        except Exception as e:
            st.error(f"Error loading filter options: {e}")
            filters = {}
    
    # Load and display customer data
    try:
        customers_df = load_customers_data(conn, filters)
        
        if customers_df.empty:
            st.info("No customers found matching your filters.")
        else:
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Customers", f"{len(customers_df):,}")
            
            with col2:
                ios_users = len(customers_df[customers_df["mobile_type"] == "iOS"])
                st.metric("iOS Users", f"{ios_users:,}")
            
            with col3:
                android_users = len(customers_df[customers_df["mobile_type"] == "Android"])
                st.metric("Android Users", f"{android_users:,}")
            
            # Display customer table
            st.subheader("Customer Data")
            st.dataframe(customers_df)
            
            # CSV download button
            csv = customers_df.to_csv(index=False)
            st.download_button(
                label="Download Customers as CSV",
                data=csv,
                file_name="filtered_customers.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
    
    # Add real customer form
    st.markdown("---")
    st.subheader("Add Real Customer")
    
    with st.form("add_customer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_customer_name = st.text_input("Customer Name")
            new_mobile_number = st.text_input("Mobile Number")
        
        with col2:
            new_email = st.text_input("Email Address")
            new_mobile_type = st.selectbox("Mobile Type", ["iOS", "Android"])
        
        submit_button = st.form_submit_button("Add Customer")
    
    if submit_button:
        if not new_customer_name or not new_mobile_number or not new_email:
            st.error("Please fill in all required fields.")
        else:
            try:
                customer_id = add_real_customer(
                    conn, 
                    new_customer_name, 
                    new_mobile_number, 
                    new_email, 
                    new_mobile_type
                )
                st.success(f"Customer added successfully with ID: {customer_id}")
                st.info("Refresh the page to see the updated customer list.")
            except Exception as e:
                st.error(f"Error adding customer: {e}")
    
    # Close the database connection
    conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="Customer Database", layout="wide")
    show_customers_tab()
