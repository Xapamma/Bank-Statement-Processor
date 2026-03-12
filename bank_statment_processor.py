import pandas as pd
import glob
import os
from rapidfuzz import process, fuzz

# Root folder containing bank folders
folder = ".data"

# Known banks and account types
known_banks = ["goldenwest", "chase", "wellsfargo", "amex"]  # extend as needed
account_types = ["checking", "savings", "credit", "loan", "investment"]

# Optimized categories
category_map = {
    "Housing": ["Mortgage/Rent", "Utilities", "Phone", "Cable/Internet", "Waste", "Maintenance/Repairs"],
    "Transportation": ["Vehicle Payments", "Insurance", "Fuel", "Licensing", "Parking", "Repairs", "Maintenance", "Other"],
    "Loans / Credit": ["Credit Card", "Student Loan", "House Loan", "Other"],
    "Insurance": ["Home/Rental", "Health", "Life", "Other"],
    "Taxes": ["Federal", "State", "Local", "Other"],
    "Savings / Investments": ["Emergency Fund", "Retirement", "Transfer to Savings", "Investments", "House Down Payment", "Other"],
    "Food / Dining": ["Groceries", "Restaurants/Dining", "Fast Food", "Snacks", "Other"],
    "Entertainment": ["Movies/Theater", "Music Platforms", "Concerts/Plays", "Games", "Hobbies", "Outdoor Recreation", "Travel", "Other"],
    "Personal Care / Health": ["Doctor/Dentist", "Medicine/Drugs", "Hair/Nails", "Health Club", "Discretionary", "Other"],
    "Education": ["Tuition", "Books", "Other"],
    "Gifts & Donations": ["Tithing", "Fast Offerings", "Gift", "Other"],
    "Vacations / Travel": ["Travel", "Lodging", "Food", "Entertainment", "Souvenirs", "Other"]
}

# Function to assign main/sub category
def assign_categories(description, category_map):
    if pd.isna(description) or description.strip() == "":
        return ("Other", "Other")
    best_sub = None
    best_main = None
    best_score = 0
    description_lower = description.lower()
    for main_cat, subcats in category_map.items():
        match = process.extractOne(description_lower, subcats, scorer=fuzz.ratio)
        if match is not None:
            subcat_name, score = match[0], match[1]
            if score > best_score:
                best_score = score
                best_sub = subcat_name
                best_main = main_cat
    if best_main is None:
        return ("Other", "Other")
    return (best_main, best_sub)

# List to hold all banks
all_banks = []

# Scan folders in .data
bank_folders = [f.path for f in os.scandir(folder) if f.is_dir()]

for bank_folder in bank_folders:
    raw_bank_name = os.path.basename(bank_folder)

    # Fuzzy match bank name
    match_result = process.extractOne(raw_bank_name, known_banks, scorer=fuzz.ratio)
    bank_name = match_result[0]  # best match
    bank_score = match_result[1]  # match score
    print(f"Processing bank folder: {raw_bank_name} → matched to {bank_name} (score {bank_score})")

    # Find CSV files in the bank folder
    files = glob.glob(os.path.join(bank_folder, "*.csv"))
    bank_dfs = []

    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()

        # Bank-specific column cleaning
        if bank_name == "goldenwest":
            df = df.rename(columns={
                "transaction date": "date",
                "posting date": "date",
                "description": "description",
                "amount": "amount",
                "balance": "balance"
            })
        elif bank_name == "chase":
            df = df.rename(columns={
                "date": "date",
                "details": "description",
                "credits/debits": "amount",
                "running balance": "balance"
            })
        # Add more banks here as needed

        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Clean amount column
        df["amount"] = (
            df["amount"]
            .astype(str)
            .str.replace(",", "")
            .str.replace("(", "-")
            .str.replace(")", "")
            .astype(float)
        )

        # Fuzzy match account type from filename
        filename_lower = os.path.basename(file).lower()
        match_result = process.extractOne(filename_lower, account_types, scorer=fuzz.ratio)
        account_name = match_result[0]
        account_score = match_result[1]

        df["bank"] = bank_name
        df["account"] = account_name

        # Assign optimized main/sub categories
        df[["main_category", "sub_category"]] = df["description"].apply(
            lambda x: pd.Series(assign_categories(x, category_map))
        )
        
        bank_dfs.append(df)
    
    # Combine all accounts for this bank
    bank_combined = pd.concat(bank_dfs, ignore_index=True)
    all_banks.append(bank_combined)

# Combine all banks
combined = pd.concat(all_banks, ignore_index=True)
combined = combined.sort_values("date")

# Keep only necessary columns
columns_to_keep = ["date", "description", "amount", "balance", "bank", "account", "main_category", "sub_category"]
combined = combined[columns_to_keep]

# Save final cleaned and categorized CSV
combined.to_csv("all_banks_final_categorized.csv", index=False)
print("✅ Done! Final cleaned and categorized CSV saved as 'all_banks_final_categorized.csv'.")











# # Read the bank statement CSV files
# def read_bank_statement(file_path):
#     try:
#         df = pd.read_csv(file_path)
#         return df
#     except Exception as e:
#         print(f"Error reading the file: {e}")
#         return None
    
# # Clean and preprocess the data
# def clean_data(df):
#     # Example cleaning steps
#     df.dropna(inplace=True)  # Remove missing values
#     df['Date'] = pd.to_datetime(df['Date'])  # Convert Date column to datetime
#     return df

# # Analyze the transactions
# def analyze_transactions(df):
#     # Example analysis: Calculate total income and expenses
#     total_income = df[df['Amount'] > 0]['Amount'].sum()
#     total_expenses = df[df['Amount'] < 0]['Amount'].sum()
#     return total_income, total_expenses

# # Generate a summary report
# def generate_summary_report(total_income, total_expenses):
#     report = f"Total Income: ${total_income:.2f}\nTotal Expenses: ${total_expenses:.2f}"
#     return report

# # Main function to process the bank statement
# def process_bank_statement(file_path):
#     df = read_bank_statement(file_path)
#     if df is not None:
#         df = clean_data(df)
#         total_income, total_expenses = analyze_transactions(df)
#         report = generate_summary_report(total_income, total_expenses)
#         print(report)