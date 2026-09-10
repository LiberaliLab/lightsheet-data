# lightsheet-data

Python client for the reference light-sheet microscopy OME-Zarr datasets published on
Zenodo: https://zenodo.org/records/22078388 (DOI `10.5281/zenodo.22078387`).

Install (importable module is `lsdata`):

```bash
pip install lightsheet-data
```

## Usage

```python
import lsdata

lsdata.info()                            # list available datasets: name, size (GB), description
p = lsdata.download('001-mini', 'v0.1')  # download dataset to local cache, return path
```

`download()` skips the network entirely if the dataset was already downloaded and
extracted in a previous call. `version` defaults to the latest published version if
omitted.

A CLI is also available:

```bash
lsdata info
lsdata download 001-mini --version v0.1
```

## Cache location

Datasets are cached under the platform's standard user cache directory (e.g.
`%LOCALAPPDATA%\lsdata\Cache` on Windows, `~/.cache/lsdata` on Linux). Set the
`LSDATA_CACHE_DIR` environment variable to use a different location — useful for:

- pointing large datasets (e.g. `001-full`, ~40GB) at a disk with more free space
- avoiding Windows `MAX_PATH` issues, since extracted OME-Zarr chunk trees nest
  deeply and a long cache path can push individual file paths past 260 characters

Downloading a dataset temporarily uses up to ~2x its size on disk (the zip archive
plus the extracted copy); the archive is deleted once extraction succeeds.
