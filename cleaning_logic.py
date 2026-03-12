import re
import pandas as pd
import numpy as np

# --- 1. DESCRIPTION CLEANING MAP ---
# Patterns are lowercase here for easier matching
description_map = {
    # --- RETAIL & SHOPPING ---
    r"wal\W*mart|wm superc|walmart": "Walmart Supercenter",
    r"costco whse|costco": "Costco Wholesale",
    r"amazon|amzn|amazon\.com|amazon mutiplace pits": "Amazon",
    r"ross stores|ross dress": "Ross",
    r"bath & body works": "Bath & Body Works",
    r"home depot": "Home Depot",
    r"maceys": "Macey's",

    # --- DINING & TREATS ---
    r"mcdonald's|mcdonalds": "McDonald's",
    r"chick-fil-a": "Chick-fil-A",
    r"taco bell": "Taco Bell",
    r"subway": "Subway",
    r"cafe zupas": "Cafe Zupas",
    r"panda express": "Panda Express",
    r"domino's|dominos": "Domino's Pizza",
    r"kneaders": "Kneaders",
    r"culver's|culvers": "Culver's",
    r"red cliffs boba": "Red Cliffs Boba Tea",
    r"cold stone": "Cold Stone Creamery",
    r".*tstbrookers.*": "Brookers Ice Cream",
    r".*popbite square.*": "Popbite Bakery",

    # --- TRANSPORTATION & AUTO ---
    r"costco gas station|costco-gas": "Costco Gas",
    r"maverik|maverick": "Maverik",
    r"shell oil": "Shell",
    r"chevron": "Chevron",
    r"jiffy lube": "Jiffy Lube",
    r"dmv": "DMV",

    # --- SERVICES, HEALTH & EDUCATION ---
    r"oak hills pharmacy": "Oak Hills Pharmacy",
    r"crosspointe dental": "Crosspointe Dental",
    r"bear river": "Bear River Insurance",
    r"t-mobile|tmobile": "T-Mobile",
    r"google \*": "Google Services",
    r"://apple.com": "Apple Services",
    r".*ebook accademy.*": "Ebook Academy",
    r"byu refund|brigham young un": "BYU Refund",
    r"byu|cougar cash|byu store": "BYU (Campus Services)",

    # --- DONATIONS & FAMILY ---
    r"church of jesus|lds philanthr|donation|ch jesuschrist": "Church Donations",
    r".*life starfish.*": "Life Starfish",
    r"life\s*starfish": "Life Starfish",
    r".*ouelessebougoualliance.*": "Ouelessebougou Alliance",
    r".*grandma becky.*": "Grandma Becky Payment",

    # --- ENTERTAINMENT & HOBBIES ---
    r"recurring withdrawal.*dancefitme.*": "Dancefitme Fun",
    r"fandango at home|vudu\.com|fandango": "Fandango/Vudu",
    r"steamgames.com": "Steam (Gaming)",
    r".*portneuf rapids tube.*|lava hot spri": "Lava Hot Springs",

    # --- INCOME, INTEREST & FEES ---
    r"deposit dividend|interest earned|interest payment": "Interest Earned",
    r"payroll withdraw|salary": "Payroll Deposit",
    r"dividend.*annual": "Dividend Income",
    r".*visa international service assessment.*": "Visa Service Fee",
    r"robinhood": "Robinhood Investment",

    # --- MISC / TRANSFERS ---
    r"home banking transfer": "Internal Transfer",
    r"pos withdrawal": "Debit Purchase",
    r"payment to perks": "Perks Payment",
}

