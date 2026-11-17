# Entry point for building the standalone "canvasdl" executable with PyInstaller
# (used by .github/workflows/release.yml). canvas_downloader/__main__.py can't be
# used for this because PyInstaller runs it as a plain script, where the relative
# import "from .cli import main" doesn't work.
import sys

from canvas_downloader.cli import main

sys.exit(main())
