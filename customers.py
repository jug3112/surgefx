import streamlit as st
import pandas as pd
import sqlite3
import os
import random
import string
from datetime import datetime

# Customer database path
CUSTOMERS_DB_PATH = 'data/customer_database.db'

# Function to initialize customer database
def initialize_customer_database():
    """Creates the customer database and table structure"""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Create/connect to the database
    conn = sqlite3.connect(CUSTOMERS_DB_PATH)
    cursor = conn.cursor()
    
    # Create the customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        email TEXT NOT NULL,
        mobile_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    
    # Check if table is empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

# Function to ensure customer database exists and contains data
def ensure_customer_database():
    """Ensures customer database exists and has data"""
    # First create the database and table if they don't exist
    record_count = initialize_customer_database()
    
    # If no records, show the generate button
    if record_count == 0:
        st.warning("Customer database is empty.")
        st.info("Click the button below to generate a database with 1000 sample customers.")
        
        if st.button("Generate Customer Database"):
            with st.spinner("Generating customer database..."):
                try:
                    generate_customer_data()
                    st.success("Customer database generated successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error generating customer database: {e}")
            return False
    return True

# Function to generate customer data
def generate_customer_data():
    """Generates 1000 sample customer records"""
    # Initialize the database to ensure table exists
    initialize_customer_database()
    
    # Connection to the database
    conn = sqlite3.connect(CUSTOMERS_DB_PATH)
    cursor = conn.cursor()

    # Lists for generating realistic customer data
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
        "Raj", "Priya", "Amit", "Neha", "Rahul", "Anjali", "Vikram", "Pooja", "Sanjay", "Meera",
        "Chen", "Wei", "Li", "Yan", "Zhang", "Min", "Liu", "Jing", "Wang", "Hui",
        "Mohammed", "Fatima", "Ahmed", "Aisha", "Omar", "Zainab", "Ali", "Layla", "Hassan", "Noor"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Patel", "Sharma", "Singh", "Kumar", "Shah", "Gupta", "Rao",
        "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
        "Ali", "Khan", "Ahmed", "Hassan", "Mohammed", "Abdullah", "Rahman", "Hussein", "Said", "Omar"
    ]

    email_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", 
                    "aol.com", "protonmail.com", "mail.com", "zoho.com", "yandex.com"]

    mobile_types = ["iOS", "Android"]  # Including only iOS and Android as specified
    mobile_type_weights = [0.45, 0.55]  # 45% iOS, 55% Android

    # Generate 1000 customer records
    customer_data = []

    for i in range(1, 1001):
        # Generate customer_id
        customer_id = f"CUST{i:06d}"
        
        # Generate name
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        customer_name = f"{first_name} {last_name}"
        
        # Generate mobile number (10 digits)
        mobile_number = "".join(random.choices(string.digits, k=10))
        mobile_number = f"+1{mobile_number}"  # US format
        
        # Generate email based on name
        email_prefix = f"{first_name.lower()}.{last_name.lower()}"
        email_prefix = ''.join(c for c in email_prefix if c.isalnum() or c == '.')
        random_number = random.randint(1, 99)
        email_domain = random.choice(email_domains)
        email = f"{email_prefix}{random_number}@{email_domain}"
        
        # Assign mobile type with weighted distribution
        mobile_type = random.choices(mobile_types, weights=mobile_type_weights, k=1)[0]
        
        # Add to the list of customer data
        customer_data.append((customer_id, customer_name, mobile_number, email, mobile_type))

    # Insert data into the database
    cursor.executemany(
        "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
        customer_data
    )
    conn.commit()
    conn.close()

# Function to load customers data with caching
@st.cache_data(ttl=300)
def load_customers_data(_conn, filters=None):
    """Loads customer data with optional filters"""
    try:
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
        
        return pd.read_sql_query(query, _conn)
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

# Function to get filter options for customers
@st.cache_data(ttl=300)
def get_customers_filter_options(_conn):
    """Gets available filter options for customers"""
    try:
        # First check if the table exists
        cursor = _conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        if not cursor.fetchone():
            return {'mobile_types': []}
            
        mobile_types = pd.read_sql_query("SELECT DISTINCT mobile_type FROM customers ORDER BY mobile_type", _conn)['mobile_type'].tolist()
        return {
            'mobile_types': mobile_types
        }
    except Exception as e:
        st.error(f"Error loading filter options: {e}")
        return {'mobile_types': []}

# Function to add a real customer
def add_real_customer(conn, customer_name, mobile_number, email, mobile_type):
    """Adds a real customer to the database"""
    cursor = conn.cursor()
    
    # Generate a new customer_id based on current max ID
    cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
    max_id_result = cursor.fetchone()[0]
    
    # Handle case where there are no customers yet
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
    """Displays the customers tab content"""
    st.header("Customer Database")
    
    # Initialize the database
    initialize_customer_database()
    
    # Ensure customer database has data
    if not ensure_customer_database():
        return
    
    try:
        # Connect to the customer database
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
    except Exception as e:
        st.error(f"Error connecting to customer database: {e}")
        return
    
    # Sidebar filters for customers
    with st.sidebar:
        st.subheader("Filter Customers")
        
        try:
            customer_filter_options = get_customers_filter_options(conn)
        except Exception as e:
            st.error(f"Error loading customer filter options: {e}")
            customer_filter_options = {"mobile_types": []}
        
        # Create filters
        customer_name_filter = st.text_input("Search by Name")
        
        # Only show mobile type filter if we have options
        if customer_filter_options["mobile_types"]:
            selected_mobile_type = st.selectbox("Mobile Type", ["All"] + customer_filter_options["mobile_types"])
        else:
            selected_mobile_type = "All"
        
        # Apply filters
        customer_filters = {}
        if customer_name_filter:
            customer_filters["customer_name"] = customer_name_filter
        if selected_mobile_type != "All":
            customer_filters["mobile_type"] = selected_mobile_type
        
        if st.button("Reset Customer Filters"):
            customer_filters = {}
    
    # Load customer data
    try:
        customers_df = load_customers_data(conn, customer_filters)
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        customers_df = pd.DataFrame()
    
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
    
    # Add real customer section
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
