import re
import pandas as pd
import numpy as np
import subprocess

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
    r"shoeman\s*enterprise": "Shoeman Enterprise",

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
    "Jacksons Food Stores": "Groceries",
    "Aldi Nord": "Groceries",
    "Volker's Bakery": "Groceries",
    "Life Starfish": "Groceries",
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
    "Backwerk": "Fast Food",
    "Burger King Sot": "Fast Food",
    "Carl's Jr.": "Fast Food",
    "Chipotle": "Fast Food",
    "Del Taco": "Fast Food",
    "Noodles And Company": "Fast Food",
    "Papa John's": "Fast Food",
    "Papa Murphy's Ut Olo": "Fast Food",
    "Py Johnny Rockets": "Fast Food",
    "Wiener Feinbackerei": "Fast Food",
    "Yogurtland Ut": "Fast Food",
    "Cafe Zupas": "Restaurants/Dining",
    "Cheesecake": "Restaurants/Dining",
    "Golden Corral": "Restaurants/Dining",
    "Ristorante Calice Doro": "Restaurants/Dining",
    "Texas Roadhouse": "Restaurants/Dining",
    "Rewe Markt Gmbh": "Groceries",
    "Landbaeckerei Schmidt": "Fast Food",
    "Le Crobag De": "Fast Food",
    "Chocoladefabriken Lindt": "Fast Food",
    "Confiserie Felicitas": "Fast Food",
    "Kamps Berlin": "Fast Food",
    "Milk & Cookies": "Fast Food",
    "Nielsens Frozen Custard": "Fast Food",
    "Roxberry Juice Co.": "Fast Food",
    "Sq Chromis Bakery": "Fast Food",
    "Willy Dany Restaurantb": "Fast Food",
    "Dolce Freddo Gmbh": "Fast Food",
    "Leatherby'S Family Cream": "Fast Food",
    "Fabulous Freddy's": "Fast Food",
    "Tstbrookers - Provo": "Fast Food",

    # --- Automotive & Fuel ---
    "Costco Gas": "Fuel",
    "Maverik": "Fuel",
    "Shell": "Fuel",
    "Chevron": "Fuel",
    "Bear River Insurance": "Insurance",
    "Jiffy Lube": "Maintenance",
    "DMV": "Maintenance",
    "Slc Airport Parking": "Maintenance",
    "Salt Lake City Airport Parking": "Maintenance",
    "Autozone": "Auto Parts",
    "Zephyr Lot": "Maintenance",

    # --- Health & Wellness ---
    "Oak Hills Pharmacy": "Pharmacy",
    "Walgreens": "Pharmacy",
    "Crosspointe Dental": "Medical",
    "Bath & Body Works": "Personal Care",
    "Hearts Nail Spa": "Personal Care",
    "Rossmann": "Personal Care",
    "Victoria's Secret": "Personal Care",
    "Spccity-Apotheken Dresde": "Pharmacy",
    "Sq Winters Custom Hair D": "Personal Care",
    "Sq Tie One On": "Personal Care",
    
    # --- Travel & Lodging ---
    "Delta Air Baggage Fee": "Travel & Commute",
    "Klm Airline": "Airfare",
    "Cotflt": "Airfare",
    "Flughafen Berlin Brand": "Travel & Commute",
    "Grandma Becky Payment": "Lodging",
    "Arcotel Hafencity Dresden": "Lodging",
    "Elaya Ht. Leipzig City": "Lodging",
    "Hotel Johann Berlin Recep": "Lodging",
    "Cothtl": "Lodging",
    "Areas Roissy": "Travel & Commute",
    "Hms Host International": "Travel & Commute",
    "Mopla Bewegt": "Travel & Commute",

    # --- Shopping & Supplies ---
    "Amazon": "General Retail",
    "Ross": "General Retail",
    "Barnes & Noble": "General Retail",
    "Dick'S Sporting Goods": "General Retail",
    "Downeast": "Clothing",
    "Jcpenney": "Clothing",
    "Maurices": "Clothing",
    "Spirit Halloween": "Clothing",
    "Home Depot": "Home Improvement",
    "Hobby Lobby": "Hobbies",
    "Sweetwater-Recordstore-Ja": "Hobbies",
    "Enticon Shops": "General Retail",
    "Post Mart": "General Retail",
    "Saturn Electro-Handels": "General Retail",
    "Tricked Out Accessories U": "General Retail",
    "Famous Footwear": "Clothing",
    "Shoeman Enterprise": "Clothing",
    "Bm Weihnachtsland K": "General Retail",
    "Fye University Place": "General Retail",
    "Springville Di": "General Retail",

    # --- Housing & Bills ---
    "T-Mobile": "Phone",
    "Cbtutah County Clerk": "Service Fees",
    "Cbtsvc Fee Utah Cnty": "Service Fees",
    "Google Services": "Service Fees",
    "Visa Service Fee": "Service Fees",
    "Capital One Member Fee": "Service Fees",
    "Hrb Online Tax Product": "Service Fees",
    "Sl.Nord Vpncom": "Service Fees",
    "Ut Hunt/Fish Lic. Onli": "Service Fees",
    
    # --- Gifts & Donations ---
    "Church Donations": "Tithing",

    # --- Education ---
    "BYU (Campus Services)": "Education",
    "Ebook Academy": "Education",

    # --- Entertainment ---
    "Steam (Gaming)": "Gaming",
    "Fandango/Vudu": "Streaming/Movies",
    "Cinemark Boxcon": "Streaming/Movies",
    "Cinemark Online": "Streaming/Movies",
    "Lava Hot Springs": "Recreation",
    "Dancefitme Fun": "Recreation",
    "Lagoon Rfm": "Recreation",
    "Lagoon Tic-Ag": "Recreation",
    "Sp Shopcornbellys": "Recreation",
    "Espn": "Streaming/Movies",
    "Provo City Cntr Temple": "Recreation",
    "Voelkerschlachtdenkmal Le": "Recreation",

    # --- Savings & Investments ---
    "Interest Earned": "Dividends",
    "Dividend Income": "Dividends",
    "Investment Income": "Dividends",
    "Robinhood Investment": "Investments",

    # --- Income ---
    "Payroll Deposit": "Paychecks",
    "BYU Refund": "Refunds",
    "Apple Services": "Refunds",
    "Credit-Travel Reward": "CC Rewards",
    "Youth Engagement Promo": "Other Income",
}

