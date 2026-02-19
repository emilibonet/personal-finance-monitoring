import os
import json
from argparse import ArgumentParser
import pandas as pd
from datetime import datetime
from utils import logging, ROOT_DIR

REGISTER_PATH = f"{ROOT_DIR}/data/processed/register.json"

def get_files(reprocess: bool = False) -> list:
    all_files = os.listdir(f"{ROOT_DIR}/data/raw")
    if reprocess or not os.path.exists(REGISTER_PATH):
        return all_files, {}
    with open(REGISTER_PATH, "r") as f:
        register = json.load(f)
    return [file for file in all_files if file not in register], register

def flag_recurring(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    base_flag = df['description'].str.lower().str.startswith('european direct debit creditor')

    df_sorted = df.sort_values(['recipient', 'date'])
    prev_dates = df_sorted.groupby('recipient')['date'].shift(1)
    days_diff = (df_sorted['date'] - prev_dates).dt.days
    periodic_flag = days_diff.between(27, 33)

    # Combine results and restore original order
    is_recurring = base_flag.copy()
    is_recurring.loc[df_sorted.index] = is_recurring.loc[df_sorted.index] | periodic_flag
    return is_recurring

def apply_fixed_rules(df: pd.DataFrame) -> None:
    df['is_recurring'] = flag_recurring(df)
    df['is_essential'] = False
    df['concept'] = 'Others'
    fixed_rules = {
        'Salary': {'keywords': ['arhs'], 'is_essential': True},
        'Rent': {'keywords': ['despes'], 'is_essential': True},
        # 'Utilities': {'keywords': [], 'is_essential': True},
        'Groceries': {'keywords': ['delhaize', 'carrefour', 'crf exp', 'finest globe belliard'], 'is_essential': True},
        'Insurance': {'keywords': ['FMSB-FSMB'], 'is_essential': True},
        'Savings': {'keywords': ['estalvis'], 'is_essential': True},
        'Grooming': {'keywords': ['sportoase', 'xxl nutrition','apotheek', 'knapper'], 'is_essential': True},
        'Transport': {'keywords': ['stib', 'sncb', 'nmbs', 'bahn'], 'is_essential': True},
        'Cantine': {'keywords': ['cantine'], 'is_essential': False},
        'Subscriptions': {'keywords': ['kbc plus'], 'is_essential': False},
    }
    for concept, attributes in fixed_rules.items():
        pattern = '|'.join(attributes['keywords'])
        mask = df['description'].str.lower().str.contains(pattern)
        df.loc[mask, 'concept'] = concept
        df.loc[mask, 'is_essential'] = attributes['is_essential']

def preprocessing(reprocess: bool = False) -> None:
    files, register = get_files(reprocess)
    if not files:
        logging.info("No new files to process; exiting preprocessing")
        return None
    # Get number of columns with header
    with open(f"{ROOT_DIR}/data/raw/{files[0]}") as f:
        ncols = len(f.readline().strip().split(';'))
    df = pd.concat(
        [pd.read_csv(f"{ROOT_DIR}/data/raw/{file}", sep=';', usecols=range(ncols), index_col=False) for file in files if file.endswith('.csv')],
        ignore_index=True
    )
    df.rename(columns={
        'Accountnumber': 'sender',
        'Counterparty account number': 'recipient'
    }, inplace=True)
    df.drop(columns=[
        "Heading",
        "Name",
        "Currency",
        "Value date",
        "Credit",
        "Debit",
        "Counterparty BIC",
        "Counterparty name",
        "Counterparty address",
        "Standard-format reference",
        "Free-format reference"
    ], inplace=True, errors='ignore')
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', dayfirst=True, errors='coerce')
    df = df.sort_values(by='date').reset_index(drop=True)
    df['amount'] = df['amount'].str.replace(',', '.').astype(float)
    df['balance'] = df['balance'].str.replace(',', '.').astype(float)
    apply_fixed_rules(df)
    sender_mapping = {
        os.getenv('GENERAL_ACCOUNT_ENDING'): 'General',
        os.getenv('SAVINGS_ACCOUNT_ENDING'): 'Savings'
    }
    def replace_sender(value):
        for suffix, replacement in sender_mapping.items(): 
            if value.endswith(suffix):
                return replacement
        return value
    df['sender'] = df['sender'].apply(replace_sender)
    logging.info("Data preprocessing completed; updating transactions.csv")
    if reprocess:
        df.to_csv(f"{ROOT_DIR}/data/processed/transactions.csv", index=False)
        register = {}
    else:
        transactions = load()
        pd.concat([transactions, df], ignore_index=True).to_csv(f"{ROOT_DIR}/data/processed/transactions.csv", index=False)
    for file in files:
        register[file] = {
            "timestamp": datetime.now().isoformat(),
        }
    with open(REGISTER_PATH, "w") as f:
        json.dump(register, f, indent=4)


def load() -> pd.DataFrame:
    df = pd.read_csv(f"{ROOT_DIR}/data/processed/transactions.csv")
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['sender'] == 'General'].reset_index(drop=True)
    return df


if __name__ == '__main__':
    parser = ArgumentParser(description="Preprocess financial transaction data.")
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help="Reprocess all raw data files."
    )
    args = parser.parse_args()
    preprocessing(reprocess=args.reprocess)
