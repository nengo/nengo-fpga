"""Provides helper functions dealing with file I/O."""

import numpy
from numpy.compat import isfileobj, pickle
from numpy.lib.format import (
    _check_version,
    _write_array_header,
    header_data_from_array_1_0,
)


def write_array(
    fp, array, version=None, allow_pickle=True, pickle_kwargs=None
):  # pragma: no cover
    """This is basically the NumPy numpy.lib.format.write_array function with the only
    change being pickle protocol 2 is used to dump the data (instead of 3 in the most
    recent release of NumPy)"""
    _check_version(version)
    _write_array_header(fp, header_data_from_array_1_0(array), version)

    if array.itemsize == 0:
        buffersize = 0
    else:
        # Set buffer size to 16 MiB to hide the Python loop overhead.
        buffersize = max(16 * 1024**2 // array.itemsize, 1)

    if array.dtype.hasobject:
        # We contain Python objects so we cannot write out the data
        # directly.  Instead, we will pickle it out
        if not allow_pickle:
            raise ValueError("Object arrays cannot be saved when allow_pickle=False")
        if pickle_kwargs is None:
            pickle_kwargs = {}

        pickle.dump(array, fp, protocol=2, **pickle_kwargs)
    elif array.flags.f_contiguous and not array.flags.c_contiguous:
        if isfileobj(fp):
            array.T.tofile(fp)
        else:
            for chunk in numpy.nditer(
                array,
                flags=["external_loop", "buffered", "zerosize_ok"],
                buffersize=buffersize,
                order="F",
            ):
                fp.write(chunk.tobytes("C"))
    else:
        if isfileobj(fp):
            array.tofile(fp)
        else:
            for chunk in numpy.nditer(
                array,
                flags=["external_loop", "buffered", "zerosize_ok"],
                buffersize=buffersize,
                order="C",
            ):
                fp.write(chunk.tobytes("C"))
