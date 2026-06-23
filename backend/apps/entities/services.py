"""
Entities service layer.

API key generation lives here because it mixes cryptographic operations with
two model writes — that's domain logic, not a view concern.
"""
import hashlib
import secrets


def generate_api_key(*, entity, created_by_user_id: int, name: str = "", expiry_date=None) -> dict:
    """
    Generate a new API key for an entity.

    Returns a dict with the raw key (shown once to the user), the prefix
    (stored in plaintext for identification), and the created record ID.
    The raw key is never stored — only a SHA-256 hash is persisted.

    Caller is responsible for returning the raw_key to the client exactly once.
    """
    from apps.shared.models import EntityApiKeys
    from apps.entities.models import EntityApiKeysIntermediary

    raw_key = secrets.token_urlsafe(32)
    hashed  = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix  = raw_key[:8]

    key = EntityApiKeys.objects.create(
        EntityId          = entity.EntityId,
        HashedApiKey      = hashed,
        KeyPrefix         = prefix,
        ExpiryDate        = expiry_date,
        AuthorizedByFor   = name,
        CreatedBy         = created_by_user_id,
    )
    EntityApiKeysIntermediary.objects.create(EntityId=entity, ApiKeyId=key)

    return {
        "ApiKeyId":  key.ApiKeyId,
        "KeyPrefix": prefix,
        "RawKey":    raw_key,
        "ExpiryDate": key.ExpiryDate,
    }


def revoke_api_key(*, key) -> None:
    """Soft-delete an API key by setting Status = 4."""
    key.Status = 4
    key.save()