# --- 2. SUB-CATEGORY MAP ---
sub_category_map = {
    # --- Food / Dining ---
    "Walmart Supercenter": "Groceries",
    "Costco Wholesale": "Groceries",
    "Macey's": "Groceries",
    "McDonald's": "Fast Food",
    "Chick-fil-A": "Fast Food",
    "Taco Bell": "Fast Food",
    "Subway": "Fast Food",
    "Panda Express": "Fast Food",
    "Domino's Pizza": "Fast Food",
    "Kneaders": "Fast Food",
    "Culver's": "Fast Food",
    "Red Cliffs Boba Tea": "Fast Food",
    "Cold Stone Creamery": "Fast Food",
    "Brookers Ice Cream": "Fast Food",
    "Popbite Bakery": "Fast Food",
    "Cafe Zupas": "Restaurants/Dining",

    # --- Transportation ---
    "Costco Gas": "Fuel",
    "Maverik": "Fuel",
    "Shell": "Fuel",
    "Chevron": "Fuel",
    "Jiffy Lube": "Maintenance",
    "DMV": "Maintenance",

    # --- Savings / Investments ---
    "Interest Earned": "Dividends",
    "Dividend Income": "Dividends",
    "Investment Income": "Dividends",
    "Robinhood Investment": "Investments",

    # --- Income ---
    "Payroll Deposit": "Paychecks",
    "BYU Refund": "Refunds",
    "Youth Engagement Promo": "Other Income",
    "Apple Services": "Refunds",
    "Credit-Travel Reward": "CC Rewards",

    # --- Shopping (The "Other" items) ---
    "Amazon": "General Retail",
    "Ross": "General Retail",
    "Bath & Body Works": "Personal Care",
    "Home Depot": "Home Improvement",

    # --- Entertainment & Recreation ---
    "Steam (Gaming)": "Gaming",
    "Fandango/Vudu": "Streaming/Movies",
    "Lava Hot Springs": "Recreation",
    "Dancefitme Fun": "Recreation",

    # --- Gifts & Donations ---
    "Church Donations": "Tithing",
    
    # --- Health & Education ---
    "Oak Hills Pharmacy": "Medical",
    "Crosspointe Dental": "Medical",
    "BYU (Campus Services)": "Education",
    "Ebook Academy": "Education",

    # --- Housing / Utilities ---
    "T-Mobile": "Phone",
    "Google Services": "Other",

    # --- Health & Services (Falls to General Spending) ---
    "Bear River Insurance": "Insurance",
    "Visa Service Fee": "Other",
    "Life Starfish": "Other",
    "Ouelessebougou Alliance": "Other",
    "Grandma Becky Payment": "Other",
}

# --- 3. CATEGORY HIERARCHY ---
category_hierarchy = {
    "Housing": ["Mortgage/Rent", "Utilities", "Phone", "Cable/Internet"],
    "Food / Dining": ["Groceries", "Restaurants/Dining", "Fast Food"],
    "Transportation": ["Fuel", "Insurance", "Maintenance"],
    "Gifts & Donations": ["Tithing", "Gift"],
    "Savings / Investments": ["Dividends", "Investments"],
    "Income": ["Paychecks", "Refunds", "CC Rewards"],
    "Shopping": ["General Retail", "Home Improvement", "Personal Care"], 
    "Entertainment": ["Gaming", "Streaming/Movies", "Recreation"],        
    "Health & Services": ["Medical", "Education", "Service Fees"]         
}

# Connects sub to main title
sub_to_main = {sub: main for main, subs in category_hierarchy.items() for sub in subs}

def clean_and_categorize(df):

    def process_row(row):
        # Convert to lowercase for pattern matching
        raw_desc = str(row['description']).lower()
        amt = row['amount']
        clean_name = None

        # Strip Bank Noise (Withdrawal, Xx, trailing locations)

        # \b ensures it's the whole word, and ^/$ ensures it's the ONLY thing in the string
        raw_desc = re.sub(r'^\s*withdrawal\s*$', 'bank withdrawal', raw_desc)

        # This turns "Withdrawal Xx Subway Provo Ut" -> "subway"
        raw_desc = re.sub(r'^withdrawal\s*(xx)?\s*x?\b|xx\s*(sq|card|[a-z])?|^recurring\s*withdrawal\s*|provo\s*ut|\borem\b', '', raw_desc).strip()    
        # Regex Matching (Checks against lowercase raw_desc)
        for pattern, replacement in description_map.items():
            if re.search(pattern, raw_desc):
                clean_name = replacement
                break
        
        # Fallback Cleaning (Strip numbers/special chars and Squish)
        if not clean_name:
            clean = re.sub(r'[0-9#*]', '', raw_desc)
            clean_name = " ".join(clean.split()).title()

        # Determine Sub-Category
        sub = sub_category_map.get(clean_name, "Other")
        
        # Determine Main Category with "General Spending" and "Other Income" fallbacks
        if sub in sub_to_main:
            main = sub_to_main[sub]
        elif amt < 0:
            main = "General Spending"
        else:
            main = "Other Income"
            
        return pd.Series([clean_name, main, sub])

    # Apply across rows
    df[['description', 'main_category', 'sub_category']] = df.apply(process_row, axis=1)
    
    # Filter Internal Noise (Transfers/Roundups)
    noise_list = ["transfer to sofi", "to checking", "angel funding", "roundup", "home banking transfer", "pymt", "payment", "north capital", "internal transfer"]
    df = df[~df['description'].str.lower().str.contains('|'.join(noise_list), na=False)]

    # Ensure description is Title Case for final output
    df['description'] = df['description'].str.title()
    
    return df
