import faulthandler
import sys

def worker_int(worker):
    worker.log("=== WORKER INTERRUPTED - DUMPING STACK ===")
    faulthandler.dump_traceback(file = sys.stderr, all_threads=True)