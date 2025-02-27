import pandas as pd
import random
import datetime
import uuid
from faker import Faker
from tqdm import tqdm
import os

# Initialize Faker for generating realistic data
fake = Faker()

# Define constants
START_DATE = datetime.datetime.now() - datetime.timedelta(days=180)  # 6 months ago
END_DATE = datetime.datetime.now()
OUTPUT_FILE = 'customer_transaction_history.csv'

# MCC (Merchant Category Codes) with descriptions
MCC_CODES = {
    '5411': 'Grocery Stores',
    '5542': 'Gas Stations',
    '5812': 'Restaurants',
    '5814': 'Fast Food',
    '5912': 'Drug Stores',
    '5311': 'Department Stores',
    '5661': 'Shoe Stores',
    '5699': 'Clothing Stores',
    '7832': 'Movie Theaters',
    '5999': 'Miscellaneous Retail',
    '4111': 'Transportation',
    '7011': 'Hotels',
    '4121': 'Taxis/Rideshares',
    '5732': 'Electronics',
    '8011': 'Medical Services',
    '8021': 'Dental Services',
    '8099': 'Health Services',
    '8299': 'Educational Services',
    '4816': 'Online Services',
    '5945': 'Hobby/Toy Stores',
    '5094': 'Office Supplies',
    '5941': 'Sporting Goods',
    '7999': 'Recreation Services',
    '7230': 'Beauty/Barber Shops',
    '7512': 'Car Rentals',
    '4899': 'Cable/Internet Services',
    '6300': 'Insurance',
}

# Payment methods and card types
PAYMENT_METHODS = ['Credit', 'Debit']
CARD_TYPES = ['Visa', 'MasterCard', 'American Express', 'Discover']
TRANSACTION_TYPES = ['Sale', 'Refund']
TRANSACTION_STATUSES = ['Approved', 'Declined', 'Pending']
ENTRY_METHODS = ['Swiped', 'Chip', 'Contactless', 'Keyed', 'Online']
TRANSACTION_SOURCES = ['POS', 'Online', 'Mobile App', 'Recurring', 'Virtual Terminal']

def get_merchants():
    """Get a list of merchants (this would normally connect to your merchant database)"""
    merchants = [
        'Walmart', 'Target', 'Amazon', 'Costco', 'Kroger', 'Home Depot', 'Walgreens',
        'CVS', 'Lowe\'s', 'Best Buy', 'Apple', 'McDonald\'s', 'Starbucks', 'Subway',
        'Taco Bell', 'Shell', 'BP', 'Exxon', 'Chevron', 'Netflix', 'Spotify', 'Uber',
        'Lyft', 'Delta Airlines', 'American Airlines', 'Hilton', 'Marriott', 'Airbnb',
        'Planet Fitness', 'LA Fitness', '7-Eleven', 'AT&T', 'Verizon', 'T-Mobile',
        'Comcast', 'Charter', 'Dish Network', 'Xbox', 'PlayStation', 'Nintendo',
        'Whole Foods', 'Trader Joe\'s', 'Aldi', 'Safeway', 'Publix', 'Albertsons',
        'H&M', 'Zara', 'Gap', 'Nike', 'Adidas', 'Sephora', 'Ulta Beauty',
        'Home Goods', 'TJ Maxx', 'Ross', 'Kohl\'s', 'Macy\'s', 'Nordstrom',
        'Chipotle', 'Panera Bread', 'Olive Garden', 'Cheesecake Factory',
        'AMC Theaters', 'Regal Cinemas', 'Barnes & Noble', 'Office Depot',
        'Staples', 'IKEA', 'Wayfair', 'Etsy', 'eBay', 'Uber Eats', 'DoorDash',
        'Instacart', 'Grubhub', 'FedEx', 'UPS', 'USPS', 'Venmo', 'PayPal',
        'Cash App', 'Bank of America', 'Chase', 'Wells Fargo', 'Citibank'
    ]
    return merchants

