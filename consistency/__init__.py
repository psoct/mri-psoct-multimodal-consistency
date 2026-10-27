"""ROI-wise MRI–PS-OCT multimodal consistency analysis."""

from .io_utils import file_sha256, load_nifti, save_json, validate_image_grid
from .plotting import plot_roi_correlation
from .statistics import compute_correlations, summarize_regions

__all__ = [
    "compute_correlations",
    "file_sha256",
    "load_nifti",
    "plot_roi_correlation",
    "save_json",
    "summarize_regions",
    "validate_image_grid",
]

