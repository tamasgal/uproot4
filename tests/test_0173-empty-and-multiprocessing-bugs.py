# BSD 3-Clause License; see https://github.com/scikit-hep/uproot4/blob/master/LICENSE

from __future__ import absolute_import

import multiprocessing

import pytest
import skhep_testdata

import uproot4


def test_empty():
    with uproot4.open(skhep_testdata.data_path("uproot-empty.root")) as f:
        t = f["tree"]
        assert t["x"].array(library="np").tolist() == []
        assert t["y"].array(library="np").tolist() == []
        assert t["z"].array(library="np").tolist() == []


def readone(filename):
    with uproot4.open(filename) as f:
        f.decompression_executor = uproot4.ThreadPoolExecutor()
        t = f["events"]
        b = t["px1"]
        b.array()


def test_multiprocessing():
    pool = multiprocessing.Pool(1)
    out = pool.map(
        readone,
        [
            skhep_testdata.data_path("uproot-Zmumu.root"),
            skhep_testdata.data_path("uproot-Zmumu-zlib.root"),
        ],
    )
    list(out)