def generate_card_data(customer_id):
    """Generate realistic credit card data for a customer"""
    card_type = random.choice(CARD_TYPES)
    
    # Generate card number based on card type
    if card_type == 'Visa':
        card_num = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
    elif card_type == 'MasterCard':
        card_num = '5' + str(random.randint(1, 5)) + ''.join([str(random.randint(0, 9)) for _ in range(14)])
    elif card_type == 'American Express':
        card_num = '3' + random.choice(['4', '7']) + ''.join([str(random.randint(0, 9)) for _ in range(13)])
    else:  # Discover
        card_num = '6' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
    
    # Mask the card number
    masked_card = card_num[0:4] + ' XXXX XXXX ' + card_num[-4:]
    
    # Generate expiration date (1-5 years in the future)
    exp_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(30, 1825))
    exp_date_str = exp_date.strftime("%m/%y")
    
    return card_type, masked_card, exp_date_str

def assign_mcc_to_merchant(merchant_name):
    """Assigns an appropriate MCC to a merchant based on name"""
    merchant_lower = merchant_name.lower()
    
    # Map keywords to MCC categories
    keyword_to_mcc = {
        'walmart': '5311', 'target': '5311', 'costco': '5311',  # Department stores
        'kroger': '5411', 'food': '5411', 'grocery': '5411', 'market': '5411',  # Grocery
        'shell': '5542', 'bp': '5542', 'exxon': '5542', 'chevron': '5542', 'gas': '5542',  # Gas
        'mcdonald': '5814', 'starbucks': '5814', 'subway': '5814', 'taco bell': '5814',  # Fast food
        'restaurant': '5812', 'grill': '5812', 'cafe': '5812', 'diner': '5812',  # Restaurants
        'walgreens': '5912', 'cvs': '5912', 'pharmacy': '5912',  # Drug stores
        'shoe': '5661',  # Shoe stores
        'cloth': '5699', 'apparel': '5699', 'fashion': '5699',  # Clothing
        'movie': '7832', 'cinema': '7832', 'theater': '7832',  # Movie theaters
        'best buy': '5732', 'apple': '5732', 'electronics': '5732',  # Electronics
        'doctor': '8011', 'clinic': '8011', 'hospital': '8011',  # Medical
        'dental': '8021', 'dentist': '8021',  # Dental
        'gym': '7999', 'fitness': '7999',  # Recreation
        'uber': '4121', 'lyft': '4121', 'taxi': '4121',  # Taxis/Rideshares
        'hotel': '7011', 'motel': '7011', 'hilton': '7011', 'marriott': '7011',  # Hotels
        'airline': '4111', 'flight': '4111', 'delta': '4111', 'american airlines': '4111',  # Transportation
        'netflix': '4816', 'spotify': '4816', 'online': '4816',  # Online services
        'toy': '5945', 'hobby': '5945',  # Hobby/Toy
        'sport': '5941', 'athletic': '5941',  # Sporting goods
        'salon': '7230', 'barber': '7230', 'beauty': '7230',  # Beauty
        'insurance': '6300',  # Insurance
        'internet': '4899', 'cable': '4899', 'at&t': '4899', 'verizon': '4899',  # Cable/Internet
    }
    
    # Check for keywords in merchant name
    for keyword, mcc in keyword_to_mcc.items():
        if keyword in merchant_lower:
            return mcc
    
    # Default to miscellaneous retail if no match
    return '5999'

