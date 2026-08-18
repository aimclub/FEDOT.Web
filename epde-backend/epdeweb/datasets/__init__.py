"""Field data: the input an equation search works on.

FEDOT reads a table with a target column. EPDE reads a *field* -- one or more
variables sampled on a grid, plus the coordinates of that grid -- because the
derivatives it takes are with respect to those coordinates. The grid is not
metadata here; it is half the input, and getting it wrong silently rescales
every derivative and therefore every coefficient in the discovered equation.
"""

from .fields import (
    FieldDataset,
    axis_from_vector,
    describe_axes,
    load_field_file,
    read_dataset,
    write_dataset,
)
from .samples import SAMPLES, build_sample
from .service import DatasetError, DatasetService

__all__ = [
    "SAMPLES",
    "DatasetError",
    "DatasetService",
    "FieldDataset",
    "axis_from_vector",
    "build_sample",
    "describe_axes",
    "load_field_file",
    "read_dataset",
    "write_dataset",
]
