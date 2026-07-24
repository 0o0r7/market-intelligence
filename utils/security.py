from __future__ import annotations
import os
from typing import Optional
from config.settings import get_settings

def _try_key_vault(secret_name: str) -> Optional[str]:
    settings = get_settings()
    vault_url = settings.key_vault_url
    if not vault_url: return None
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        kv_name = secret_name.replace("_", "-")
        return client.get_secret(kv_name).value
    except Exception: return None

def resolve_secret(env_name: str, *, required: bool = False) -> Optional[str]:
    value = os.environ.get(env_name)
    if value: return value
    settings = get_settings()
    attr = env_name.lower()
    value = getattr(settings, attr, None)
    if value: return value
    value = _try_key_vault(env_name)
    if value: return value
    if required: raise RuntimeError(f"Required secret '{env_name}' not found in environment, settings, or Key Vault.")
    return None