def create_spending_profile():
    """Create a randomized spending profile for a customer"""
    # Weighted MCC preferences
    mcc_preference = {}
    
    # Pick 3-5 primary categories the customer frequently spends in
    primary_categories = random.sample(list(MCC_CODES.keys()), random.randint(3, 5))
    secondary_categories = random.sample([mcc for mcc in MCC_CODES.keys() if mcc not in primary_categories], 
                                         random.randint(5, 10))
    
    # Assign weights to categories
    for mcc in MCC_CODES:
        if mcc in primary_categories:
            mcc_preference[mcc] = random.uniform(0.1, 0.25)  # Primary categories get higher weight
        elif mcc in secondary_categories:
            mcc_preference[mcc] = random.uniform(0.01, 0.09)  # Secondary categories get medium weight
        else:
            mcc_preference[mcc] = random.uniform(0, 0.01)  # Rarely visited categories
    
    # Normalize weights to sum to 1
    total_weight = sum(mcc_preference.values())
    for mcc in mcc_preference:
        mcc_preference[mcc] /= total_weight
    
    # Day of week preferences (weekend vs weekday)
    weekday_weight = random.uniform(0.5, 0.7)
    weekend_weight = 1 - weekday_weight
    
    # Time of day preferences
    time_preferences = {
        'morning': random.uniform(0, 0.3),
        'afternoon': random.uniform(0.2, 0.5),
        'evening': random.uniform(0.2, 0.5),
        'night': random.uniform(0, 0.2)
    }
    total_time_weight = sum(time_preferences.values())
    for time_key in time_preferences:
        time_preferences[time_key] /= total_time_weight
    
    # Amount preferences
    amount_profile = {
        'min_amount': random.uniform(1, 10),
        'max_amount': random.uniform(500, 2000),
        'avg_amount': random.uniform(20, 100),
        'std_amount': random.uniform(10, 50)
    }
    
    # Create specific recurring transactions for this customer
    recurring_transactions = []
    if random.random() < 0.8:  # 80% chance of having recurring transactions
        num_recurring = random.randint(1, 5)
        for _ in range(num_recurring):
            merchant = random.choice([
                'Netflix', 'Spotify', 'Amazon Prime', 'Gym Membership', 'Internet Service',
                'Phone Bill', 'Insurance', 'Streaming Service', 'Subscription Box', 'Cloud Storage'
            ])
            amount = random.uniform(5, 100)
            day_of_month = random.randint(1, 28)
            mcc = assign_mcc_to_merchant(merchant)
            
            recurring_transactions.append({
                'merchant': merchant,
                'amount': amount,
                'day_of_month': day_of_month,
                'mcc': mcc
            })
    
    return {
        'mcc_preference': mcc_preference,
        'weekday_weight': weekday_weight,
        'weekend_weight': weekend_weight,
        'time_preferences': time_preferences,
        'amount_profile': amount_profile,
        'recurring_transactions': recurring_transactions
    }

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_diff = end_date - start_date
    random_days = random.randrange(time_diff.days)
    random_date = start_date + datetime.timedelta(days=random_days)
    return random_date

def generate_transaction_time(date, profile):
    """Generate a realistic transaction time based on customer profile and date"""
    is_weekend = date.weekday() >= 5  # Saturday or Sunday
    
    # Determine time period based on weighted preferences
    time_periods = list(profile['time_preferences'].keys())
    time_weights = list(profile['time_preferences'].values())
    
    # Adjust weights for weekends
    if is_weekend:
        # On weekends, people tend to be more active later in the day
        time_weights[0] *= 0.7  # morning
        time_weights[1] *= 1.2  # afternoon
        time_weights[2] *= 1.3  # evening
        time_weights[3] *= 1.5  # night
    
    # Normalize weights
    total = sum(time_weights)
    time_weights = [w/total for w in time_weights]
    
    # Choose time period
    time_period = random.choices(time_periods, weights=time_weights, k=1)[0]
    
    # Generate time within that period
    if time_period == 'morning':
        hour = random.randint(6, 11)
    elif time_period == 'afternoon':
        hour = random.randint(12, 16)
    elif time_period == 'evening':
        hour = random.randint(17, 20)
    else:  # night
        hour = random.randint(21, 23)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return datetime.time(hour, minute, second)

