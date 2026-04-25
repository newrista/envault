# envault

> A CLI tool to securely manage and rotate environment variables across multiple projects using encrypted local vaults.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

Initialize a new vault for your project:

```bash
envault init my-project
```

Add and retrieve environment variables:

```bash
# Store a secret
envault set my-project DATABASE_URL "postgres://user:pass@localhost/db"

# Retrieve a secret
envault get my-project DATABASE_URL

# List all variables in a vault
envault list my-project

# Rotate a secret
envault rotate my-project DATABASE_URL "postgres://user:newpass@localhost/db"

# Export variables to your shell
eval $(envault export my-project)
```

Vaults are AES-256 encrypted and stored locally at `~/.envault/`.

---

## Features

- 🔐 AES-256 encrypted local vaults
- 🔄 Secret rotation with history tracking
- 📁 Multi-project support
- 🐚 Shell export for seamless integration
- 🔑 Master password or key-file authentication

---

## License

This project is licensed under the [MIT License](LICENSE).