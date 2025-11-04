# Splurge Pub-Sub - CLI Reference

Command-line interface reference for the Splurge Pub-Sub framework.

## Overview

The Splurge Pub-Sub CLI provides package metadata and information access via command-line. It can be invoked using:

```bash
python -m splurge_pub_sub [OPTIONS] [COMMAND]
```

or

```bash
splurge-pub-sub [OPTIONS] [COMMAND]
```

(if installed with CLI entry point)

## Global Options

### --version

Print the installed version of splurge-pub-sub and exit.

**Syntax**:
```bash
python -m splurge_pub_sub --version
```

**Output**:
```
splurge-pub-sub 2025.0.0
```

**Exit Code**: 0 (success)

### --help

Print help message showing available commands and options.

**Syntax**:
```bash
python -m splurge_pub_sub --help
```

**Output**:
```
usage: splurge-pub-sub [-h] [--version]

Splurge Pub-Sub - Python pub-sub framework

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

**Exit Code**: 0 (success)

## Commands

Currently, the CLI supports the following:

### No Command (Default)

Running without a command or with `--help` displays the help message.

**Syntax**:
```bash
python -m splurge_pub_sub
```

**Output**: Displays help message

**Exit Code**: 0 (success)

## Environment Variables

The CLI does not currently use environment variables. All configuration is provided via command-line arguments.

**Future Environment Variables** (for planning):
- `SPLURGE_PUB_SUB_*` - Reserved prefix for framework environment variables
- `SPLURGE_PUB_SUB_DEBUG` - Enable debug mode (future)
- `SPLURGE_PUB_SUB_CONFIG` - Configuration file path (future)

## Exit Codes

- **0** - Success
- **1** - Generic error
- **2** - Invalid arguments/syntax error
- **130** - Interrupted (Ctrl+C)

## Examples

### Display Version

```bash
$ python -m splurge_pub_sub --version
splurge-pub-sub 2025.0.0
```

### Display Help

```bash
$ python -m splurge_pub_sub --help
usage: splurge-pub-sub [-h] [--version]

Splurge Pub-Sub - Python pub-sub framework

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

### Run without Arguments

```bash
$ python -m splurge_pub_sub
usage: splurge-pub-sub [-h] [--version]

Splurge Pub-Sub - Python pub-sub framework

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

## Usage in Scripts

### Get Version Programmatically

```python
import subprocess
import sys

# Get version via CLI
result = subprocess.run(
    [sys.executable, "-m", "splurge_pub_sub", "--version"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    version = result.stdout.strip()
    print(f"Installed version: {version}")
```

### Get Version from Python

```python
from splurge_pub_sub import __version__

print(f"Installed version: {__version__}")
```

## Python API Alternative

While the CLI provides limited functionality, the Python API offers comprehensive access:

```python
from splurge_pub_sub import PubSub, Message, __version__

# Get version
print(f"Version: {__version__}")

# Create and use pub-sub bus
bus = PubSub()

@bus.on("event.topic")
def handle_event(msg: Message) -> None:
    print(f"Received: {msg.data}")

bus.publish("event.topic", {"data": "value"})
```

## Future CLI Features

The CLI is intentionally lightweight in Phase 1. Future enhancements may include:

- **Server Mode**: Run pub-sub bus as a server
- **Configuration**: Load settings from config files
- **Debugging**: Debug mode with detailed logging
- **Inspection**: Inspect subscription registry
- **Testing**: Test mode for development
- **Metrics**: Display performance metrics
- **REPL**: Interactive shell for testing

## Related Documentation

- **[API-REFERENCE.md](../api/API-REFERENCE.md)** - Complete API reference
- **[README-DETAILS.md](../README-DETAILS.md)** - Developer's guide
- **[README.md](../../README.md)** - Project overview
- **[CHANGELOG.md](../../CHANGELOG.md)** - Version history

## Support

For issues or questions about the CLI, see the main README or visit the [GitHub repository](https://github.com/jim-schilling/splurge-pub-sub).
