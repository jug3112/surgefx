import streamlit as st
import sqlite3
import os
import pandas as pd
import random
import string
from datetime import datetime

def admin_panel():
    """Admin panel for database management"""
    st.title("Database Administration")
    
    # Password protection (simple)
    password = st.text_input("Enter admin password", type="password")
    if password != "admin123":  # Simple password, change in production
        st.warning("Enter the admin password to continue")
        return
    
    st.success("Admin access granted")
    
    # Create tabs for different admin functions
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Database Diagnostics", "Customer DB Management", "Data Explorer"])
    
    # Database Diagnostics Tab
    with admin_tab1:
        st.header("Database Diagnostics")
        
        if st.button("Run Database Diagnostics"):
            run_database_diagnostics()
    
    # Customer DB Management Tab
    with admin_tab2:
        st.header("Customer Database Management")
        
        st.warning("⚠️ These actions will modify your database!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Customer Database", use_container_width=True):
                create_customer_database()
        
        with col2:
            if st.button("Reset Customer Database", use_container_width=True):
                reset_customer_database()
    
    # Data Explorer Tab
    with admin_tab3:
        st.header("Database Explorer")
        
        db_type = st.selectbox("Select Database", ["Customers", "Offers"])
        
        if db_type == "Customers":
            explore_customer_database()
        else:
            explore_offers_database()

def run_database_diagnostics():
    """Run diagnostics on all databases"""
    st.subheader("Customer Database")
    
    # Database path
    db_path = 'data/customer_database.db'
    
    # Check if data directory exists
    if not os.path.exists('data'):
        st.error("❌ 'data' directory does not exist")
        st.info("Creating data directory...")
        os.makedirs('data', exist_ok=True)
        st.success("✅ Data directory created")
    else:
        st.success("✅ 'data' directory exists")
    
    # Check if database file exists
    if not os.path.exists(db_path):
        st.error("❌ Customer database file does not exist")
        st.info("Run 'Create Customer Database' to fix this issue")
    else:
        st.success(f"✅ Database file exists at {db_path}")
        file_size_kb = os.path.getsize(db_path) / 1024
        st.info(f"File size: {file_size_kb:.2f} KB")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if customers table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                st.error("❌ 'customers' table does not exist in the database")
                st.info("Run 'Create Customer Database' to fix this issue")
            else:
                st.success("✅ 'customers' table exists in the database")
                
                # Count records
                cursor.execute("SELECT COUNT(*) FROM customers")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    st.error("❌ 'customers' table is empty (0 records)")
                    st.info("Run 'Create Customer Database' to populate the database")
                else:
                    st.success(f"✅ 'customers' table contains {count} records")
                    
                    # Get mobile type distribution
                    cursor.execute("SELECT mobile_type, COUNT(*) FROM customers GROUP BY mobile_type")
                    distribution = cursor.fetchall()
                    
                    st.write("Mobile type distribution:")
                    dist_df = pd.DataFrame(distribution, columns=["Device Type", "Count"])
                    st.dataframe(dist_df)
                    
                    # Show sample data
                    st.write("Sample customer records:")
                    cursor.execute("SELECT * FROM customers LIMIT 5")
                    columns = [desc[0] for desc in cursor.description]
                    sample_data = cursor.fetchall()
                    sample_df = pd.DataFrame(sample_data, columns=columns)
                    st.dataframe(sample_df)
            
            # Close connection
            conn.close()
            
        except sqlite3.Error as e:
            st.error(f"❌ Database error: {e}")
            st.info("This could indicate database corruption or permission issues")
    
    # Check offers database as well
    st.subheader("Offers Database")
    offers_db_path = 'data/offers_database.db'
    
    if not os.path.exists(offers_db_path):
        st.error("❌ Offers database file does not exist")
    else:
        st.success(f"✅ Offers database file exists at {offers_db_path}")
        file_size_kb = os.path.getsize(offers_db_path) / 1024
        st.info(f"File size: {file_size_kb:.2f} KB")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(offers_db_path)
            cursor = conn.cursor()
            
            # Check if offers table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='offers'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                st.error("❌ 'offers' table does not exist in the database")
            else:
                st.success("✅ 'offers' table exists in the database")
                
                # Count records
                cursor.execute("SELECT COUNT(*) FROM offers")
                count = cursor.fetchone()[0]
                st.success(f"✅ 'offers' table contains {count} records")
            
            # Close connection
            conn.close()
        
        except sqlite3.Error as e:
            st.error(f"❌ Offers database error: {e}")