def select_merchant_and_mcc(profile, merchants):
    """Select a merchant and MCC based on customer spending profile"""
    # First decide on MCC based on customer preferences
    mcc_list = list(profile['mcc_preference'].keys())
    mcc_weights = list(profile['mcc_preference'].values())
    
    selected_mcc = random.choices(mcc_list, weights=mcc_weights, k=1)[0]
    
    # Next, choose a merchant that would fall under this MCC
    # For simplicity, we'll randomly select from our merchant list and assign the MCC
    merchant = random.choice(merchants)
    
    # Alternatively, we could map merchants to MCCs more intelligently
    # If the selected MCC is gas stations and we have gas station merchants, prefer those
    if selected_mcc == '5542' and any(m in ['Shell', 'BP', 'Exxon', 'Chevron'] for m in merchants):
        gas_merchants = [m for m in merchants if m in ['Shell', 'BP', 'Exxon', 'Chevron']]
        merchant = random.choice(gas_merchants)
    
    # If the selected MCC is grocery and we have grocery merchants, prefer those
    elif selected_mcc == '5411' and any(m in ['Kroger', 'Walmart', 'Target', 'Costco'] for m in merchants):
        grocery_merchants = [m for m in merchants if m in ['Kroger', 'Walmart', 'Target', 'Costco']]
        merchant = random.choice(grocery_merchants)
    
    # Re-assign MCC based on merchant name for better consistency
    actual_mcc = assign_mcc_to_merchant(merchant)
    
    return merchant, actual_mcc

def generate_transaction_amount(profile, mcc):
    """Generate a realistic transaction amount based on customer profile and MCC"""
    amount_profile = profile['amount_profile']
    
    # Base amount uses a normal distribution around customer's average
    base_amount = max(
        amount_profile['min_amount'],
        min(
            random.normalvariate(amount_profile['avg_amount'], amount_profile['std_amount']),
            amount_profile['max_amount']
        )
    )
    
    # Adjust based on MCC category
    mcc_amount_multipliers = {
        '5411': random.uniform(0.8, 1.5),    # Grocery - moderate
        '5542': random.uniform(0.5, 1.2),    # Gas - lower
        '5812': random.uniform(1.0, 2.0),    # Restaurants - higher
        '5814': random.uniform(0.3, 0.8),    # Fast Food - much lower
        '5912': random.uniform(0.6, 1.2),    # Drug Stores - moderate
        '5311': random.uniform(1.0, 3.0),    # Department Stores - higher
        '7011': random.uniform(2.0, 5.0),    # Hotels - much higher
        '5732': random.uniform(1.5, 4.0),    # Electronics - much higher
        '4111': random.uniform(1.5, 4.0),    # Transportation - higher
    }
    
    # Use general multiplier for MCCs not explicitly defined
    if mcc not in mcc_amount_multipliers:
        mcc_multiplier = random.uniform(0.7, 1.5)
    else:
        mcc_multiplier = mcc_amount_multipliers[mcc]
    
    # Apply multiplier
    adjusted_amount = base_amount * mcc_multiplier
    
    # Weekly patterns (paydays tend to have higher spending)
    day_of_week = datetime.datetime.now().weekday()
    if day_of_week == 4 or day_of_week == 5:  # Friday and Saturday
        adjusted_amount *= random.uniform(1.1, 1.4)  # Higher spending
    
    # Round to 2 decimal places
    final_amount = round(adjusted_amount, 2)
    
    return final_amount

