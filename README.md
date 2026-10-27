# MRI–PS-OCT multimodal consistency

Reusable code for ROI-wise consistency analysis between MRI and PS-OCT
measurements in a shared atlas space.

The default analysis includes three consecutively numbered subjects
(`sub-001`, `sub-002`, and `sub-003`) and four modality pairs:

- T2–Intensity
- T2–Retardance
- FA–Intensity
- FA–Retardance

Both the subject list and the modality-to-file mapping can be changed from the
command line without editing the source code.

## Expected input layout

```text
DATA_ROOT/
├── sub-001/s4_roi_analysis/ccf_space/
│   ├── anat_2_ccf_100.nii.gz
│   ├── fa_2_ccf_100.nii
│   ├── inten_2_ccf_100.nii
│   ├── retar_2_ccf_100.nii
│   └── FAAcoarse_100.nii
├── sub-002/...
└── sub-003/...
```

The input images are not distributed with this code repository. The associated
data record is being prepared on Zenodo under the reserved DOI
[10.5281/zenodo.23530831](https://doi.org/10.5281/zenodo.23530831). The files
will become accessible through the DOI after the Zenodo record is published.

All images belonging to a subject must have the same array shape and affine.
The atlas image must contain integer region identifiers; label 0 is treated as
background.

## Installation

The code has been tested on Linux with Python 3.10.16. The exact package
versions used for testing are recorded in `requirements.txt`:

- NumPy 1.23.5
- pandas 1.5.3
- SciPy 1.15.2
- Matplotlib 3.10.1
- seaborn 0.13.2
- NiBabel 5.3.2

A clean Conda environment can be created as follows:

```bash
conda create --name mri-psoct-consistency python=3.10
conda activate mri-psoct-consistency
python -m pip install -r requirements.txt
```

## Usage

```bash
bash run_analysis.sh \
  --data-root /path/to/psoct/results \
  --output-dir /path/to/output
```

To provide a different subject list:

```bash
bash run_analysis.sh \
  --data-root /path/to/psoct/results \
  --output-dir /path/to/output \
  --subjects sample-a sample-b sample-c
```

Use `python run_analysis.py --help` for all options. The output directory must
not already exist.

## Statistical procedure

For every atlas region, paired finite voxels are selected and summarized with
the arithmetic mean (or median when requested). Regions below `--min-vox` are
excluded. Pearson and Spearman correlations are then calculated across the
retained atlas regions. No normalization or outlier exclusion is performed.

The generated p-values describe an ROI-wise association. Atlas regions are
spatially related and should not be interpreted as independent biological
replicates.

## Outputs

Each subject/pair directory contains:

- ROI-level values as CSV
- correlation statistics as JSON
- a scatter plot as PNG and PDF

The output root also contains a combined correlation table, an input manifest
with file hashes and image geometry, and the software environment metadata.

## Acknowledgements

This repository builds on the original analysis and core code contributions of
[Winston Jiang](https://github.com/winston1716).

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE)
for the full terms.

