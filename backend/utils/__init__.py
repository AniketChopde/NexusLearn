"""Utils package initialization."""

from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    create_token_pair
)

from utils.helpers import (
    serialize_datetime,
    safe_json_dumps,
    safe_json_loads,
    generate_hash,
    paginate_results,
    calculate_percentage,
    format_time_duration,
    validate_email,
    sanitize_input,
    get_error_response,
    get_success_response
)

__all__ = [
    # Auth
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "create_token_pair",
    # Helpers
    "serialize_datetime",
    "safe_json_dumps",
    "safe_json_loads",
    "generate_hash",
    "paginate_results",
    "calculate_percentage",
    "format_time_duration",
    "validate_email",
    "sanitize_input",
    "get_error_response",
    "get_success_response",
]
