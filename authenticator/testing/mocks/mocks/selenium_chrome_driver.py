import multiprocessing
import platform

if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork")  # Required on macOSX
