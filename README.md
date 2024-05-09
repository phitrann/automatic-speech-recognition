# Automatic Speech Recognition

## Dependencies
```bash
    sudo apt-get install ffmpeg
    cd <PATH_TO_UNQLIB_DIR>

    # Install in editable mode to avoid constant re-installation
    # Also include all optional dependencies
    python -m pip install -e .[all]

    # Install pre-commit hooks to automatically check/format code on commits
    pre-commit install
```



## Guidelines
Youtube API is free, just have quota limit: https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Understanding-YouTube-API-Quota-Limits

### Collect data
```bash
   python /src/asr/download_data.py
```

### Clean up data
```bash
    ./clean_up.sh
```
