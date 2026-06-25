# AutoBackupAJM
### Automated backup on a chosen schedule

`AutoBackupAJM` is a Python utility designed to simplify and automate the backup process for files and directories. It allows you to schedule backups on a daily, weekly, or monthly basis and intelligently checks if a backup is necessary based on file changes.

## Features

- **Scheduled Backups**: Support for daily, weekly, and monthly backup frequencies.
- **Change Detection**: Uses hashing to determine if the source has changed since the last backup, avoiding redundant copies.
- **Large File Support**: Specialized hashers for handling large files efficiently.
- **Directory Hashing**: Ability to hash entire directories to detect changes within any file.
- **Interactive Prompts**: Uses `questionary` for user-friendly directory creation prompts.
- **Customizable**: Configure backup names, locations, and logging.

## Installation

You can install the dependencies using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

To install the package in editable mode:

```bash
pip install -e .
```

## Usage

### AutoBackup

The main class `AutoBackup` handles the logic for scheduling and executing backups.

```python
from AutoBackupAJM.auto_backup_ajm import AutoBackup
from pathlib import Path

# Initialize AutoBackup
backup_manager = AutoBackup(
    source_path="path/to/your/source_file.txt",
    backup_dir_path_root="path/to/backup/folder",
    backup_frequency="daily", # 'daily', 'weekly', or 'monthly'
    backup_name="my_backup.txt"
)

# Run the backup process
if backup_manager.due_for_backup():
    if backup_manager.source_changed_since_last_backup():
        backup_manager.backup()
        print("Backup completed successfully.")
    else:
        print("No changes detected since last backup.")
else:
    print("Not due for backup yet.")
```

### Hashers

The `Hasher` module can be used independently to calculate MD5 hashes for files and directories.

#### File Hashing
```python
from AutoBackupAJM.Hasher.file_hashers import FileHasher
from pathlib import Path

hasher = FileHasher("path/to/file.txt")
path, file_hash = hasher.hash_file()
print(f"MD5 Hash: {file_hash}")
```

#### Directory Hashing
```python
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher

dir_hasher = DirectoryHasher("path/to/directory")
for path, file_hash in dir_hasher.hash_directory():
    print(f"File: {path}, Hash: {file_hash}")
```

#### Large File Hashing
For very large files, use `LargeFileHasher` which defaults to a larger buffer size (1GB).
```python
from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher

large_hasher = LargeFileHasher("path/to/large_file.zip")
path, file_hash = large_hasher.hash_file()
```

## Requirements

- Python 3.x
- `questionary`

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details.

## Author

**Amcsparron** - [amcsparron@albanyny.gov](mailto:amcsparron@albanyny.gov)