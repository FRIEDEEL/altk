import logging

def setup_entry_log(filename = "runtime.log", level: int = logging.DEBUG):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter_file = logging.Formatter("%(asctime)s [%(levelname)8s ] %(name)s : %(message)s")
    filehandler = logging.FileHandler(filename = filename, mode="w")
    filehandler.setFormatter(formatter_file)
    filehandler.setLevel(logging.DEBUG)
    logger.addHandler(filehandler)