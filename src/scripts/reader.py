import os
from dataclasses import dataclass
from typing import Iterator

@dataclass
class M2File:
    path: str
    content: str

def read_m2_files(root_dir: str, extensions=(".m2",)) -> Iterator[M2File]:
    """
    Recursively read all .m2 files under `root_dir`.
    Yields M2File objects.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if name.endswith(extensions):
                full_path = os.path.join(dirpath, name)
                rel_path = os.path.relpath(full_path, root_dir)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        yield M2File(path=rel_path, content=f.read())
                except Exception as e:
                    print(f"[WARN] Could not read {rel_path}: {e}")
