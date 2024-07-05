#TODO: This file is a duplicate from vega.core; remove duplicate logic once vega.core is published publicly
"""Module with logic to help implement factory pattern logic in a program"""
import importlib
import os
import sys
import types
import typing
import functools

# TODO: Add regex argument to help filter out additional modules for importing
def resolve_import_name(path: str):
    """Resolve the import name to use for loading the module to memory.

    This is done by comparing the path to the paths in sys.path.

    Usage:
    ```
    from vega.core import factory

    # We are using the factory module itself as an example
    path = factory.__file__

    factory.resolve_import_name(path) # Returns vega.core.factory
    ```
    """
    # Ensure that the path uses the correct dashes for this os
    path, _ = os.path.splitext(os.path.normpath(path))
    for each_root in sys.path:
        if path.startswith(each_root):
            path = path.split(each_root)[-1]
            break
    return ".".join(filter(None, path.split(os.path.sep)))


def import_module_from_path(path: str, name: str = None) -> types.ModuleType:
    """Dynamically import the module from the given path.

    Args:
        path (str): Path to the module to import
        name (str): Name to use for the namespace if a name relative to the import location

    Usage:
    ```
    from vega.core import factory

    # We are using the factory module itself as an example
    path = factory.__file__

    factory.resolve_import_name(path) # Returns vega.core.factory
    ```
    """
    if not path.lower().endswith(".py"):
        raise ValueError(f"{path} is not a valid python file.")

    # Resolve which base name for the module to use
    name = name or resolve_import_name(path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def import_modules_from_directory(path: str, depth=0):
    """Dynamically import all the python modules.

    Args:
        path (str): Path to a directory
        depth (int): Recursion depth, this value is only meant to be used within the function itself.

    Usage:
    ```
    import os
    from vega.core import factory

    #This is an example path
    path = os.path.dirname(factory.__file__)
    factory.import_modules_from_directory(path) # imports all the modules within vega.core
    ```
    """
    modules = []
    for root, directories, files in os.walk(path):
        for directory_path in directories:
            import_path = os.path.join(root, directory_path)
            modules.extend(import_modules_from_directory(import_path, depth=depth + 1))

        for file_path in files:
            if not file_path.endswith(".py"):
                continue
            import_path = os.path.join(root, file_path)
            modules.append(import_module_from_path(import_path))
    return modules


def get_subclasses(cls: object) ->typing.List[object]:
    """Gets a list of subclasses that a class is being inherited in."""
    return [subclass for subclass in cls.__subclasses__()]

# End of duplicate code
@functools.cache
def import_parsers():
    """Imports the file parsers into memory to allow them to be dynamically discovered"""
    return import_modules_from_directory(os.path.join(os.path.dirname(__file__), "parsers"))


@functools.cache
def get_parser_by_filename(filename):
    """Gets the correct parser based on the filename given"""
    import_parsers()
    root_cls = sys.modules["vega.packaging.parsers.abstract_parser"].AbstractFileParser
    for cls in get_subclasses(root_cls):
        if cls.FILENAME.lower() == filename.lower():
            return cls