# --- 3. CATEGORY HIERARCHY ---
category_hierarchy = {
    "Food / Dining": ["Groceries", "Restaurants/Dining", "Fast Food"],
    "Automotive & Fuel": ["Fuel", "Insurance", "Maintenance", "Auto Parts"],
    "Health & Wellness": ["Medical", "Personal Care", "Pharmacy"],
    "Travel & Lodging": ["Airfare", "Lodging", "Travel & Commute"],
    "Shopping & Supplies": ["General Retail", "Home Improvement", "Hobbies", "Clothing"], 
    "Housing & Bills": ["Mortgage/Rent", "Phone", "Cable/Internet", "Service Fees", "Utilities"],
    "Gifts & Donations": ["Tithing", "Gift"],
    "Education": ["Education"],
    "Entertainment": ["Gaming", "Streaming/Movies", "Recreation"],
    "Savings & Investments": ["Dividends", "Investments"],
    "Income": ["Paychecks", "Refunds", "CC Rewards", "Other Income"],
    "Miscellaneous": ["Fees & Charges", "Other Services"]         
}

# Connects sub to main title
sub_to_main = {sub: main for main, subs in category_hierarchy.items() for sub in subs}

# Basic cleaning for descriptions
def clean_description_for_matching(description):
    raw_desc = str(description).lower()

    # Normalize "withdrawal"
    raw_desc = re.sub(r'^\s*withdrawal\s*$', 'bank withdrawal', raw_desc)

    # Strip common bank noise
    raw_desc = re.sub(
        r'^withdrawal\s*(xx)?\s*x?\b|xx\s*(sq|card|[a-z])?|^recurring\s*withdrawal\s*|provo\s*ut|\borem\b',
        '',
        raw_desc
    ).strip()

    return raw_desc

# Check the regex cleaning first
def match_description_map(raw_desc):
    for pattern, replacement in description_map.items():
        if re.search(pattern, raw_desc):
            return replacement
    return None


def clean_and_categorize(df):

    def process_row(row):
        # Convert to lowercase for pattern matching
        raw_desc = str(row['merchant']).lower()
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
    noise_list = ["transfer to sofi", "to checking", "angel funding", "roundup", "home banking transfer", "pymt", "payment to", "north capital", "internal transfer"]
    df = df[~df['description'].str.lower().str.contains('|'.join(noise_list), na=False)]

    # Ensure description is Title Case for final output
    df['description'] = df['description'].str.title()

    # 2. Specifically fix the lowercase 's' after apostrophes
    df['description'] = df['description'].str.replace(r"'S\b", "'s", regex=True)
    
    return df
