import json
from pathlib import Path

def verify_token(input_key: str):
    token_path = Path("/srv/cockswain-core/scripts/caretaker_token.json")
    if not token_path.exists():
        return False, "token_file_missing"
    data = json.loads(token_path.read_text())
    valid_key = data.get("access_key")
    if input_key == valid_key:
        return True, "verified"
    return False, "invalid_key"
