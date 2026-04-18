"""Context managers for directory and path management."""
import os


class WorkingDirectory:
    """Context manager for temporarily changing the current working directory.

    Saves the current working directory on entry, changes to the target directory,
    and restores the original directory on exit (even if an exception occurs).

    Example:
        >>> with WorkingDirectory("/path/to/project"):
        ...     subprocess.run(["make"])
        >>> # CWD restored to original

        >>> with WorkingDirectory("/path/to/file.txt", is_file=True):
        ...     subprocess.run(["gcc", "file.c"])
        >>> # CWD is file's parent directory
    """

    def __init__(self, path: str, is_file: bool = True):
        """Initialize the WorkingDirectory context manager.

        Args:
            path: The target directory path, or a file path if is_file=True.
            is_file: If True, path is treated as a file path and the parent
                directory is used as the target. If False, path is treated as
                the target directory directly. Defaults to True.
        """
        self.__path = os.getcwd()
        if is_file:
            path = os.path.dirname(path)
        self.__target_path = path or self.__path

    def __enter__(self) -> str:
        """Enter the context and change to the target directory.

        Returns:
            The target directory path.
        """
        os.chdir(self.__target_path)
        return self.__target_path

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the context and restore the original working directory.

        Args:
            exc_type: The exception type if an exception occurred, else None.
            exc_val: The exception value if an exception occurred, else None.
            exc_tb: The traceback if an exception occurred, else None.

        Returns:
            False to propagate any exception, True to suppress it.
        """
        os.chdir(self.__path)
        return False