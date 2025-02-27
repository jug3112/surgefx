import sqlite3
import pandas as pd
import random
import datetime
import uuid
from tqdm import tqdm

# Define constants for data generation
NUM_OFFERS = 10000  # Total number of offers to generate

# Define realistic data pools
MERCHANTS = {
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa", "Tata CLiQ", "Meesho", "Snapdeal", "Reliance Digital", "Croma"],
    "Food & Dining": ["Swiggy", "Zomato", "EatSure", "Domino's", "McDonald's", "Pizza Hut", "KFC", "Dunkin' Donuts", "Starbucks", "Burger King"],
    "Grocery": ["BigBasket", "Grofers", "JioMart", "Nature's Basket", "DMart", "Spencer's", "Reliance Fresh", "More", "Zepto", "BlinkIt"],
    "Travel": ["MakeMyTrip", "Goibibo", "Cleartrip", "EaseMyTrip", "Yatra", "IRCTC", "Booking.com", "Agoda", "Oyo", "Ixigo"],
    "Entertainment": ["BookMyShow", "PVR", "INOX", "Netflix", "Amazon Prime", "Disney+ Hotstar", "SonyLIV", "ZEE5", "Gaana", "Spotify"],
    "Electronics": ["Samsung", "Apple", "OnePlus", "Xiaomi", "Lenovo", "Dell", "HP", "Boat", "JBL", "Sony"],
    "Fashion": ["H&M", "ZARA", "Levi's", "Nike", "Adidas", "Puma", "Pantaloons", "Lifestyle", "Westside", "Fabindia"],
    "Beauty": ["Lakme", "MAC", "Forest Essentials", "Kama Ayurveda", "The Body Shop", "L'Oreal", "Maybelline", "Sugar", "Biotique", "Mamaearth"],
    "Home": ["IKEA", "Home Centre", "Urban Ladder", "Pepperfry", "Hometown", "Godrej Interio", "@home", "Nilkamal", "HomeTown", "Sleepwell"],
    "Pharmacy": ["Pharmeasy", "1mg", "Netmeds", "Apollo Pharmacy", "MedPlus", "Wellness Forever", "Practo", "Healthkart", "Tata 1mg", "Zeno Health"]
}

OFFER_TYPES = [
    "discount", "cashback", "buy_one_get_one", "reward_points", 
    "free_delivery", "flash_sale", "bundle_offer", "first_purchase", 
    "limited_time", "clearance_sale"
]

COUPON_PREFIXES = [
    "NEW", "WELCOME", "SAVE", "GET", "GRAB", "FLASH", "MEGA", "FEST", 
    "DEAL", "SALE", "HURRY", "EXTRA", "SUPER", "HAPPY", "SPECIAL", "WOW"
]

def generate_coupon_code():
    """Generate realistic coupon codes"""
    prefix = random.choice(COUPON_PREFIXES)
    if random.random() < 0.3:  # 30% chance of merchant-specific coupon
        merchant_word = random.choice(["SHOP", "APP", "FIRST", "NEW", "FRESH", "BIG"])
        number = random.randint(10, 50) * 5  # Values like 50, 100, 150, etc.
        return f"{prefix}{merchant_word}{number}"
    elif random.random() < 0.7:  # 40% chance of discount-indicating coupon
        if random.random() < 0.5:
            discount = random.choice([10, 15, 20, 25, 30, 40, 50])
            return f"{prefix}{discount}"
        else:
            discount = random.choice([10, 15, 20, 25, 30, 40, 50])
            return f"{prefix}{discount}OFF"
    else:  # 30% chance of season or event-based coupon
        season = random.choice(["SUMMER", "WINTER", "DIWALI", "HOLI", "FEST", "SALE", "SPECIAL"])
        year = random.choice([2023, 2024, 2025])
        return f"{season}{year}"

