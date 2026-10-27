"""Input/output helpers for NIfTI-based analyses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import nibabel as nib
import numpy as np


def file_sha256(path: str | Path, block_size: int = 8 * 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def load_nifti(path: str | Path) -> np.ndarray:
    """Load a NIfTI image as a float32 NumPy array."""
    return nib.load(str(path)).get_fdata(dtype=np.float32)


def validate_image_grid(paths: Mapping[str, str | Path]) -> list[dict[str, Any]]:
    """Ensure all images share one voxel grid and return provenance records."""
    if not paths:
        raise ValueError("No image paths were supplied")

    normalized = {name: Path(path) for name, path in paths.items()}
    missing = [str(path) for path in normalized.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing input file(s):\n" + "\n".join(missing))

    images = {name: nib.load(str(path)) for name, path in normalized.items()}
    reference_name = "labels" if "labels" in images else next(iter(images))
    reference = images[reference_name]
    records = []

    for name, image in images.items():
        if image.shape != reference.shape or not np.allclose(image.affine, reference.affine):
            raise ValueError(
                f"Image grid mismatch for {name}: {normalized[name]} "
                f"(reference: {reference_name})"
            )
        records.append(
            {
                "modality": name,
                "path": str(normalized[name].resolve()),
                "sha256": file_sha256(normalized[name]),
                "shape": list(image.shape),
                "affine": image.affine.tolist(),
                "orientation": "".join(nib.aff2axcodes(image.affine)),
            }
        )
    return records


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def save_json(data: Any, path: str | Path) -> None:
    """Write Python and NumPy values as readable UTF-8 JSON."""
    Path(path).write_text(
        json.dumps(_to_jsonable(data), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

