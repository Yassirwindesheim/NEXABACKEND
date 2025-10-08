# Placeholder for additional security utilities (e.g., role extraction)
def has_admin_role(claims: dict) -> bool:
    role = claims.get("role") or claims.get("user_metadata", {}).get("role")
    return role == "Admin"