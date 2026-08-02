import re

# =============================================================================
# Guest nicknames
# =============================================================================

# Allowed shape for a guest nickname: 3-20 letters, digits, "_" or "-".
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
