
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import requests
from tqdm import tqdm
import os
# Import customers module if it exists
try:
    import customers
    customers_module_available = True
except ImportError:
    customers_module_available = False

# Import transaction analysis
try:
    from transactions_analysis import show_transactions_tab
except ImportError:
    show_transactions_tab = None

# Set page configuration
st.set_page_config(
    page_title="Merchant Offers Dashboard",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Add this function to your app.py file near the beginning

def ensure_database_exists():
    """Ensure the database exists, creating it if necessary"""
    if not os.path.exists("offers_database.db"):
        st.info("Database not found. Generating dummy database...")
        
        # Import functions from the generator script
        try:
            # Option 1: Import directly from the file
            from generate_dummy_data import generate_dummy_data, create_database
            
            # Generate and save data
            with st.spinner("Generating 10,000 dummy offers..."):
                df = generate_dummy_data()
                create_database(df)
                st.success("Database created successfully!")
        except ImportError:
            # Option 2: Generate data inline if import fails
            st.warning("Could not import from generate_dummy_data.py. Generating data inline...")
            
            # Define a simplified version of the data generator
            def quick_generate_dummy_data():
                """Generate a smaller set of dummy data"""
                import pandas as pd
                import random
                import datetime
                import uuid
                
                data = []
                merchants = [
                    "Amazon", "Flipkart", "Swiggy", "Zomato", "BigBasket", 
                    "MakeMyTrip", "BookMyShow", "Myntra", "Ajio", "Nykaa"
                ]
                categories = ["Shopping", "Food", "Travel", "Fashion", "Grocery"]
                offer_types = ["discount", "cashback", "buy_one_get_one", "free_delivery"]
                
                # Generate 1,000 offers for quick testing
                for _ in range(1000):
                    merchant = random.choice(merchants)
                    category = random.choice(categories)
                    offer_type = random.choice(offer_types)
                    
                    offer = {
                        "offer_id": f"{merchant[:3].upper()}{str(uuid.uuid4())[:8].upper()}",
                        "merchant": merchant,
                        "category": category,
                        "type": offer_type,
                        "discount_percent": random.choice([10, 15, 20, 25, 30, 40, 50]) if random.random() < 0.7 else None,
                        "discount_value": random.choice([50, 100, 150, 200, 300]) if random.random() < 0.3 else None,
                        "minimum_purchase": random.choice([499, 999, 1499, 1999]) if random.random() < 0.6 else None,
                        "coupon_code": f"SAVE{random.choice([10, 20, 30])}" if random.random() < 0.7 else None,
                        "description": f"Special offer at {merchant}",
                        "terms_conditions": "Terms and conditions apply",
                        "valid_from": (datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))).date(),
                        "valid_until": (datetime.datetime.now() + datetime.timedelta(days=random.randint(15, 90))).date(),
                        "affiliate_link": f"https://{merchant.lower().replace(' ', '-')}.affiliate.com/offers/{random.randint(1000, 9999)}"
                    }
                    data.append(offer)
                
                return pd.DataFrame(data)
            
            # Create database with simplified data
            conn = sqlite3.connect("offers_database.db")
            df = quick_generate_dummy_data()
            df.to_sql('offers', conn, if_exists='replace', index=False)
            
            # Create indices
            conn.execute('CREATE INDEX IF NOT EXISTS idx_merchant ON offers (merchant)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON offers (category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON offers (type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_valid_dates ON offers (valid_from, valid_until)')
            
            conn.close()
            st.success("Database created with 1,000 sample offers!")

