import os 
import datetime
import logging 

def setup(title: str, verbose: bool = False, write_to_disk: bool = True):
    """Sets up logging for this application.

    Args:
        verbose: write debug and info statements to stdout. Defaults to False.
        write_to_disk: write logs to disk. Defaults to True.
    """
    default_log_directory = os.path.join(os.getcwd(), "logs")
    current_time = datetime.datetime.now(datetime.UTC).strftime("%Y_%m_%dT%H_%M_%SZ")
    log_path = os.path.join(default_log_directory, f"{title}_{current_time}.log")
    if not os.path.exists(default_log_directory):
        os.makedirs(default_log_directory)

    log_format = "%(asctime)s %(message)s"
    log_date_format = "%m/%d/%Y %I:%M:%S %p"
    logging_level = logging.DEBUG if verbose else logging.WARNING
    handlers = [logging.StreamHandler()]
    if write_to_disk:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(format=log_format,
                        datefmt=log_date_format,
                        handlers=handlers,
                        level=logging_level)

def get(name: str): 
    return logging.getLogger(name)
