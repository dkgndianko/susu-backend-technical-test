from itertools import groupby
from typing import TypeVar, Generic, Callable, Iterable, List, Dict

T = TypeVar("T")
K = TypeVar("K")


class Grouping(Generic[T, K]):
    """
    this genric class is a helper for grouping elements of type T.

    """

    def __init__(self, iterable: Iterable[T]):
        """
        Initialize with iterables
        """
        self.elements: List[T] = iterable
        self.keys: List[K] = []
        self.groups: Dict[K, List[T]] = {}

    def group_by(self, key_fn: Callable[[T], K]) -> None:
        """
        Groups elements using the given key function. It will hold groups and keys
        """
        grouped = groupby(self.elements, key=key_fn)
        for key, group in grouped:
            self.groups[key] = list(group)
            self.keys.append(key)

    def get_keys(self) -> List[K]:
        """
        Get list of keys after grouping
        """
        return self.keys

    def get_group(self, key: K) -> List[T]:
        """
        Returns a group given the key or an empty list if not present
        """
        return self.groups.get(key, [])
