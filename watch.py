#!/usr/bin/env python3

import argparse
import os
import signal
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from common import console

if os.environ.get('DOCKER_CONTAINER', False):
    console.log("Info", "Observer performed by polling method.")
    from watchdog.observers.polling import PollingObserver as Observer

process = None
control = False

class when_file_chanage(FileSystemEventHandler):
    def __init__(self, kill_sub, self_harakiri):
        super().__init__()
        self.kill = kill_sub
        self.harakiri = self_harakiri
    def on_any_event(self, event):
        if os.path.basename(os.path.dirname(event.src_path)) == "static_page":
            return
        if event.src_path.endswith('watch.py'):
            self.harakiri()
        if event.src_path.endswith('.py'):
            self.kill()
        if not control:
            endswith_list = ['.json','.md','.xml','.html']
            for item in endswith_list:
                if event.src_path.endswith(item):
                    self.kill()
                    break
        if control and event.src_path.endswith('config/system.json'):
            self.kill()

def HUP_handler(signum, frame):
    console.log("Info", "Received {} signal.".format(signum))
    kill_progress()

def KILL_handler(signum, frame):
    console.log("Info", "Received {} signal.".format(signum))
    harakiri()

def harakiri():
    kill_progress()
    console.log("Success", "Stopped SilverBlog server.")
    os._exit(0)

def kill_progress():
    global process
    process.kill()


def start_watch(cmd, debug):
    global process
    event_handler = when_file_chanage(kill_progress, harakiri)
    observer = Observer(timeout=1)
    observer.schedule(event_handler, path=os.getcwd(), recursive=True)
    observer.start()
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    return_code = process.poll()
    while return_code is None:
        sleep_time = 1
        if debug:
            sleep_time = 0.05
        time.sleep(sleep_time)
        if not observer.is_alive():
            kill_progress()
            break
        return_code = process.poll()
        if debug:
            line_byte = process.stderr.readline()
            line = line_byte.decode("UTF-8")
            line = line.strip()
            if len(line) != 0:
                print(line)
                sys.stderr.flush()
            while len(line) != 0:
                line_byte = process.stderr.readline()
                line = line_byte.decode("UTF-8")
                line = line.strip()
                print(line)
                sys.stderr.flush()
    observer.stop()
    return return_code

parser = argparse.ArgumentParser()
parser.add_argument("--main", action="store_true",
                    help=argparse.SUPPRESS)
parser.add_argument("--control", action="store_true",
                    help="If you need to monitor the control server, add this option")
parser.add_argument("--debug", action="store_true",
                    help="Debug mode")
args = parser.parse_args()
job_name = "uwsgi.json"
job = "main"

if args.control:
    job_name = "uwsgi.json:control"
    job = "control"
    control = True

console.log("Info", "Started SilverBlog {} server".format(job))

cmd = ["uwsgi", "--json", job_name, "--chmod-socket=666"]
if not args.debug:
    if not os.path.exists("./logs"):
        os.mkdir("./logs")
    cmd.append("--logto")
    cmd.append("./logs/{}.log".format(job))
    cmd.append("--threaded-logger")
    cmd.append("--log-master")
    cmd.append("--disable-logging")

signal.signal(signal.SIGINT, KILL_handler)
signal.signal(signal.SIGTERM, KILL_handler)
signal.signal(signal.SIGQUIT, KILL_handler)
signal.signal(signal.SIGHUP, HUP_handler)
result_code = 0

while True:
    result_code = start_watch(cmd, args.debug)
    if result_code == 1:
        console.log("Error", "Received 1 signal,exited.")
        exit(1)
    if result_code == 78:
        console.log("Error", "Configuration Error,exited.")
        exit(78)
