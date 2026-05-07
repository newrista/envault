# Secret Lifecycle Management

envault supports tracking the **lifecycle state** of each secret, helping teams
identify which secrets are actively used, deprecated, or fully retired.

## States

| State        | Meaning                                         |
|--------------|-------------------------------------------------|
| `active`     | Secret is in use and healthy                    |
| `deprecated` | Secret is being phased out; avoid new usage     |
| `retired`    | Secret is no longer valid or in use             |

## CLI Usage

### Set a lifecycle state

```bash
envault lifecycle set API_KEY active
envault lifecycle set OLD_TOKEN deprecated --reason "Replaced by TOKEN_V2"
envault lifecycle set LEGACY_DB_PASS retired
```

### Show lifecycle metadata for a key

```bash
envault lifecycle show API_KEY
# state: active
# created_at: 2024-06-01T10:00:00+00:00
# updated_at: 2024-06-01T10:00:00+00:00
```

### List all keys in a given state

```bash
envault lifecycle list deprecated
# OLD_TOKEN
# LEGACY_KEY
```

### Remove lifecycle metadata

```bash
envault lifecycle remove OLD_TOKEN
```

## Python API

```python
from envault.lifecycle import set_state, get_state, list_by_state, remove_state

set_state(secrets, "API_KEY", "deprecated", reason="use TOKEN_V2")
entry = get_state(secrets, "API_KEY")
keys = list_by_state(secrets, "deprecated")
remove_state(secrets, "API_KEY")
```

## Integration with Lint & Verify

The `lint` and `verify` commands will surface `deprecated` and `retired` secrets
as warnings, prompting teams to clean up stale credentials.
