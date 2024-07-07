"""Decorators for packaging related operations."""


def autocreate(func):
    """Decorator for auto creating a file if it doesn't exist """
    def wrapper(instance, *args, **kwargs):
        if not instance.exists and instance.AUTOCREATE:
            instance.create()
        elif not instance.exists:
            raise FileNotFoundError(f"{instance.path} not found on disk.")
        return func(instance, *args, **kwargs)
    return wrapper