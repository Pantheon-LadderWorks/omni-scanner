# 🏁 Omni Beginner's Guide: Zero to Hero

Welcome to the **Federation**. You are about to install **Omni**, the "All-Seeing Eye" governance engine. 

Omni is designed to be modular. It doesn't modify your code; it observes it. This guide will walk you through setting up the passive observation engine on your local machine.

---

## 📋 Prerequisites

Before you start, ensure you have:
- **Python 3.10** or higher installed (`python --version`)
- **Git** installed (`git --version`)
- A terminal (PowerShell, Bash, or Zsh)

---

## 🚀 Step-by-Step Installation

### 0. The Easy Way (PyPI)
If you just want to use Omni without modifying the code, you can install it directly from PyPI. This is the **recommended** path for most users:

```bash
pip install omni-governance
```
That's it! You can skip directly to **Step 4. Verify Installation**.

If you want to modify the code or contribute to Omni, follow the source installation steps below.

### 1. Clone the Repository
Get the code onto your machine.

```bash
git clone https://github.com/Kryssie6985/Infrastructure.git omni
cd omni/tools/omni
```
*(Note: Adjust the path if you downloaded the standalone zip)*

### 2. The Configuration Dance 💃
**CRITICAL STEP**: Omni comes with "templates" instead of active configuration files. You must activate them.

#### A. Activate the Project Definition
The file `pyproject.toml.template` contains the build instructions.
1. Locate `pyproject.toml.template` in the root.
2. Rename it to `pyproject.toml`.

```bash
# Windows (PowerShell)
Rename-Item pyproject.toml.template pyproject.toml

# Linux/Mac
mv pyproject.toml.template pyproject.toml
```

#### B. Activate the Settings
The file `omni/config/settings_template.py` controls how Omni behaves.
1. Navigate to `omni/config/`.
2. Rename `settings_template.py` to `settings.py`.

```bash
# Windows (PowerShell)
Rename-Item omni/config/settings_template.py omni/config/settings.py

# Linux/Mac
mv omni/config/settings_template.py omni/config/settings.py
```

> **Why?** We do this so your personal settings (like API keys or local paths) are never accidentally committed back to the public repository. These files are ignored by Git.

### 3. Install Omni
Now that the configuration is active, install Omni in "editable" mode. This allows you to modify the code and see changes immediately.

```bash
# From the root 'omni' directory (where pyproject.toml is)
pip install -e .
```

### 4. Verify Installation ✅
Let's confirm everything is working.

#### Check 1: The Introspection
Ask Omni what it sees about itself.
```bash
omni introspect
```
**Success:** You should see a JSON output listing ~55 scanners across 12 categories.

#### Check 2: The First Scan
Scan the current directory.
```bash
omni scan .
```
**Success:** You should see a JSON output describing the files in the current folder.

---

## 🔧 Basic Configuration

By default, Omni scans everything except `node_modules`, `.git`, and `__pycache__`.

To customize settings (like adding more exclude patterns):
1. Open `omni/config/settings.py`.
2. Edit the `OmniSettings` class.

For advanced configuration (Environment variables, Federation connection, etc.), see the **[Configuration Guide](../omni/config/README.md)**.

---

## 🆘 Troubleshooting

**"File not found: pyproject.toml"**
> You missed Step 2A. Rename `pyproject.toml.template` to `pyproject.toml`.

**"ModuleNotFoundError: No module named 'omni.config.settings'"**
> You missed Step 2B. Rename `omni/config/settings_template.py` to `settings.py`.

**"pip: command not found"**
> Ensure Python is added to your system PATH.

---

Welcome to the All-Seeing Eye. 👁️
