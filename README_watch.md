# envault watch

The **watch** feature lets you track changes to secrets over time by recording
a cryptographic fingerprint baseline and comparing future states against it.

## Commands

### `envault watch snapshot`

Capture the current state of all secrets as the watch baseline.

```bash
envault watch snapshot --vault-dir ./myproject --password $VAULT_PASS
```

### `envault watch check`

Compare the current secrets against the saved baseline and print any changes.

```bash
envault watch check --vault-dir ./myproject --password $VAULT_PASS
```

Output example:

```
  [ADDED   ] NEW_FEATURE_FLAG
  [MODIFIED] DB_PASSWORD
  [REMOVED ] OLD_API_TOKEN
```

### `envault watch reset`

Clear the baseline so the next `check` treats all current secrets as freshly
added.

```bash
envault watch reset --vault-dir ./myproject --password $VAULT_PASS
```

## Programmatic API

```python
from envault.watch import detect_changes, save_watch_state, _secret_fingerprint

secrets = vault.load(password)

# Record baseline
save_watch_state(secrets, _secret_fingerprint(secrets))
vault.save(secrets, password)

# Later — detect what changed
changes = detect_changes(secrets)
for key, change_type in changes.items():
    print(f"{key}: {change_type}")
```

## How it works

1. `snapshot` computes an MD5 fingerprint for every non-internal secret value
   and stores the fingerprint map as `__watch_state__` inside the encrypted
   vault.
2. `check` re-computes fingerprints and diffs them against the stored state,
   classifying each difference as *added*, *removed*, or *modified*.
3. All watch operations are recorded in the audit log.
