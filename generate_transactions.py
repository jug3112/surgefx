import pandas as pd
import random
import datetime
import uuid
from faker import Faker
import csv

# Initialize faker
fake = Faker()

# Constants
NUM_CUSTOMERS = 1003  # Customers from CUST000001 to CUST001003
START_DATE = datetime.datetime.now() - datetime.timedelta(days=180)  # 6 months ago
END_DATE = datetime.datetime.now()
OUTPUT_FILE = 'customer_transactions.csv'

# MCC Codes
MCC_CODES = {
    '5411': 'Grocery Stores',
    '5542': 'Gas Stations',
    '5812': 'Restaurants',
    '5814': 'Fast Food',
    '5912': 'Drug Stores',
    '5311': 'Department Stores',
    '5699': 'Clothing Stores',
    '7832': 'Movie Theaters',
    '5732': 'Electronics',
    '4899': 'Cable/Internet Services',
}

# Merchants
MERCHANTS = {
    '5411': ['Kroger', 'Walmart', 'Safeway', 'Whole Foods', 'Aldi'],
    '5542': ['Shell', 'Exxon', 'BP', 'Chevron', 'Marathon'],
    '5812': ['Olive Garden', 'Chili\'s', 'Applebee\'s', 'Outback', 'Cheesecake Factory'],
    '5814': ['McDonald\'s', 'Burger King', 'Subway', 'Taco Bell', 'Starbucks'],
    '5912': ['CVS', 'Walgreens', 'Rite Aid', 'Duane Reade'],
    '5311': ['Target', 'Macy\'s', 'Kohl\'s', 'JCPenney', 'Nordstrom'],
    '5699': ['H&M', 'Zara', 'Gap', 'Old Navy', 'Nike'],
    '7832': ['AMC Theaters', 'Regal Cinemas', 'Cinemark', 'IMAX'],
    '5732': ['Best Buy', 'Apple Store', 'GameStop', 'Microsoft Store'],
    '4899': ['Comcast', 'AT&T', 'Verizon', 'T-Mobile', 'Dish Network'],
}

# Card types
CARD_TYPES = ['Visa', 'MasterCard', 'American Express', 'Discover']

def generate_customer_name(customer_id):
    # Generate consistent name based on customer ID
    random.seed(int(customer_id.replace('CUST', '')))
    return fake.name()

def generate_transactions():
    transactions = []
    customer_count = 0
    transaction_count = 0
    
    # For each customer
    for i in range(1, NUM_CUSTOMERS + 1):
        customer_id = f"CUST{i:06d}"
        customer_name = generate_customer_name(customer_id)
        customer_count += 1
        
        # Assign a card type
        card_type = random.choice(CARD_TYPES)
        
        # Generate masked card number
        if card_type == 'Visa':
            card_number = f"4{''.join([str(random.randint(0, 9)) for _ in range(3)])} XXXX XXXX {''.join([str(random.randint(0, 9)) for _ in range(4)])}"
        elif card_type == 'MasterCard':
            card_number = f"5{''.join([str(random.randint(0, 9)) for _ in range(3)])} XXXX XXXX {''.join([str(random.randint(0, 9)) for _ in range(4)])}"
        elif card_type == 'American Express':
            card_number = f"3{''.join([str(random.randint(0, 9)) for _ in range(3)])} XXXX XXXX {''.join([str(random.randint(0, 9)) for _ in range(3)])}"
        else:  # Discover
            card_number = f"6{''.join([str(random.randint(0, 9)) for _ in range(3)])} XXXX XXXX {''.join([str(random.randint(0, 9)) for _ in range(4)])}"
        
        # Create favorite categories for this customer (3-5 categories)
        favorite_categories = random.sample(list(MCC_CODES.keys()), random.randint(3, 5))
        
        # Generate 1-5 transactions per day with higher probability for favorite categories
        days = (END_DATE - START_DATE).days
        for day in range(days):
            # Not every day has transactions
            if random.random() > 0.3:  # 30% chance of transactions on any given day
                continue
                
            current_date = START_DATE + datetime.timedelta(days=day)
            
            # Generate 1-5 transactions per day
            num_transactions = random.randint(1, 5)
            for _ in range(num_transactions):
                # Select category with preference for favorites
                if random.random() < 0.7:  # 70% chance of using a favorite category
                    category = random.choice(favorite_categories)
                else:
                    category = random.choice(list(MCC_CODES.keys()))
                
                # Select merchant
                merchant = random.choice(MERCHANTS[category])
                
                # Generate amount based on category
                if category in ['5411', '5311']:  # Grocery, Department Stores
                    amount = round(random.uniform(15, 200), 2)
                elif category == '5542':  # Gas
                    amount = round(random.uniform(20, 60), 2)
                elif category in ['5812']:  # Restaurants
                    amount = round(random.uniform(25, 150), 2)
                elif category in ['5814']:  # Fast Food
                    amount = round(random.uniform(5, 30), 2)
                elif category in ['7832']:  # Movies
                    amount = round(random.uniform(10, 50), 2)
                elif category in ['5732']:  # Electronics
                    amount = round(random.uniform(50, 1000), 2)
                elif category in ['4899']:  # Cable/Internet
                    amount = round(random.uniform(50, 200), 2)
                else:
                    amount = round(random.uniform(10, 100), 2)
                
                # Generate transaction time
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                transaction_time = f"{hour:02d}:{minute:02d}:{second:02d}"
                
                # Generate transaction ID
                transaction_id = str(uuid.uuid4())
                
                # Create transaction record
                transaction = {
                    'transaction_id': transaction_id,
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'transaction_date': current_date.strftime("%Y-%m-%d"),
                    'transaction_time': transaction_time,
                    'merchant_name': merchant,
                    'merchant_category_code': category,
                    'transaction_amount': amount,
                    'card_type': card_type,
                    'card_number': card_number,
                    'transaction_type': 'Sale',
                    'transaction_status': 'Approved'
                }
                
                transactions.append(transaction)
                transaction_count += 1
    
    print(f"Generated {transaction_count} transactions for {customer_count} customers")
    return transactions

def save_to_csv(transactions, filename):
    with open(filename, 'w', newline='') as csvfile:
        if not transactions:
            print("No transactions to save")
            return
            
        fieldnames = transactions[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"Saved {len(transactions)} transactions to {filename}")

def main():
    print("Generating transaction history...")
    transactions = generate_transactions()
    save_to_csv(transactions, OUTPUT_FILE)
    print("Done!")

if __name__ == "__main__":
    main()
