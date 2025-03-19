
import os
from typing import Any, Callable, Set, Dict, List, Optional

sample_data_path = os.path.join(".", "sample_data")




def get_transaction_details(account_id: str) -> str:
    """Get transaction details for the given account ID."""
    try:
        txn_data_file = os.path.join(sample_data_path, f"Txn_{account_id}.json")
        with open(txn_data_file, "r") as file:
            data = file.read()
        return data
    except FileNotFoundError:
        return "Transaction details not found."


get_transaction_info_tool_functions: Set[Callable[..., Any]] = {
    
    get_transaction_details
}