import re

def is_safe_query(query: str) -> bool:
    """
    Allow only SELECT statements, block others.
    Basic validation to block UPDATE, DELETE, INSERT, etc.
    """
    query = query.strip().lower()
    # Only allow statements starting with 'select' and block other SQL keywords
    if not query.startswith("select"):
        return False
    forbidden_keywords = ["insert", "update", "delete", "drop", "create", "alter", ";", "--"]
    return not any(keyword in query for keyword in forbidden_keywords)
