# Rollback

The **rollback** feature lets you restore secrets to a previous state using either
the per-key history log or a named checkpoint.

## Commands

```
envault rollback history  KEY [--steps N]   # revert KEY N versions back
envault rollback checkpoint  NAME           # restore all keys from a checkpoint
envault rollback points  KEY               # list available rollback points for KEY
```

## How it works

### History-based rollback

Every time a secret is written, `envault.history.record_history` appends an
entry to an internal index stored inside the vault.  `rollback history` reads
that log and replaces the live value with the entry that was current *N* steps
ago.

```bash
# Undo the last change to API_KEY
envault rollback history API_KEY --steps 1

# Go back two changes
envault rollback history API_KEY --steps 2
```

### Checkpoint-based rollback

Checkpoints capture a snapshot of *all* non-internal keys at a named point in
time.  Rolling back to a checkpoint restores every captured key to its
checkpointed value.

```bash
# Create a checkpoint before a risky rotation
envault checkpoint create pre-rotation

# … something went wrong …
envault rollback checkpoint pre-rotation
```

## Safety

- **Read-only keys** (protected via `envault readonly`) are silently skipped;
  the rollback still completes for all other keys.
- **Internal keys** (surrounded by `__`) cannot be rolled back directly.
- An error is raised if the requested number of history steps exceeds the
  available log length.

## Python API

```python
from envault.rollback import rollback_to_history, rollback_to_checkpoint

# Revert one step
result = rollback_to_history(secrets, "API_KEY", steps=1)
print(result.restored)   # {"API_KEY": "<old-value>"}
print(result.skipped)    # keys that were protected

# Restore from checkpoint
result = rollback_to_checkpoint(secrets, "pre-rotation")
```