def generate_recurring_transactions(customer_id, customer_name, profile, start_date, end_date, card_data):
    """Generate recurring transactions based on customer profile"""
    transactions = []
    
    for recurring in profile['recurring_transactions']:
        # Generate transaction for each month
        current_date = start_date
        
        # Move to the first occurrence
        while current_date.day > recurring['day_of_month']:
            current_date += datetime.timedelta(days=1)
            
        while current_date.day != recurring['day_of_month']:
            current_date += datetime.timedelta(days=1)
        
        # Generate recurring transactions until end date
        while current_date <= end_date:
            transaction = generate_transaction(
                customer_id, 
                customer_name,
                recurring['merchant'], 
                recurring['mcc'], 
                current_date, 
                generate_transaction_time(current_date, profile),
                recurring['amount'],
                card_data
            )
            transactions.append(transaction)
            
            # Move to next month (approximately)
            days_to_add = 28 if current_date.month == 2 else 30
            current_date += datetime.timedelta(days=days_to_add)
            
            # Adjust to correct day of month
            while current_date.day != recurring['day_of_month'] and current_date <= end_date:
                if current_date.day > recurring['day_of_month']:
                    # If we passed the target day, move to next month
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1, day=1)
                else:
                    # Otherwise, increment days
                    current_date += datetime.timedelta(days=1)
                
                # Stop if we've exceeded the end date
                if current_date > end_date:
                    break
    
    return transactions

def generate_transaction(customer_id, customer_name, merchant, mcc, date, time, amount, card_data):
    """Generate a single transaction with all required fields"""
    card_type, card_number, expiration_date = card_data
    
    # Determine probability of different transaction types
    if random.random() < 0.05:  # 5% chance of refund
        transaction_type = 'Refund'
    else:
        transaction_type = 'Sale'
    
    # Determine status (mostly approved)
    if random.random() < 0.03:  # 3% chance of declined
        transaction_status = 'Declined'
    elif random.random() < 0.01:  # 1% chance of pending
        transaction_status = 'Pending'
    else:
        transaction_status = 'Approved'
    
    # Generate consistent settlement and accounting dates
    if transaction_status == 'Approved':
        settlement_date = date + datetime.timedelta(days=random.randint(1, 3))
        settlement_status = 'Settled'
    elif transaction_status == 'Pending':
        settlement_date = date + datetime.timedelta(days=random.randint(3, 7))
        settlement_status = 'Pending'
    else:  # Declined
        settlement_date = None
        settlement_status = 'N/A'
    
    # Format dates as strings
    date_str = date.strftime("%Y-%m-%d")
    time_str = time.strftime("%H:%M:%S")
    settlement_date_str = settlement_date.strftime("%Y-%m-%d") if settlement_date else None
    accounting_date_str = settlement_date.strftime("%Y-%m-%d") if settlement_date else None
    
    # Generate fees and net amount
    fees = round(amount * random.uniform(0.015, 0.035), 2)  # 1.5% to 3.5% fee
    net_amount = round(amount - fees, 2)
    
    # Create the transaction
    transaction = {
        'transaction_id': str(uuid.uuid4()),
        'customer_id': customer_id,
        'transaction_date': date_str,
        'transaction_time': time_str,
        'settlement_date': settlement_date_str,
        'card_type': card_type,
        'payment_method': 'Credit' if card_type in ['Visa', 'MasterCard', 'American Express', 'Discover'] else 'Debit',
        'transaction_type': transaction_type,
        'transaction_status': transaction_status,
        'authorization_code': ''.join(random.choices('0123456789ABCDEF', k=6)),
        'merchant_category_code': mcc,
        'transaction_amount': amount if transaction_type == 'Sale' else -amount,
        'currency': 'USD',
        'fees': fees if transaction_status == 'Approved' else 0,
        'net_amount': net_amount if transaction_status == 'Approved' else 0,
        'batch_id': f"BATCH{random.randint(100000, 999999)}",
        'card_number': card_number,
        'expiration_date': expiration_date,
        'cardholder_name': customer_name,
        'merchant_id': f"M{random.randint(10000, 99999)}",
        'merchant_name': merchant,
        'terminal_id': f"T{random.randint(1000, 9999)}",
        'user_account': f"UA{random.randint(10000, 99999)}",
        'customer_name': customer_name,
        'billing_address': fake.street_address(),
        'zip_code': fake.zipcode(),
        'invoice_number': f"INV{random.randint(100000, 999999)}",
        'order_id': f"ORD{random.randint(100000, 999999)}",
        'transaction_source': random.choice(TRANSACTION_SOURCES),
        'entry_method': random.choice(ENTRY_METHODS),
        'settlement_status': settlement_status,
        'settlement_batch_number': f"SB{random.randint(100000, 999999)}" if settlement_date else None,
        'processor_name': random.choice(['FirstData', 'Square', 'Stripe', 'PayPal', 'Adyen']),
        'accounting_date': accounting_date_str,
        'revenue_account': f"RA{random.randint(1000, 9999)}",
        'account_set': random.choice(['Default', 'Premium', 'Business', None]),
        'comments': random.choice([None, 'Customer satisfaction guaranteed', 'Loyalty program', 'Special order']),
        'special_instructions': None,
        'transaction_flexfield': None
    }
    
    return transaction

