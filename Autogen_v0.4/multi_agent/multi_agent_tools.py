import os
from typing import List
from autogen_core.tools import FunctionTool, Tool, ToolSchema

sample_data_path = os.path.join("..", "sample_data")

def get_account_info(account_id: str) -> str:
    try:
        account_data_file = os.path.join(sample_data_path, f"{account_id}.json")
        with open(account_data_file, "r") as file:
            data = file.read()
        return data
    except FileNotFoundError:
        return "Account not found."


def get_transaction_details(account_id: str) -> str:
    try:
        txn_data_file = os.path.join(sample_data_path, f"Txn_{account_id}.json")
        with open(txn_data_file, "r") as file:
            data = file.read()
        return data
    except FileNotFoundError:
        return "Transaction details not found."



tools: List[Tool] = [FunctionTool(get_account_info, description="Gets account details for given account id."),
                     FunctionTool(get_transaction_details, description="Gets transaction details for given account id.")]