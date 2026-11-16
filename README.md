# canvas-file-downloader (canvasdl)

canvasdl is a powerful, multi-threaded Python tool to automate downloading and organizing files from your Canvas LMS.

## Features
* **Multi-threaded Downloading**: Fast, parallel downloading to save time.
* **Smart File Tracking**: Uses a local tracking file (`.downloaded_files`) and performs byte-level comparison to detect updated files and save them as new versions, avoiding redundant downloads.
* **Auto-Categorization**: Optionally sorts downloaded files into specific directories (e.g., *Clase*, *Ayudantías*, *Apuntes*) based on file name keywords.
* **Flexible Filtering**: Whitelist or blacklist specific courses, terms, or file extensions.
* **CLI & JSON Configuration**: Easily configure the tool globally via a JSON file or override settings per-run using command-line arguments.


## Setup
1. **Get your Canvas API Token**:
   * Log into your Canvas account.
   * Go to **Account** -> **Settings**.
   * Scroll down to **Approved Integrations** and click **+ New Access Token**.
   * Copy the generated token.
