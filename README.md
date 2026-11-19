# canvas-file-downloader (canvasdl)

`canvasdl` is a command-line tool that downloads the files of your Canvas LMS courses to your computer, keeping the same folder structure they have on Canvas. It can clone whole semesters or single courses, downloads in parallel, and only downloads what changed when you run it again.

```bash
canvasdl show semesters          # find your semester IDs
canvasdl clone -s 120            # download every course of that semester
```

## Features

* **Clone semesters or single courses**: `-s` for whole semesters (each in its own folder), `-c` for single courses, or both in one run.
* **Same folders as Canvas**: every Canvas folder, including empty and nested ones, is recreated on your computer.
* **Incremental**: running the same command again only downloads new or changed files (see [How canvasdl knows a file is already downloaded](#how-canvasdl-knows-a-file-is-already-downloaded)).
* **Parallel downloads**: up to 8 files at once, shared across all the courses being cloned.
* **Finds past courses too**: lists every course you were ever enrolled in, not only the current ones.
* **Secure token storage**: your API token is kept in your operating system's password store, and is never typed visibly or saved in your shell history.
* **Works on Ubuntu, Windows and macOS**: file names are cleaned so they're valid on every system.

## Requirements

* A Canvas account and an API token (see [Setup](#setup))
* One of:
  * **Nothing else**, if you download the ready-made program: Windows 10/11 (64-bit), macOS on Apple Silicon (M1 or newer), or 64-bit Linux / WSL (Ubuntu 22.04 or newer, or any distribution with glibc 2.35+)
  * **Python 3.8+ and pipx**, on any system (including Intel Macs)

## Installation

### Option 1: download the program (no Python needed)

Get the file for your system from the [latest release](https://github.com/vpardos/canvas-file-downloader/releases/latest):

| System | File |
|---|---|
| Windows | `canvasdl-windows-x64.exe` |
| macOS (Apple Silicon) | `canvasdl-macos-arm64` |
| Linux / WSL | `canvasdl-linux-x64` |

**Linux / WSL**: download it straight into a folder that's on your `PATH`:

```bash
mkdir -p ~/.local/bin
curl -L -o ~/.local/bin/canvasdl https://github.com/vpardos/canvas-file-downloader/releases/latest/download/canvasdl-linux-x64
chmod +x ~/.local/bin/canvasdl
```

If `canvasdl` isn't found afterwards, open a new terminal (Ubuntu adds `~/.local/bin` to the `PATH` at login once the folder exists).

**macOS (Apple Silicon)**:

```bash
curl -L -o canvasdl https://github.com/vpardos/canvas-file-downloader/releases/latest/download/canvasdl-macos-arm64
chmod +x canvasdl
sudo mkdir -p /usr/local/bin && sudo mv canvasdl /usr/local/bin/
```

If you downloaded it with the browser instead, macOS blocks it because it isn't signed by Apple. Allow it once with `xattr -d com.apple.quarantine canvasdl`, or right-click it in Finder → **Open**.

**Windows** (Windows 10 and 11 include `curl`):

1. Download it into a `bin` folder inside your user folder, already named `canvasdl.exe`.

   In **Command Prompt**:
   ```bat
   mkdir %USERPROFILE%\bin
   curl -L -o %USERPROFILE%\bin\canvasdl.exe https://github.com/vpardos/canvas-file-downloader/releases/latest/download/canvasdl-windows-x64.exe
   ```
   If the folder already exists, `mkdir` says so; that's fine.

   In **PowerShell**:
   ```powershell
   mkdir -Force $env:USERPROFILE\bin
   curl.exe -L -o $env:USERPROFILE\bin\canvasdl.exe https://github.com/vpardos/canvas-file-downloader/releases/latest/download/canvasdl-windows-x64.exe
   ```
2. Add that folder to your `PATH` (only once): open **Start**, search **"Edit environment variables for your account"**, select **Path** → **Edit** → **New**, type `%USERPROFILE%\bin`, and press **OK** in both windows.
3. Open a **new** Command Prompt or PowerShell window (one that was already open doesn't see the change; in Windows Terminal, close every window) and run `canvasdl --version`.

If you'd rather use the browser: download `canvasdl-windows-x64.exe` from the release page, move it to that folder and rename it to `canvasdl.exe`. If Explorer hides file extensions, type only `canvasdl` when renaming; typing `canvasdl.exe` would make it `canvasdl.exe.exe`. Files downloaded with the browser may show **"Windows protected your PC"** the first time, because the program isn't signed: click **More info** → **Run anyway**, or run `Unblock-File canvasdl.exe` in PowerShell in that folder.

**To update**, run the same download command again: the `curl` line on Linux / WSL, all three macOS commands, or on Windows the `curl` (Command Prompt) or `curl.exe` (PowerShell) line. It downloads the latest release over the old file; check with `canvasdl --version`. If you used the browser, download the new file and replace the old one the same way. On WSL, the Linux and Windows programs are separate, so update each one you use.

### Option 2: install with pipx (needs Python)

[pipx](https://pipx.pypa.io/) installs `canvasdl` in its own isolated environment and makes the command available in every terminal. Install pipx once:

| System | Command |
|---|---|
| Ubuntu / WSL | `sudo apt install pipx && pipx ensurepath` |
| macOS | `brew install pipx && pipx ensurepath` |
| Windows | `py -m pip install --user pipx` then `py -m pipx ensurepath` |

Open a new terminal, then install `canvasdl` (Git is not needed):

```bash
pipx install https://github.com/vpardos/canvas-file-downloader/archive/refs/heads/main.zip
```

To update to the latest version, run the same command with `--force`.

### For development

Install it in editable mode inside a virtual environment, so your code changes apply immediately:

```bash
git clone https://github.com/vpardos/canvas-file-downloader.git
cd canvas-file-downloader
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

The `canvasdl` command is available while the virtual environment is active, from any folder. Run `pip install -e .` again only after changing `pyproject.toml`.

### Releasing a new version

The downloadable programs are built by GitHub Actions (`.github/workflows/release.yml`):

1. Set the new version in `canvas_downloader/__init__.py` (e.g. `__version__ = "2.0.0"`) and merge it into `main`.
2. Tag that commit and push the tag:
   ```bash
   git switch main && git pull
   git tag v2.0.0 && git push origin v2.0.0
   ```
3. The workflow builds `canvasdl` for Windows, macOS and Linux (a few minutes) and publishes them as a GitHub Release with notes listing the merged pull requests. If the tag doesn't match `__version__`, it stops without publishing.

To test the build without releasing anything, open **Actions → Release → Run workflow**; the executables can then be downloaded from that run's page.

## Setup

You need to do this once.

### 1. Get your Canvas API token

1. Log into your Canvas account.
2. Go to **Account** → **Settings**.
3. Scroll down to **Approved Integrations** and click **+ New Access Token**.
4. Copy the generated token.

### 2. Save the token

```bash
canvasdl token set
```

Paste the token when asked. Nothing appears while you type or paste; that's intentional, so the token isn't visible on screen. See [Where your token and settings are stored](#where-your-token-and-settings-are-stored).

On Windows, in **Command Prompt** Ctrl+V doesn't paste at this prompt: click the icon in the window's top-left corner → **Edit** → **Paste** instead, then press Enter. In **Windows Terminal**, Ctrl+V works normally.

### 3. Save your Canvas domain

This is the address you use to open Canvas in your browser:

```bash
canvasdl domain set https://yourschool.instructure.com
```

`https://` is added automatically if you leave it out. You can also paste any Canvas link (e.g. `https://yourschool.instructure.com/courses/123`); only the address part is kept.

## Usage

### Find semester and course IDs

```bash
canvasdl show semesters
```

```
   120  Fall 2026
   115  Spring 2026
   110  Fall 2025
```

```bash
canvasdl show courses              # all courses, grouped by semester
canvasdl show courses -s 120       # only one semester
canvasdl show courses -s 120 115   # several semesters
```

```
Fall 2026 (semester ID 120)
   54321  CS201-1  Data Structures
   54322  CS202-1  Databases
```

The first column is the course ID.

### Clone

`canvasdl clone` downloads into the folder you run it from, so `cd` to where you want the files first.

```bash
cd ~/Documents/canvas

canvasdl clone -s 120                 # one semester
canvasdl clone -s 120 115             # several semesters
canvasdl clone -c 54321 54322         # single courses
canvasdl clone -s 120 -c 43210        # semesters and courses together
```

At least one of `-s` or `-c` is required; `canvasdl clone` on its own does nothing and shows an error.

Resulting folders:

```
~/Documents/canvas/
├── Fall_2026/                    ← from -s: one folder per semester
│   ├── CS201-1/                  ← one folder per course (its course code)
│   │   ├── Lectures/
│   │   │   └── Lecture 1.pdf     ← same folders as on Canvas
│   │   └── Syllabus.pdf
│   └── CS202-1/
└── MATH101-1/                    ← from -c: the course folder, right here
```

While it runs, `canvasdl` prints each file as it finishes and a summary per course at the end:

```
Done:
  Fall_2026/CS201-1: 12 downloaded, 30 already up to date, 0 locked, 0 failed
  Fall_2026/CS202-1: 0 downloaded, 8 already up to date, 0 locked, 0 failed

2 of 2 courses cloned
```

### All commands

| Command | What it does |
|---|---|
| `canvasdl token set` | Save your Canvas API token (asks for it, hidden input) |
| `canvasdl token delete` | Delete the saved token |
| `canvasdl domain set DOMAIN` | Save your Canvas address, e.g. `https://yourschool.instructure.com` |
| `canvasdl show semesters` | List your semesters and their IDs |
| `canvasdl show courses [-s ID ...]` | List your courses grouped by semester, optionally only some semesters |
| `canvasdl clone -s ID ...` | Clone every course of these semesters, each semester in its own folder |
| `canvasdl clone -c ID ...` | Clone these courses into the current folder |
| `canvasdl --version` | Show the installed version |

Add `-h` to any command for its help, e.g. `canvasdl clone -h`.

## How it works

### Where your token and settings are stored

**The API token** is saved in your operating system's password store, which is encrypted with your login:

| System | Password store |
|---|---|
| Windows | Credential Manager |
| macOS | Keychain |
| Ubuntu (desktop) | GNOME Keyring / Secret Service |

If no password store is available (common on WSL and servers), the token is saved instead in a `credentials.json` file in the config folder below, with permissions set so only your user can read it (`600`).

**The Canvas domain** is saved in `config.json` in the config folder:

| System | Config folder |
|---|---|
| Linux / WSL | `~/.config/canvasdl/` (or `$XDG_CONFIG_HOME/canvasdl/`) |
| macOS | `~/Library/Application Support/canvasdl/` |
| Windows | `%APPDATA%\canvasdl\` |

Running `canvasdl token set` or `canvasdl domain set` again replaces the previous value.

### Which courses are found

Canvas's normal "list my courses" request only returns current courses and hides most past ones. `canvasdl` instead starts from your **enrollments** (current and finished), then fetches each course with its semester. That's why `show courses` also lists courses from past semesters. Those requests run in parallel, so it takes a couple of seconds.

### How the folders are built

* Each course folder is named after its **course code** (e.g. `CS201-1`).
* Each semester folder is the **semester name with underscores** instead of spaces (e.g. `Fall 2026` → `Fall_2026`).
* Inside a course, the Canvas folder tree is recreated. Canvas's root folder (`course files`) is the course folder itself.
* Characters that Windows doesn't allow in names (`< > : " / \ | ? *`) are replaced with `_`, and trailing dots and spaces are removed, so `Lecture 1: Intro.pdf` is saved as `Lecture 1_ Intro.pdf`. This keeps the same command working on every system.

### How canvasdl knows a file is already downloaded

There is no database or tracking file. For each file, `canvasdl` compares the file on your disk with the information Canvas reports about it:

1. **No file with that name in that folder** → it's downloaded.
2. **A file exists and its size in bytes is exactly the size Canvas reports** → it's considered up to date and skipped.
3. **A file exists but its size is different** → the file changed on Canvas (or locally), so it's downloaded again and **replaces** the local copy.

This makes re-running a clone fast: only new and changed files are downloaded. It also means:

* ⚠️ **Local edits are overwritten.** If you annotate or edit a downloaded file, its size changes, and the next clone replaces it with the Canvas version. Copy files somewhere else before editing them.
* **A file updated on Canvas that keeps exactly the same size is not re-downloaded.** This is rare (most edits change the size), but possible.
* **Files deleted or renamed on Canvas are not deleted locally.** A renamed file is downloaded under its new name and the old copy stays.
* Moving or renaming the cloned folders makes `canvasdl` treat everything as new, because it looks for files at the same paths as on Canvas.

### Parallel downloads

Cloning happens in two steps:

1. The folder and file lists of **every** course are fetched at the same time, and the folders are created.
2. All files of all courses go into **one shared queue** that downloads up to **8 files at once**.

Sharing one queue means cloning several semesters never sends more than 8 downloads to Canvas at the same time, which keeps you well below Canvas's rate limit. The limit is `MAX_WORKERS` in `canvas_downloader/canvas.py`; lower it if you ever see `Rate Limit Exceeded` errors.

Files are streamed to disk in 64 KB pieces, so large files (like recorded lectures) don't use much memory.

### Interrupted downloads

Each file is first written as `<name>.part` and only renamed to its real name once it's complete, so a half-downloaded file never looks finished. If a download fails, the `.part` file is removed.

Pressing **Ctrl+C** cancels the files that haven't started yet and waits for the ones in progress (at most 8) to finish, then exits with `Cancelled.`. Run the same command again to continue: everything already downloaded is skipped.

### Skipped courses and locked files

* **Courses whose files you can't access** (Canvas answers `403 Forbidden`, usually because the course ended and the school closed file access, or the course hides its Files section) are skipped with the reason, and the other courses continue.
* **Locked files** (not yet available, or restricted by the teacher) are not downloaded and are counted as `locked` in the summary.
* **A file that fails to download** is shown as `FAILED` with the reason; the rest continue. Running the command again retries it.
* **Repeated IDs** (`-s 120 120`) are only cloned once. A course given with `-c` that's also in a `-s` semester is cloned in both places.
* **An unknown semester ID** stops the command before anything is downloaded, so a typo never starts a partial clone.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (some courses may have been skipped) |
| `1` | Error: no token or domain saved, wrong token, no connection, unknown semester, nothing could be cloned, or a file/folder couldn't be written |
| `2` | Wrong usage, e.g. `canvasdl clone` without `-s` or `-c` |
| `130` | Cancelled with Ctrl+C |

## Troubleshooting

| Message | Fix |
|---|---|
| `No token saved` | Run `canvasdl token set` |
| `No Canvas domain configured` | Run `canvasdl domain set https://your-canvas-address` |
| `Canvas rejected your token (HTTP 401)` | The token is wrong or expired: create a new one in Canvas and run `canvasdl token set` |
| `That doesn't look like a Canvas token` | What was pasted isn't a token (often Ctrl+V in Command Prompt, which doesn't paste there): see [Save the token](#2-save-the-token) |
| `Canvas rejected the request (HTTP 400)` | The saved token is damaged: run `canvasdl token delete`, then `canvasdl token set` and paste as described in [Save the token](#2-save-the-token) |
| `Couldn't connect to Canvas` | Check your internet connection, and that your domain is right (`canvasdl domain set`) |
| `Not found on Canvas (HTTP 404)` | Your domain probably isn't your Canvas address: run `canvasdl domain set` again |
| `Canvas is limiting your requests (rate limit)` | Wait a minute and run the command again; already downloaded files are skipped |
| `Canvas doesn't allow access to the files of ... (HTTP 403)` | Canvas doesn't let you download that course's files; nothing to fix on your side |
| `... config.json is damaged` / `... credentials.json is damaged` | The file was edited by hand and isn't valid JSON: fix it, or delete it and run `canvasdl domain set` / `canvasdl token set` again |
| `Couldn't create the folders of ...` / `File error: ...` | No permission to write there, or the disk is full: `cd` to a folder you own |
| `Windows protected your PC` / macOS says `canvasdl` can't be opened | The downloaded program isn't signed: see [Option 1](#option-1-download-the-program-no-python-needed) for how to allow it |
| `Permission denied` when running the downloaded program (Linux / macOS) | Make it executable: `chmod +x canvasdl` |
| `'canvasdl' is not recognized as an internal or external command` (Windows) | The file must be named exactly `canvasdl.exe` and be in a folder listed in your `PATH`; then open a new terminal. See [Option 1](#option-1-download-the-program-no-python-needed) |
| `canvasdl: command not found` | Activate the virtual environment (`source .venv/bin/activate`) or install with pipx |

## License

[MIT](LICENSE): you can use, modify and share this project freely, as long as you keep the copyright notice.
