import os
from supabase import create_client, Client
from functools import lru_cache


@lru_cache()
def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def set_tenant(client: Client, tenant_id: str) -> None:
    client.rpc(
        "set_config",
        {"parameter": "app.current_tenant_id", "value": tenant_id, "is_local": True},
    ).execute()
