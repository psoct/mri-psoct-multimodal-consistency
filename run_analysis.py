"""Run ROI-wise MRI–PS-OCT multimodal consistency analyses."""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
from pathlib import Path
import sys

import pandas as pd

from consistency import (
    compute_correlations,
    load_nifti,
    plot_roi_correlation,
    save_json,
    summarize_regions,
    validate_image_grid,
)


DEFAULT_SUBJECTS = ("sub-001", "sub-002", "sub-003")
DEFAULT_MODALITY_FILES = {
    "T2": "anat_2_ccf_100.nii.gz",
    "FA": "fa_2_ccf_100.nii",
    "Intensity": "inten_2_ccf_100.nii",
    "Retardance": "retar_2_ccf_100.nii",
}
DEFAULT_PAIRS = (
    ("T2", "Intensity"),
    ("T2", "Retardance"),
    ("FA", "Intensity"),
    ("FA", "Retardance"),
)


def parse_file_mapping(entries: list[str]) -> dict[str, str]:
    """Apply MODALITY=FILENAME overrides to the default file mapping."""
    mapping = dict(DEFAULT_MODALITY_FILES)
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Invalid --file entry: {entry!r}; expected MODALITY=FILENAME")
        modality, filename = entry.split("=", 1)
        if not modality or not filename:
            raise ValueError(f"Invalid --file entry: {entry!r}")
        mapping[modality] = filename
    return mapping


def parse_pair(entries: list[str]) -> tuple[tuple[str, str], ...]:
    """Parse FIRST:SECOND modality pairs."""
    if not entries:
        return DEFAULT_PAIRS
    pairs = []
    for entry in entries:
        parts = entry.split(":", 1)
        if len(parts) != 2 or not all(parts):
            raise ValueError(f"Invalid --pair entry: {entry!r}; expected FIRST:SECOND")
        pairs.append((parts[0], parts[1]))
    return tuple(pairs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--subjects", nargs="+", default=list(DEFAULT_SUBJECTS))
    parser.add_argument(
        "--data-subdir",
        default="s4_roi_analysis/ccf_space",
        help="Path below each subject directory containing registered images",
    )
    parser.add_argument("--label-file", default="FAAcoarse_100.nii")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="MODALITY=FILENAME",
        help="Override or add a modality file; may be repeated",
    )
    parser.add_argument(
        "--pair",
        action="append",
        default=[],
        metavar="FIRST:SECOND",
        help="Analyze a modality pair; may be repeated",
    )
    parser.add_argument("--min-vox", type=int, default=50)
    parser.add_argument("--aggregation", choices=("mean", "median"), default="mean")
    parser.add_argument("--dpi", type=int, default=600)
    return parser.parse_args()


def package_versions() -> dict[str, str]:
    packages = ("numpy", "pandas", "scipy", "matplotlib", "seaborn", "nibabel")
    return {name: importlib.metadata.version(name) for name in packages}


def analyze_pair(
    subject: str,
    first_name: str,
    second_name: str,
    arrays: dict[str, object],
    paths: dict[str, Path],
    output_root: Path,
    min_vox: int,
    aggregation: str,
    dpi: int,
) -> dict[str, object]:
    pair_name = f"{first_name}_{second_name}"
    destination = output_root / subject / pair_name
    destination.mkdir(parents=True)
    stem = f"{subject}_{pair_name}"

    summary = summarize_regions(
        arrays[first_name],
        arrays[second_name],
        arrays["labels"],
        min_vox=min_vox,
        aggregation=aggregation,
    )
    valid, statistics = compute_correlations(summary)
    summary = summary.loc[valid.index]

    csv_path = destination / f"roi_values_{stem}.csv"
    figure_prefix = destination / f"roi_scatter_{stem}"
    statistics_path = destination / f"stats_{stem}.json"
    summary.to_csv(csv_path, index=False)
    plot_roi_correlation(valid, statistics, figure_prefix, dpi=dpi)

    statistics.update(
        {
            "subject_id": subject,
            "modal_1": first_name,
            "modal_2": second_name,
            "aggregation": aggregation,
            "min_vox": min_vox,
            "input_files": {
                "modal_1": str(paths[first_name]),
                "modal_2": str(paths[second_name]),
                "labels": str(paths["labels"]),
            },
            "roi_table": str(csv_path),
            "figure_png": str(figure_prefix) + ".png",
            "figure_pdf": str(figure_prefix) + ".pdf",
        }
    )
    save_json(statistics, statistics_path)
    return statistics


def main() -> None:
    args = parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {args.output_dir}")

    modality_files = parse_file_mapping(args.file)
    pairs = parse_pair(args.pair)
    required_modalities = {name for pair in pairs for name in pair}
    unknown = sorted(required_modalities.difference(modality_files))
    if unknown:
        raise ValueError("Missing file mappings for: " + ", ".join(unknown))

    subject_inputs = {}
    manifest = []
    for subject in args.subjects:
        data_dir = args.data_root / subject / args.data_subdir
        paths = {name: data_dir / modality_files[name] for name in required_modalities}
        paths["labels"] = data_dir / args.label_file
        records = validate_image_grid(paths)
        manifest.extend({"subject": subject, **record} for record in records)
        subject_inputs[subject] = paths

    args.output_dir.mkdir(parents=True)
    save_json(manifest, args.output_dir / "input_manifest.json")
    save_json(
        {
            "python": sys.executable,
            "python_version": platform.python_version(),
            "package_versions": package_versions(),
            "argv": sys.argv,
        },
        args.output_dir / "environment.json",
    )

    all_statistics = []
    for subject, paths in subject_inputs.items():
        arrays = {name: load_nifti(path) for name, path in paths.items()}
        for first_name, second_name in pairs:
            result = analyze_pair(
                subject,
                first_name,
                second_name,
                arrays,
                paths,
                args.output_dir,
                args.min_vox,
                args.aggregation,
                args.dpi,
            )
            all_statistics.append(result)
            print(
                f"{subject} {first_name}–{second_name}: "
                f"n={result['n']}, r={result['pearson_r']:.4f}, "
                f"rho={result['spearman_rho']:.4f}",
                flush=True,
            )

    summary_columns = (
        "subject_id",
        "modal_1",
        "modal_2",
        "n",
        "pearson_r",
        "pearson_p",
        "spearman_rho",
        "spearman_p",
    )
    pd.DataFrame(all_statistics).loc[:, summary_columns].to_csv(
        args.output_dir / "correlation_summary.csv", index=False
    )


if __name__ == "__main__":
    main()