# Database connection helper
def get_db_connection(db_path="offers_database.db"):
    """Create a database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(_conn, filters=None):
    """Load data from database with optional filters"""
    query = "SELECT * FROM offers"
    params = []
    
    if filters:
        conditions = []
        
        # Apply merchant filter
        if filters.get('merchant') and filters['merchant'] != 'All':
            conditions.append("merchant = ?")
            params.append(filters['merchant'])
        
        # Apply category filter
        if filters.get('category') and filters['category'] != 'All':
            conditions.append("category = ?")
            params.append(filters['category'])
        
        # Apply offer type filter
        if filters.get('offer_type') and filters['offer_type'] != 'All':
            conditions.append("type = ?")
            params.append(filters['offer_type'])
        
        # Apply min discount filter
        if filters.get('min_discount'):
            conditions.append("(discount_percent >= ? OR discount_value >= ?)")
            params.extend([filters['min_discount'], filters['min_discount'] * 10])  # Approximate conversion
        
        # Apply date filter
        if filters.get('valid_on_date'):
            conditions.append("date(valid_from) <= date(?) AND date(valid_until) >= date(?)")
            params.extend([filters['valid_on_date'], filters['valid_on_date']])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    # Execute query
    df = pd.read_sql_query(query, _conn, params=params)
    return df

@st.cache_data
def get_filter_options(_conn):
    """Get unique values for filters"""
    merchants = pd.read_sql_query("SELECT DISTINCT merchant FROM offers ORDER BY merchant", _conn)['merchant'].tolist()
    categories = pd.read_sql_query("SELECT DISTINCT category FROM offers ORDER BY category", _conn)['category'].tolist()
    offer_types = pd.read_sql_query("SELECT DISTINCT type FROM offers ORDER BY type", _conn)['type'].tolist()
    
    return {
        'merchants': ['All'] + merchants,
        'categories': ['All'] + categories,
        'offer_types': ['All'] + offer_types
    }

# Visualization functions
def create_offers_by_merchant_chart(data):
    """Create a bar chart of offers by merchant"""
    merchant_counts = data['merchant'].value_counts().reset_index()
    merchant_counts.columns = ['merchant', 'count']
    merchant_counts = merchant_counts.sort_values('count', ascending=False).head(15)
    
    fig = px.bar(
        merchant_counts,
        x='merchant',
        y='count',
        title='Number of Offers by Merchant (Top 15)',
        labels={'merchant': 'Merchant', 'count': 'Number of Offers'},
        color='count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500
    )
    
    return fig

def create_offers_by_type_chart(data):
    """Create a pie chart of offers by type"""
    type_counts = data['type'].value_counts().reset_index()
    type_counts.columns = ['type', 'count']
    
    fig = px.pie(
        type_counts,
        values='count',
        names='type',
        title='Distribution of Offer Types',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_offers_by_category_chart(data):
    """Create a bar chart of offers by category"""
    category_counts = data['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    category_counts = category_counts.sort_values('count', ascending=False)
    
    fig = px.bar(
        category_counts,
        x='category',
        y='count',
        title='Offers by Category',
        labels={'category': 'Category', 'count': 'Number of Offers'},
        color='category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
        height=400
    )
    
    return fig

def create_discount_distribution_chart(data):
    """Create a histogram of discount percentages"""
    # Filter out None values
    discount_data = data[data['discount_percent'].notna()]
    
    if len(discount_data) > 0:
        fig = px.histogram(
            discount_data,
            x='discount_percent',
            nbins=20,
            title='Distribution of Discount Percentages',
            labels={'discount_percent': 'Discount Percentage', 'count': 'Number of Offers'},
            color_discrete_sequence=['#3366CC']
        )
        
        fig.update_layout(bargap=0.1, height=400)
        return fig
    else:
        # Create empty chart if no data
        fig = go.Figure()
        fig.add_annotation(
            text="No discount percentage data available for the current selection",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(height=400)
        return fig

def create_offers_timeline_chart(data):
    """Create a timeline of offers"""
    # Convert strings to datetime
    data['valid_from'] = pd.to_datetime(data['valid_from'])
    data['valid_until'] = pd.to_datetime(data['valid_until'])
    
    # Group by date and count
    timeline_data = (
        pd.DataFrame({
            'date': pd.date_range(
                start=data['valid_from'].min(),
                end=data['valid_until'].max(),
                freq='D'
            )
        })
    )
    
    # Count active offers for each date
    timeline_data['active_offers'] = timeline_data['date'].apply(
        lambda date: sum(
            (data['valid_from'] <= date) & 
            (data['valid_until'] >= date)
        )
    )
    
    # Create timeline chart
    fig = px.line(
        timeline_data,
        x='date',
        y='active_offers',
        title='Number of Active Offers Over Time',
        labels={'date': 'Date', 'active_offers': 'Active Offers'},
        line_shape='spline'
    )
    
    fig.update_layout(height=450)
    return fig

# API Integration Functions
def fetch_offers_from_api(api_key):
    """Fetch offers from Coupomated API"""
    url = "https://api.coupomated.com/coupons"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        with st.spinner("Fetching offers from API..."):
            response = requests.get(url, headers=headers)
            
            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return []
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def normalize_api_data(api_response):
    """Normalize API response to match our database schema"""
    normalized_data = []
    
    try:
        # Handle different possible API response structures
        if isinstance(api_response, list):
            offers = api_response
        elif isinstance(api_response, dict) and 'offers' in api_response:
            offers = api_response['offers']
        elif isinstance(api_response, dict) and 'data' in api_response:
            offers = api_response['data']
        else:
            offers = [api_response]  # Single offer
        
        for offer in offers:
            # Map API fields to our schema
            normalized_offer = {
                "offer_id": offer.get('offer_id') or offer.get('id') or f"API_{len(normalized_data)}",
                "merchant": offer.get('merchant') or offer.get('store_name') or "Unknown",
                "category": offer.get('category') or "Uncategorized",
                "type": offer.get('type') or offer.get('offer_type') or "discount",
                "discount_percent": offer.get('discount_percent'),
                "discount_value": offer.get('discount_value') or offer.get('amount'),
                "minimum_purchase": offer.get('minimum_purchase') or offer.get('min_purchase'),
                "coupon_code": offer.get('coupon_code') or offer.get('code'),
                "description": offer.get('description') or offer.get('title') or "No description available",
                "terms_conditions": offer.get('terms_conditions') or offer.get('terms') or "Terms and conditions apply",
                "valid_from": offer.get('valid_from') or offer.get('start_date') or datetime.now().date().isoformat(),
                "valid_until": offer.get('valid_until') or offer.get('end_date') or (datetime.now() + timedelta(days=30)).date().isoformat(),
                "affiliate_link": offer.get('affiliate_link') or offer.get('link') or ""
            }
            normalized_data.append(normalized_offer)
        
        return normalized_data
    except Exception as e:
        st.error(f"Error normalizing API data: {e}")
        return []

def save_api_data_to_db(offers, db_path="offers_database.db"):
    """Save API data to database"""
    if not offers:
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.DataFrame(offers)
        
        # Convert date strings to proper format if needed
        for date_col in ['valid_from', 'valid_until']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col]).dt.date
        
        # Insert data
        df.to_sql('offers', conn, if_exists='replace', index=False)
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_merchant ON offers (merchant)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON offers (category)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON offers (type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_valid_dates ON offers (valid_from, valid_until)')
        
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving API data to database: {e}")
        return False

# Main Application
def main():
    # Ensure database exists
    ensure_database_exists()
    # App title with company logo/icon
    st.title("🏷️ Merchant Offers Dashboard")
    st.markdown("### Real-time Database for Merchant Offers & Promotions")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Database mode selection
        data_source = st.radio(
            "Data Source",
            ["Dummy Data", "API Data"],
            index=0
        )
        
        if data_source == "API Data":
            st.info("Connect to the Coupomated API for real offer data")
            api_key = st.text_input("API Key", type="password")
            
            if st.button("Fetch Offers from API"):
                if not api_key:
                    st.error("Please enter your API key")
                else:
                    api_data = fetch_offers_from_api(api_key)
                    
                    if api_data:
                        st.success(f"Successfully fetched data from API")
                        
                        # Normalize API data
                        normalized_data = normalize_api_data(api_data)
                        
                        if normalized_data:
                            # Save to database
                            if save_api_data_to_db(normalized_data):
                                st.success(f"Successfully saved {len(normalized_data)} offers to database")
                                st.rerun()  # Refresh app to show new data
        
        # Debug mode toggle
        debug_mode = st.checkbox("Debug Mode", value=False)
        
        if debug_mode and data_source == "API Data":
            st.subheader("API Debugging")
            if st.button("Test API Connection"):
                if not api_key:
                    st.error("Please enter your API key")
                else:
                    try:
                        response = requests.get(
                            "https://api.coupomated.com/coupons", 
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        st.write("Status Code:", response.status_code)
                        st.write("Response Headers:", response.headers)
                        st.json(response.json())
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Generate dummy data option
        if data_source == "Dummy Data" and (not os.path.exists("offers_database.db") or debug_mode):
            if st.button("Generate Dummy Database", help="Create a new database with 10,000 dummy offers"):
                try:
                    # Import the generator module
                    import sys
                    sys.path.append(".")
                    
                    with st.spinner("Generating dummy database with 10,000 offers..."):
                        # Execute the data generator script inline
                        from generate_dummy_data import generate_dummy_data, create_database
                        df = generate_dummy_data()
                        create_database(df)
                        st.success("Successfully generated dummy database!")
                        st.rerun()  # Refresh the app
                except Exception as e:
                    st.error(f"Error generating dummy data: {e}")
                    st.error("Make sure generate_dummy_data.py is in the same directory")
        
        # Separator
        st.markdown("---")
        
        # Filters section
        st.subheader("Filters")
        
        # Connect to database
        try:
            conn = get_db_connection()
            filter_options = get_filter_options(conn)
            
            # Create filters
            selected_merchant = st.selectbox("Merchant", filter_options['merchants'])
            selected_category = st.selectbox("Category", filter_options['categories'])
            selected_offer_type = st.selectbox("Offer Type", filter_options['offer_types'])
            min_discount = st.slider("Minimum Discount %", 0, 100, 0)
            valid_on_date = st.date_input(
                "Offers Valid On", 
                datetime.now().date(),
                min_value=datetime.now().date() - timedelta(days=30),
                max_value=datetime.now().date() + timedelta(days=180)
            )
            
            # Create filter dictionary
            filters = {
                'merchant': selected_merchant,
                'category': selected_category,
                'offer_type': selected_offer_type,
                'min_discount': min_discount,
                'valid_on_date': valid_on_date.isoformat() if valid_on_date else None
            }
            
            # Load data with filters
            df = load_data(conn, filters)
            
            # Close connection
            conn.close()
            
        except Exception as e:
            st.error(f"Database error: {e}")
            st.info("Please generate the dummy database first by clicking the button above.")
            return
    
    # Display data stats
    st.markdown(f"### Found {len(df)} offers matching your criteria")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📋 Data Explorer", "📈 Analytics", "👥 Customers", "💳 Transactions"])
    
    # Tab 1: Dashboard
    with tab1:
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Offers", 
                value=len(df),
                delta=None
            )
        
        with col2:
            merchant_count = df['merchant'].nunique()
            st.metric(
                label="Unique Merchants", 
                value=merchant_count,
                delta=None
            )
        
        with col3:
            avg_discount = df['discount_percent'].mean()
            st.metric(
                label="Avg. Discount", 
                value=f"{avg_discount:.1f}%" if not pd.isna(avg_discount) else "N/A",
                delta=None
            )
        
        with col4:
            # Calculate offers expiring soon (within 7 days)
            df['valid_until'] = pd.to_datetime(df['valid_until'])
            expiring_soon = sum(
                (df['valid_until'] >= datetime.now()) & 
                (df['valid_until'] <= datetime.now() + timedelta(days=7))
            )
            st.metric(
                label="Expiring Soon", 
                value=expiring_soon,
                delta=None
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Offers by merchant chart
            st.plotly_chart(create_offers_by_merchant_chart(df), use_container_width=True)
            
            # Offers by category chart
            st.plotly_chart(create_offers_by_category_chart(df), use_container_width=True)
        
        with col2:
            # Offers by type chart
            st.plotly_chart(create_offers_by_type_chart(df), use_container_width=True)
            
            # Discount distribution chart
            st.plotly_chart(create_discount_distribution_chart(df), use_container_width=True)
        
        # Full width charts
        st.plotly_chart(create_offers_timeline_chart(df), use_container_width=True)
    
    # Tab 2: Data Explorer
    with tab2:
        # Display data table with pagination
        st.dataframe(
            df.style.highlight_max(subset=['discount_percent'], color='lightgreen')
              .highlight_min(subset=['discount_percent'], color='#ffcccc'),
            height=600
        )
        
        # Export functionality
        st.download_button(
            label="Download Data as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="merchant_offers_export.csv",
            mime="text/csv"
        )
        
        # Offer details section
        st.subheader("Offer Details")
        selected_offer_id = st.selectbox("Select an offer to view details", df['offer_id'].tolist())
        
        if selected_offer_id:
            offer_details = df[df['offer_id'] == selected_offer_id].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Merchant:** {offer_details['merchant']}")
                st.markdown(f"**Category:** {offer_details['category']}")
                st.markdown(f"**Offer Type:** {offer_details['type']}")
                
                if not pd.isna(offer_details['discount_percent']):
                    st.markdown(f"**Discount:** {offer_details['discount_percent']}%")
                elif not pd.isna(offer_details['discount_value']):
                    st.markdown(f"**Discount Value:** ₹{offer_details['discount_value']}")
                
                if not pd.isna(offer_details['minimum_purchase']):
                    st.markdown(f"**Minimum Purchase:** ₹{offer_details['minimum_purchase']}")
                
                if not pd.isna(offer_details['coupon_code']):
                    st.code(offer_details['coupon_code'], language="")
            
            with col2:
                st.markdown(f"**Valid From:** {offer_details['valid_from']}")
                st.markdown(f"**Valid Until:** {offer_details['valid_until']}")
                
                if not pd.isna(offer_details['affiliate_link']):
                    st.markdown(f"**Affiliate Link:** {offer_details['affiliate_link']}")
            
            st.markdown("### Description")
            st.markdown(offer_details['description'])
            
            st.markdown("### Terms and Conditions")
            st.markdown(offer_details['terms_conditions'])
    
    # Tab 3: Analytics
    with tab3:
        st.subheader("Offers Analytics")
        
        # Top merchants by offer count
        st.markdown("#### Top Merchants by Offer Count")
        top_merchants = df['merchant'].value_counts().head(10)
        st.bar_chart(top_merchants)
        
        # Offer type distribution over time
        st.markdown("#### Offer Type Distribution Over Time")
        
        # Convert dates and create month column
        df['valid_from'] = pd.to_datetime(df['valid_from'])
        df['month'] = df['valid_from'].dt.strftime('%Y-%m')
        
        # Group by month and offer type
        type_time_dist = df.groupby(['month', 'type']).size().unstack().fillna(0)
        
        # Only show if we have time-based data
        if not type_time_dist.empty and len(type_time_dist) > 1:
            st.line_chart(type_time_dist)
        else:
            st.info("Not enough time-based data to show distribution over time")
        
        # Discount analysis
        st.markdown("#### Discount Analysis by Category")
        
        # Group by category and calculate average discount
        discount_by_category = df.groupby('category')['discount_percent'].mean().sort_values(ascending=False)
        
        # Show the analysis
        if not discount_by_category.empty:
            st.bar_chart(discount_by_category)
        else:
            st.info("Not enough discount data available for analysis")
        
        # Correlation analysis
        st.markdown("#### Correlation: Minimum Purchase vs. Discount")
        
        # Filter for rows with both values present
        corr_data = df[['minimum_purchase', 'discount_percent']].dropna()
        
        if len(corr_data) > 5:
            fig = px.scatter(
                corr_data,
                x='minimum_purchase',
                y='discount_percent',
                title='Correlation between Minimum Purchase and Discount Percentage',
                labels={
                    'minimum_purchase': 'Minimum Purchase (₹)',
                    'discount_percent': 'Discount Percentage (%)'
                },
                trendline='ols'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate correlation coefficient
            correlation = corr_data.corr().iloc[0, 1]
            st.markdown(f"**Correlation Coefficient:** {correlation:.2f}")
            
            if correlation > 0.5:
                st.success("Strong positive correlation: Higher minimum purchase amounts tend to offer larger discounts")
            elif correlation < -0.5:
                st.success("Strong negative correlation: Lower minimum purchase amounts tend to offer larger discounts")
            else:
                st.info("No strong correlation between minimum purchase amount and discount percentage")
        else:
            st.info("Not enough data points to perform correlation analysis")

        # Customers tab
        with tab4:
            if customers_module_available:
                try:
                    customers.show_customers_tab()
                except Exception as e:
                    st.error(f"Error displaying customers tab: {e}")
                    st.exception(e)
            else:
                st.warning("Customers module not available. Please make sure customers.py is in your repository.")

        # Transactions tab
        with tab5:
            if show_transactions_tab:
                show_transactions_tab()
            else:
                st.error("Transaction analysis module not found")

if __name__ == "__main__":
    main()
