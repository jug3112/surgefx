import sqlite3
import pandas as pd
import random
import string
import os
from datetime import datetime

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

print("Creating customer database...")

# Connection to the database
conn = sqlite3.connect('data/customer_database.db')
cursor = conn.cursor()

# Create the customers table if it doesn't exist
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

# Check if data already exists
cursor.execute("SELECT COUNT(*) FROM customers")
count = cursor.fetchone()[0]

if count > 0:
    print(f"Database already contains {count} customer records.")
    print("Do you want to clear existing data and regenerate? (y/n)")
    response = input()
    if response.lower() == "y":
        cursor.execute("DELETE FROM customers")
        conn.commit()
        print("Existing data cleared.")
    else:
        print("Keeping existing data. Program will exit.")
        conn.close()
        exit()

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
print("Generating 1000 customer records...")
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

# Add 3 real customer examples
print("Adding 3 real customer examples...")
real_customers = [
    ("CUST001001", "John Smith", "+12025550123", "john.smith@example.com", "iOS"),
    ("CUST001002", "Mary Johnson", "+16505551234", "mary.johnson@example.com", "Android"),
    ("CUST001003", "Robert Davis", "+13125552345", "robert.davis@example.com", "iOS")
]

for customer in real_customers:
    try:
        cursor.execute(
            "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
            customer
        )
        print(f"Added real customer: {customer[1]}")
    except sqlite3.IntegrityError:
        # If the customer_id already exists, try with a different ID
        print(f"Customer ID {customer[0]} already exists. Trying with a new ID...")
        
        cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
        max_id = cursor.fetchone()[0]
        new_id = int(max_id) + 1
        new_customer_id = f"CUST{new_id:06d}"
        
        cursor.execute(
            "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
            (new_customer_id, customer[1], customer[2], customer[3], customer[4])
        )
        print(f"Added real customer: {customer[1]} with new ID: {new_customer_id}")
    except Exception as e:
        print(f"Error adding customer {customer[1]}: {e}")

conn.commit()

# Verify the data
cursor.execute("SELECT COUNT(*) FROM customers")
total_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM customers WHERE mobile_type = 'iOS'")
ios_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM customers WHERE mobile_type = 'Android'")
android_count = cursor.fetchone()[0]

print(f"Customer database created successfully with {total_count} total records.")
print(f"iOS Users: {ios_count}")
print(f"Android Users: {android_count}")

# Close the connection
conn.close()

print("Customer database generation complete!")
