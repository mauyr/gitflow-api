from gitflow_api.domain.exceptions import ConfigError


def require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing required config field: {field_name}")
    return value.strip()


def ensure_provider_supported(provider_type: str) -> str:
    normalized = provider_type.strip().lower()
    if normalized not in {"gitlab", "github"}:
        raise ConfigError(
            f"Unsupported provider '{provider_type}'. Supported providers: 'gitlab', 'github'."
        )
    return normalized