def generate_description(merchant, offer_type, discount_percent=None, discount_value=None, 
                        min_purchase=None, product_category=None):
    """Generate realistic offer descriptions based on parameters"""
    
    if offer_type == "discount":
        return f"Get {discount_percent}% off on {product_category} at {merchant}" + (f" on minimum purchase of ₹{min_purchase}" if min_purchase else "")
    
    elif offer_type == "cashback":
        if discount_value:
            return f"Get ₹{discount_value} cashback on your purchase at {merchant}" + (f" with minimum spend of ₹{min_purchase}" if min_purchase else "")
        else:
            return f"Get {discount_percent}% cashback on your purchase at {merchant}" + (f" with minimum spend of ₹{min_purchase}" if min_purchase else "")
    
    elif offer_type == "buy_one_get_one":
        return f"Buy 1 Get 1 Free on select {product_category} at {merchant}"
    
    elif offer_type == "reward_points":
        points = random.randint(2, 10)
        return f"Earn {points}X reward points on your {merchant} purchase"
    
    elif offer_type == "free_delivery":
        return f"Free delivery on all orders" + (f" above ₹{min_purchase}" if min_purchase else "") + f" at {merchant}"
    
    elif offer_type == "flash_sale":
        hours = random.randint(2, 12)
        return f"{hours} Hour Flash Sale! Up to {random.randint(30, 80)}% off on {product_category} at {merchant}"
    
    elif offer_type == "bundle_offer":
        return f"Special bundle offer on {product_category} at {merchant}. Buy more save more!"
    
    elif offer_type == "first_purchase":
        if discount_percent:
            return f"{discount_percent}% off on your first purchase at {merchant}" + (f" (Min. order: ₹{min_purchase})" if min_purchase else "")
        else:
            return f"₹{discount_value} off on your first purchase at {merchant}" + (f" (Min. order: ₹{min_purchase})" if min_purchase else "")
    
    elif offer_type == "limited_time":
        return f"Limited time offer! Save big on {product_category} at {merchant}"
    
    elif offer_type == "clearance_sale":
        return f"Clearance Sale! Up to {random.randint(40, 90)}% off on {product_category} at {merchant}"
    
    return f"Special offer at {merchant}"

def generate_terms_conditions(offer_type, min_purchase=None, valid_until=None):
    """Generate realistic terms and conditions"""
    terms = []
    
    # Common terms
    terms.append("Offer cannot be combined with any other offer or promotion.")
    
    if valid_until:
        terms.append(f"Valid until {valid_until.strftime('%d %b %Y')}.")
    
    if min_purchase:
        terms.append(f"Minimum purchase of ₹{min_purchase} required.")
    
    # Offer-specific terms
    if offer_type == "discount":
        terms.append("Discount applicable on selected items only.")
        if random.random() < 0.3:
            terms.append("Maximum discount of ₹2000 per order.")
    
    elif offer_type == "cashback":
        terms.append(f"Cashback will be credited within {random.randint(1, 7)} days of purchase.")
        terms.append(f"Maximum cashback of ₹{random.choice([500, 1000, 1500, 2000])} per transaction.")
    
    elif offer_type == "buy_one_get_one":
        terms.append("Offer valid on selected items only.")
        terms.append("Free item must be of equal or lesser value than the purchased item.")
    
    elif offer_type == "reward_points":
        terms.append(f"Points validity: {random.randint(30, 90)} days from date of credit.")
        terms.append("Points cannot be transferred or exchanged for cash.")
    
    elif offer_type == "free_delivery":
        terms.append("Valid for standard delivery only.")
        terms.append("Not applicable for express or same-day delivery.")
    
    # Add some randomized specific terms
    if random.random() < 0.3:
        terms.append("Not valid on already discounted items.")
    
    if random.random() < 0.2:
        terms.append("Limited to one use per customer.")
    
    if random.random() < 0.15:
        terms.append("Valid for online purchases only.")
    
    return "\n".join(terms)

def generate_affiliate_link(merchant, offer_id):
    """Generate dummy affiliate links"""
    merchant_slug = merchant.lower().replace(" ", "-").replace("'", "")
    return f"https://{merchant_slug}.affiliate.com/offers/{offer_id}"

