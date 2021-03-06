# BSD 3-Clause License; see https://github.com/scikit-hep/uproot4/blob/master/LICENSE

"""
Physical layer for file-like objects.

Defines a :py:class:`~uproot4.source.object.ObjectResource` (wrapped Python file-like
object) and one source :py:class:`~uproot4.source.object.ObjectSource` which always
has exactly one worker (we can't assume that the object is thread-safe).
"""

from __future__ import absolute_import

import uproot4.source.futures
import uproot4.source.chunk
import uproot4._util


class ObjectResource(uproot4.source.chunk.Resource):
    """
    Args:
        obj: The file-like object to use.

    A :py:class:`~uproot4.source.chunk.Resource` for a file-like object.

    This object must have the following methods:

    - ``read(num_bytes)`` where ``num_bytes`` is an integer number of bytes to
      read.
    - ``seek(position)`` where ``position`` is an integer position to seek to.

    Both of these methods change the internal state of the object, its current
    seek position (because ``read`` moves that position forward ``num_bytes``).
    Hence, it is in principle not thread-safe.
    """

    def __init__(self, obj):
        self._obj = obj

    @property
    def obj(self):
        return self._obj

    @property
    def closed(self):
        return getattr(self._obj, "closed", False)

    def __enter__(self):
        if hasattr(self._obj, "__enter__"):
            self._obj.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if hasattr(self._obj, "__exit__"):
            self._obj.__exit__(exception_type, exception_value, traceback)

    def get(self, start, stop):
        """
        Args:
            start (int): Seek position of the first byte to include.
            stop (int): Seek position of the first byte to exclude
                (one greater than the last byte to include).

        Returns a Python buffer of data between ``start`` and ``stop``.
        """
        self._obj.seek(start)
        return self._obj.read(stop - start)

    @staticmethod
    def future(source, start, stop):
        """
        Args:
            source (:py:class:`~uproot4.source.chunk.ObjectSource`): The data source.
            start (int): Seek position of the first byte to include.
            stop (int): Seek position of the first byte to exclude
                (one greater than the last byte to include).

        Returns a :py:class:`~uproot4.source.futures.ResourceFuture` that calls
        :py:meth:`~uproot4.source.object.ObjectResource.get` with ``start`` and
        ``stop``.
        """

        def task(resource):
            return resource.get(start, stop)

        return uproot4.source.futures.ResourceFuture(task)


class ObjectSource(uproot4.source.chunk.MultithreadedSource):
    """
    Args:
        obj: The file-like object to use.

    A :py:class:`~uproot4.source.chunk.Source` for a file-like object. (Although this
    is a :py:class:`~uproot4.source.chunk.MultithreadedSource`, it never has more or
    less than one thread.)

    This object must have the following methods:

    - ``read(num_bytes)`` where ``num_bytes`` is an integer number of bytes to
      read.
    - ``seek(position)`` where ``position`` is an integer position to seek to.

    Both of these methods change the internal state of the object, its current
    seek position (because ``read`` moves that position forward ``num_bytes``).
    Hence, it is in principle not thread-safe.
    """

    ResourceClass = ObjectResource

    def __init__(self, obj, **options):
        self._num_requests = 0
        self._num_requested_chunks = 0
        self._num_requested_bytes = 0

        self._file_path = repr(obj)
        self._executor = uproot4.source.futures.ResourceThreadPoolExecutor(
            [ObjectResource(obj)]
        )
        self._num_bytes = None
