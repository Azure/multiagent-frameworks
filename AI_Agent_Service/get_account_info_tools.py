
import os
from typing import Any, Callable, Set, Dict, List, Optional

sample_data_path = os.path.join(".", "sample_data")

def get_account_info(account_id: str) -> str:
    """Get account information for the given account ID."""
    try:
        account_data_file = os.path.join(sample_data_path, f"{account_id}.json")
        with open(account_data_file, "r") as file:
            data = file.read()
        return data
    except FileNotFoundError:
        return "Account not found."



get_account_info_tool_functions: Set[Callable[..., Any]] = {
    get_account_info
    
}