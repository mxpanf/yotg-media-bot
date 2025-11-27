"""
Temporary storage manager backed by tmpfs (/dev/shm).
Provides per-job directories and cleanup helpers.
"""

from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Storage:
    base_dir: Path

    def ensure(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_job_dir(self, prefix: str = "job") -> Path:
        self.ensure()
        job_dir = self.base_dir / f"{prefix}_{uuid.uuid4().hex}"
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def cleanup(self, path: Path) -> None:
        if not path.exists():
            return
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)

    @contextmanager
    def job_scope(self, prefix: str = "job") -> Iterator[Path]:
        job_dir = self.create_job_dir(prefix)
        try:
            yield job_dir
        finally:
            self.cleanup(job_dir)
