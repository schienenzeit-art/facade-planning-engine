"""ODA File Converter adapter — converts DXF to DWG via subprocess.

ODA File Converter is a free tool from the Open Design Alliance:
  https://www.opendesign.com/guestfiles/oda_file_converter

Command syntax:
  ODAFileConverter <input_dir> <output_dir> <fmt> <version> <recursive> <audit>

Example (DXF R2013 → DWG 2018):
  ODAFileConverter /tmp/in /tmp/out DWG ACAD2018 0 1
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

from facade_planner.domain.exceptions import ExportError, OdaConverterNotFoundError


def _default_oda_path() -> Path:
    if sys.platform == "win32":
        return Path("C:/Program Files/ODA/ODAFileConverter/ODAFileConverter.exe")
    if sys.platform == "darwin":
        return Path(
            "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"
        )
    return Path("/usr/bin/ODAFileConverter")


class OdaConverterConfig(BaseModel):
    model_config = {"frozen": True}

    oda_path: Path = Path()  # overridden in __init_subclass__ below
    timeout_s: int = 60
    dwg_version: str = "ACAD2018"


class OdaConverterAdapter:
    """Wraps ODA File Converter as a subprocess to convert DXF → DWG."""

    def __init__(self, oda_path: Path | None = None, timeout_s: int = 60) -> None:
        self._oda_path = oda_path or _default_oda_path()
        self._timeout_s = timeout_s
        self._dwg_version = "ACAD2018"

    def convert(self, src_dxf: Path, dst_dwg: Path) -> None:
        """Convert *src_dxf* to *dst_dwg* (DWG ACAD2018).

        Raises:
            OdaConverterNotFoundError: binary not found at configured path.
            ExportError: conversion subprocess returned non-zero exit code.
        """
        if not self._oda_path.exists():
            raise OdaConverterNotFoundError(str(self._oda_path))

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_in = Path(tmpdir) / "in"
            tmp_out = Path(tmpdir) / "out"
            tmp_in.mkdir()
            tmp_out.mkdir()

            shutil.copy2(src_dxf, tmp_in / src_dxf.name)

            cmd = [
                str(self._oda_path),
                str(tmp_in),
                str(tmp_out),
                "DWG",
                self._dwg_version,
                "0",  # no recursion
                "1",  # audit output file
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
            )

            if proc.returncode != 0:
                raise ExportError(
                    f"ODA-Konvertierung fehlgeschlagen (exit {proc.returncode}):\n"
                    f"{proc.stderr.strip() or proc.stdout.strip()}"
                )

            dwg_files = list(tmp_out.glob("*.dwg"))
            if not dwg_files:
                raise ExportError(
                    "ODA File Converter hat keine .dwg-Datei erzeugt. "
                    "Prüfe die ODA-Logs im Ausgabeverzeichnis."
                )

            dst_dwg.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dwg_files[0], dst_dwg)
