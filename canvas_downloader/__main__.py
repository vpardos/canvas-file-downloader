# lets "python -m canvas_downloader" work the same as the "canvasdl" command
import sys

from .cli import main

sys.exit(main())
