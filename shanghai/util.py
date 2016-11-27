
import functools
from typing import Union, Callable

from fullqualname import fullqualname


class ShadowAttributesMixin:

    """Mixin class that allows to add (and set) attributes without collisions.

    Instead of directly setting attributes (or using `setattr`) for the first time,
    use `add_attribute` or `add_method`.

    When changing adding attributes,
    use `set_attribute` (not designed to be used with 'methods').

    When removing attributes,
    use `remove_attribute`.
    """

    def __init__(self, *args, **kwargs):
        self._added_attributes = dict()

        super().__init__(*args, **kwargs)

    def add_attribute(self, name: str, value=None):
        """Allows to add attributes to an object.

        Use this instead of directly setting attributes (or with `setattr`).
        For adding methods, use add_method.
        """
        if hasattr(self, name) or name in self._added_attributes:
            raise KeyError("Attribute '{}' is already defined".format(name))
        self._added_attributes[name] = value

    def set_attribute(self, name: str, value=None):
        """Allows to modify added attributes to an object."""
        if name not in self._added_attributes:
            raise KeyError("Attribute '{}' is not defined".format(name))
        self._added_attributes[name] = value

    def add_method(self, name_or_function: Union[str, Callable], function: callable = None):
        """Allows to add methods to an object.

        Added functions will be called with an implicit `self` argment,
        like for normal methods.

        Also functions as a decorator and infers the attribute name from the function name.
        """
        if callable(name_or_function):
            function = name_or_function
            name = function.__name__
        elif not callable(function):
            raise ValueError("Parameter is not callable")
        else:
            name = name_or_function

        self.add_attribute(name, functools.partial(function, self))

        return function

    def remove_attribute(self, name: str):
        """Allows for plugins to remove their added attributes to the network object."""
        if name not in self._added_attributes:
            raise KeyError("Attribute '{}' is not defined".format(name))
        del self._added_attributes[name]

    def __getattr__(self, name):
        if name in self._added_attributes:
            return self._added_attributes[name]
        else:
            raise AttributeError("{!r} has no attribute {!r}".format(self, name))
        #     super().__getattr__(name)


def repr_func(func: callable) -> str:
    """Represent a function with its full qualname instead of just its name and an address."""
    return "<{} {}>".format(type(func).__name__, fullqualname(func))