def create_customer_database():
    """Create a new customer database with sample data"""
    # Database path
    db_path = 'data/customer_database.db'
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Progress indicator
    progress = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Creating new database...")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            status_text.text("Removed existing database...")
        except Exception as e:
            st.error(f"Error removing existing database: {e}")
            return
    
    progress.progress(10)
    
    try:
        # Create a new database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        status_text.text("Creating tables...")
        # Create customer table
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
        conn.commit()
        
        progress.progress(20)
        
        # Simple data for generation
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
                      "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                     "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
        mobile_types = ["iOS", "Android"]
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
        
        status_text.text("Generating customer data...")
        
        # Generate customer data
        total_customers = 1000
        batch_size = 100
        
        for batch_start in range(0, total_customers, batch_size):
            batch_end = min(batch_start + batch_size, total_customers)
            status_text.text(f"Generating customers {batch_start+1} to {batch_end}...")
            
            customer_data = []
            for i in range(batch_start, batch_end):
                customer_id = f"CUST{i+1:06d}"
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                customer_name = f"{first_name} {last_name}"
                mobile_number = f"+1{''.join(random.choices(string.digits, k=10))}"
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{random.choice(email_domains)}"
                mobile_type = random.choice(mobile_types)
                
                customer_data.append((customer_id, customer_name, mobile_number, email, mobile_type))
            
            # Insert batch
            cursor.executemany(
                "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
                customer_data
            )
            conn.commit()
            
            # Update progress
            progress_value = 20 + (batch_end * 70 / total_customers)
            progress.progress(int(progress_value))
        
        status_text.text("Adding real customer examples...")
        
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
                # If ID exists, generate a new ID
                cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
                max_id = int(cursor.fetchone()[0])
                new_id = max_id + 1
                new_customer_id = f"CUST{new_id:06d}"
                
                cursor.execute(
                    "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
                    (new_customer_id, customer[1], customer[2], customer[3], customer[4])
                )
        
        conn.commit()
        
        progress.progress(95)
        
        # Verify database
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        progress.progress(100)
        status_text.text("")
        
        st.success(f"✅ Customer database created successfully with {total_count} records!")
        st.info("You can now use the Customer tab in the main application.")
        
    except Exception as e:
        st.error(f"Error creating customer database: {e}")

def reset_customer_database():
    """Reset (delete) the customer database"""
    # Database path
    db_path = 'data/customer_database.db'
    
    if not os.path.exists(db_path):
        st.warning("Customer database does not exist - nothing to reset")
        return
    
    try:
        os.remove(db_path)
        st.success("✅ Customer database has been reset")
        st.info("You can create a new database using the 'Create Customer Database' button")
    except Exception as e:
        st.error(f"Error resetting database: {e}")

def explore_customer_database():
    """Explore customer database contents"""
    # Database path
    db_path = 'data/customer_database.db'
    
    if not os.path.exists(db_path):
        st.warning("Customer database does not exist")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Get table list
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            st.warning("No tables found in the database")
            return
        
        # Let user select a table
        selected_table = st.selectbox("Select Table", tables)
        
        # Show table schema
        cursor.execute(f"PRAGMA table_info({selected_table})")
        schema = cursor.fetchall()
        
        st.subheader("Table Schema")
        schema_df = pd.DataFrame(schema, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])
        st.dataframe(schema_df[["name", "type", "notnull", "pk"]])
        
        # Show table data
        st.subheader("Table Data")
        limit = st.slider("Number of rows to display", 5, 100, 10)
        
        query = f"SELECT * FROM {selected_table} LIMIT {limit}"
        table_data = pd.read_sql_query(query, conn)
        
        st.dataframe(table_data)
        
        # Table statistics
        st.subheader("Table Statistics")
        
        cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
        row_count = cursor.fetchone()[0]
        
        st.metric("Total Rows", row_count)
        
        if selected_table == "customers":
            # Mobile type distribution
            cursor.execute("SELECT mobile_type, COUNT(*) FROM customers GROUP BY mobile_type")
            distribution = cursor.fetchall()
            
            dist_df = pd.DataFrame(distribution, columns=["Device Type", "Count"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Mobile Type Distribution")
                st.dataframe(dist_df)
            
            with col2:
                st.write("Distribution Chart")
                st.bar_chart(dist_df.set_index("Device Type"))
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error exploring database: {e}")

def explore_offers_database():
    """Explore offers database contents"""
    # Database path
    db_path = 'data/offers_database.db'
    
    if not os.path.exists(db_path):
        st.warning("Offers database does not exist")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Get table list
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            st.warning("No tables found in the database")
            return
        
        # Let user select a table
        selected_table = st.selectbox("Select Table", tables)
        
        # Show table schema
        cursor.execute(f"PRAGMA table_info({selected_table})")
        schema = cursor.fetchall()
        
        st.subheader("Table Schema")
        schema_df = pd.DataFrame(schema, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])
        st.dataframe(schema_df[["name", "type", "notnull", "pk"]])
        
        # Show table data
        st.subheader("Table Data")
        limit = st.slider("Number of rows to display", 5, 100, 10)
        
        query = f"SELECT * FROM {selected_table} LIMIT {limit}"
        table_data = pd.read_sql_query(query, conn)
        
        st.dataframe(table_data)
        
        # Table statistics
        st.subheader("Table Statistics")
        
        cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
        row_count = cursor.fetchone()[0]
        
        st.metric("Total Rows", row_count)
        
        if selected_table == "offers":
            # Type distribution
            cursor.execute("SELECT type, COUNT(*) FROM offers GROUP BY type")
            distribution = cursor.fetchall()
            
            if distribution:
                dist_df = pd.DataFrame(distribution, columns=["Offer Type", "Count"])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Offer Type Distribution")
                    st.dataframe(dist_df)
                
                with col2:
                    st.write("Distribution Chart")
                    st.bar_chart(dist_df.set_index("Offer Type"))
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error exploring database: {e}")

if __name__ == "__main__":
    st.set_page_config(page_title="Database Admin", layout="wide")
    admin_panel()