def generate_dummy_data():
    """Generate a dataframe with dummy offer data"""
    print("Generating dummy offers data...")
    data = []
    
    today = datetime.datetime.now().date()
    
    for _ in tqdm(range(NUM_OFFERS)):
        # Select a random category and merchant
        category = random.choice(list(MERCHANTS.keys()))
        merchant = random.choice(MERCHANTS[category])
        
        # Generate random dates
        days_to_add = random.randint(-15, 90)  # Some offers started in the past, some in future
        valid_from = today + datetime.timedelta(days=max(-30, days_to_add - random.randint(5, 30)))
        valid_until = today + datetime.timedelta(days=days_to_add + random.randint(15, 120))
        
        # Generate offer ID
        offer_id = str(uuid.uuid4())[:8].upper()
        
        # Select offer type
        offer_type = random.choice(OFFER_TYPES)
        
        # Generate appropriate values based on offer type
        discount_percent = None
        discount_value = None
        min_purchase = None
        
        if offer_type in ["discount", "flash_sale", "clearance_sale"]:
            discount_percent = random.choice([10, 15, 20, 25, 30, 40, 50, 60, 70])
            if random.random() < 0.7:  # 70% chance of having minimum purchase
                min_purchase = random.choice([499, 999, 1499, 1999, 2499, 2999, 4999])
        
        elif offer_type == "cashback":
            if random.random() < 0.6:  # 60% chance of percentage cashback
                discount_percent = random.choice([5, 10, 15, 20, 25])
            else:  # 40% chance of fixed cashback
                discount_value = random.choice([50, 100, 150, 200, 250, 300, 500])
            min_purchase = random.choice([499, 999, 1499, 1999, 2499])
        
        elif offer_type in ["free_delivery", "first_purchase"]:
            if random.random() < 0.8:  # 80% chance of having minimum purchase
                min_purchase = random.choice([299, 499, 699, 999, 1499])
            if offer_type == "first_purchase":
                if random.random() < 0.5:
                    discount_percent = random.choice([10, 15, 20, 25, 30])
                else:
                    discount_value = random.choice([100, 150, 200, 250, 300])
        
        elif offer_type == "buy_one_get_one":
            # These typically don't have discount percent/value as they're special offers
            pass
        
        elif offer_type == "reward_points":
            # Usually these offer multipliers on standard points
            pass
        
        elif offer_type == "bundle_offer":
            if random.random() < 0.6:
                discount_percent = random.choice([5, 10, 15, 20, 25, 30])
            min_purchase = random.choice([999, 1499, 1999, 2499, 2999])
        
        # Generate coupon code (only some offers have codes)
        coupon_code = None
        if random.random() < 0.7:  # 70% chance of having a coupon code
            coupon_code = generate_coupon_code()
        
        # Generate description and terms
        description = generate_description(
            merchant, 
            offer_type, 
            discount_percent, 
            discount_value, 
            min_purchase, 
            category
        )
        
        terms_conditions = generate_terms_conditions(
            offer_type, 
            min_purchase, 
            valid_until
        )
        
        # Generate affiliate link
        affiliate_link = generate_affiliate_link(merchant, offer_id)
        
        # Create offer record
        offer = {
            "offer_id": f"{merchant[:3].upper()}{offer_id}",
            "merchant": merchant,
            "category": category,
            "type": offer_type,
            "discount_percent": discount_percent,
            "discount_value": discount_value,
            "minimum_purchase": min_purchase,
            "coupon_code": coupon_code,
            "description": description,
            "terms_conditions": terms_conditions,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "affiliate_link": affiliate_link
        }
        
        data.append(offer)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Successfully generated {len(df)} offers")
    return df

def create_database(df, db_path="offers_database.db"):
    """Create SQLite database and store the data"""
    print(f"Creating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # Create tables
    conn.execute('''
    CREATE TABLE IF NOT EXISTS offers (
        offer_id TEXT PRIMARY KEY,
        merchant TEXT,
        category TEXT,
        type TEXT,
        discount_percent REAL,
        discount_value REAL,
        minimum_purchase REAL,
        coupon_code TEXT,
        description TEXT,
        terms_conditions TEXT,
        valid_from TEXT,
        valid_until TEXT,
        affiliate_link TEXT
    )
    ''')
    
    # Insert data
    df.to_sql('offers', conn, if_exists='replace', index=False)
    
    # Create indices for faster filtering
    conn.execute('CREATE INDEX IF NOT EXISTS idx_merchant ON offers (merchant)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON offers (category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON offers (type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_valid_dates ON offers (valid_from, valid_until)')
    
    # Verify data
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM offers")
    count = cursor.fetchone()[0]
    print(f"Database created with {count} offers")
    
    # Sample query to verify data
    cursor.execute("""
    SELECT offer_id, merchant, type, coupon_code, valid_until 
    FROM offers 
    LIMIT 5
    """)
    sample = cursor.fetchall()
    print("\nSample data:")
    for row in sample:
        print(row)
    
    conn.close()
    print(f"Database successfully created at {db_path}")

def main():
    """Main function to generate data and create database"""
    try:
        # Generate dummy data
        df = generate_dummy_data()
        
        # Create database
        create_database(df)
        
        print("\nDummy database created successfully!")
        print("You can now run the dashboard app to visualize and filter this data.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
