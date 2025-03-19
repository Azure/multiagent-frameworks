import os
from typing import List
from semantic_kernel.functions.kernel_function_decorator import kernel_function

sample_data_path = os.path.join("..", "sample_data")


class MultiAgentToolsPlugin:

    @kernel_function
    def get_account_info(self, account_id: str) -> str:
        """Get account information for the given account ID."""
        try:
            account_data_file = os.path.join(sample_data_path, f"{account_id}.json")
            with open(account_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Account not found."

    @kernel_function
    def get_transaction_details(self, account_id: str) -> str:
        """Get transaction details for the given account ID."""
        try:
            txn_data_file = os.path.join(sample_data_path, f"Txn_{account_id}.json")
            with open(txn_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Transaction details not found."



