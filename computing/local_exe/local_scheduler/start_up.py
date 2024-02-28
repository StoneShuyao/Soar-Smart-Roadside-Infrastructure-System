import os
import time

import psutil


def find_pid_by_cmdline(cmd):
    cmd = cmd.split()
    processes = []
    for proc in psutil.process_iter():
        if proc.cmdline()[-1:] == cmd[-1:]:
            processes.append(proc)
    return processes


def run():
    cmd = "nohup python3 /local_scheduler/control.py"
    proc = find_pid_by_cmdline(cmd)
    if len(proc) > 0:
        [p.terminate() for p in proc]
    time.sleep(0.1)
    cmd = cmd + " &"
    os.system(cmd)


if __name__ == "__main__":
    run()