def generate_customer_transactions(customer_id, customer_name, merchants, start_date, end_date):
    """Generate 6 months of transactions for a single customer"""
    # Create spending profile for this customer
    profile = create_spending_profile()
    
    # Generate credit card data
    card_data = generate_card_data(customer_id)
    
    # Calculate the number of days in the date range
    days = (end_date - start_date).days + 1
    
    # List to store all transactions
    all_transactions = []
    
    # Generate recurring transactions first
    recurring_transactions = generate_recurring_transactions(
        customer_id, customer_name, profile, start_date, end_date, card_data
    )
    all_transactions.extend(recurring_transactions)
    
    # Generate 1-5 random transactions per day
    for day_offset in range(days):
        current_date = start_date + datetime.timedelta(days=day_offset)
        
        # Determine if transactions happen on this day
        is_weekend = current_date.weekday() >= 5
        
        # Weekend probability based on profile
        if is_weekend:
            transaction_probability = profile['weekend_weight']
        else:
            transaction_probability = profile['weekday_weight']
        
        # Skip days with no transactions
        if random.random() > transaction_probability * 0.8:
            continue
        
        # Determine number of transactions for this day (1-5)
        num_transactions = random.randint(1, 5)
        
        # Generate each transaction
        for _ in range(num_transactions):
            # Select merchant and MCC
            merchant, mcc = select_merchant_and_mcc(profile, merchants)
            
            # Generate transaction time
            transaction_time = generate_transaction_time(current_date, profile)
            
            # Generate transaction amount
            amount = generate_transaction_amount(profile, mcc)
            
            # Create transaction
            transaction = generate_transaction(
                customer_id, customer_name, merchant, mcc, current_date, transaction_time, amount, card_data
            )
            
            all_transactions.append(transaction)
    
    return all_transactions

def generate_customer_names():
    """Generate a list of customer names"""
    customer_names = {}
    for i in range(1, 1004):
        customer_id = f"CUST{i:06d}"
        customer_names[customer_id] = fake.name()
    return customer_names

def main():
    print("Generating transaction history for customers...")
    
    # Get merchants
    merchants = get_merchants()
    print(f"Using {len(merchants)} merchants for transaction generation.")
    
    # Generate customer names
    customer_names = generate_customer_names()
    print(f"Generating transactions for {len(customer_names)} customers.")
    
    # Generate transactions for each customer
    all_transactions = []
    
    # Process customers with progress bar
    for customer_id, customer_name in tqdm(customer_names.items(), desc="Generating customer transactions"):
        # Generate transactions for this customer
        customer_transactions = generate_customer_transactions(
            customer_id, customer_name, merchants, START_DATE, END_DATE
        )
        
        all_transactions.extend(customer_transactions)
    
    # Convert to DataFrame
    transactions_df = pd.DataFrame(all_transactions)
    
    # Save to CSV
    transactions_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nTransaction generation complete!")
    print(f"Total transactions generated: {len(transactions_df):,}")
    print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
