import sqlite3

# Connect to the customer database
conn = sqlite3.connect('data/customer_database.db')
cursor = conn.cursor()

# Function to add a real customer
def add_real_customer(customer_name, mobile_number, email, mobile_type):
    # Generate a new customer_id based on current max ID
    cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
    max_id = cursor.fetchone()[0]
    if max_id is None:
        max_id = 0
    new_id = int(max_id) + 1
    customer_id = f"CUST{new_id:06d}"
    
    # Insert the new customer
    cursor.execute(
        "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
        (customer_id, customer_name, mobile_number, email, mobile_type)
    )
    conn.commit()
    return customer_id

# Sample real customers to add
real_customers = [
    ("John Smith", "+12025550123", "john.smith@example.com", "iOS"),
    ("Mary Johnson", "+16505551234", "mary.johnson@example.com", "Android"),
    ("Robert Davis", "+13125552345", "robert.davis@example.com", "iOS")
]

# Add each real customer
for customer in real_customers:
    try:
        customer_id = add_real_customer(*customer)
        print(f"Added real customer: {customer[0]} with ID: {customer_id}")
    except Exception as e:
        print(f"Error adding customer {customer[0]}: {e}")

# Close the connection
conn.close()

print("Real customers added successfully!")
