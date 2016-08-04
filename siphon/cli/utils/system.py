import os
import subprocess
import errno
import itertools
import tempfile
import time
import shutil
import shlex
import sys

from contextlib import contextmanager

def bash(cmd, hide_stdout=False, hide_stderr=False):
    hide_out = '/bin/bash -c "%s" %s> /dev/null'

    if hide_stdout and not hide_stderr:
        return subprocess.call(hide_out % (cmd, 1), shell=True)
    elif hide_stderr and not hide_stdout:
        return subprocess.call(hide_out % (cmd, 2), shell=True)
    elif hide_stderr and hide_stdout:
        return subprocess.call(hide_out % (cmd, '&'), shell=True)
    else:
        return subprocess.call('/bin/bash -c "%s"' % cmd, shell=True)

def ensure_dir_exists(path):
    """ Ensure that a directory at the given path exists """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def copyfile(src, dest):
    # Preserve symlinks
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dest)
    else:
        shutil.copy(src, dest)

def cleanup_dir(dir):
    if os.path.isdir(dir):
        shutil.rmtree(dir, ignore_errors=True)

def process_running(name):
    """ Takes a process name and returns True if it is running """
    try:
        subprocess.check_output(['pgrep', name], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

def background_process(cmd, time_estimate=60, spinner=False):
    """
    Run a given command in the background and display a progress bar.
    Provide an time estimate (in seconds) for the task to complete, and
    the bar will run at an appropriate rate. If it is finished before the
    time estimate, the bar will hurry up and reach the end. If the process
    is still running after the time estimate, the bar will wait at 90%% until
    the task is complete.

    Returns a process object when complete that can be inspected for
    the status code, errors etc.
    """
    try:
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE)
        if spinner:
            spin_phases = itertools.cycle(['|', '/', '-', '\\'])
            while p.poll() is None:
                sys.stdout.write('\r%s' % next(spin_phases))
                time.sleep(0.05)
                sys.stdout.flush()
            sys.stdout.write('\rDone\n')
        else:
            progress = 0
            bar_width = 50  # Length in chars

            load_up_to = int(50 * 0.9)  # 90%
            sleep_time = time_estimate / bar_width
            while p.poll() is None:
                sys.stdout.write('\r[%s%s]' % ('=' * progress,
                                            ' ' * (bar_width - progress)))
                sys.stdout.flush()
                time.sleep(sleep_time)
                if progress < load_up_to:
                    progress += 1
            remainder = bar_width - progress
            for i in range(remainder):
                progress += 1
                sys.stdout.write('\r[%s%s]' % ('=' * progress,
                                               ' ' * (bar_width - progress)))
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write('\n')
        return p

    except KeyboardInterrupt:
        p.kill()
        raise

@contextmanager
def cd(*paths):
    path = os.path.join(*paths)
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)

@contextmanager
def make_temp_dir(suffix=''):
    """ Use this within a `with` statement. Cleans up after itself. """
    path = tempfile.mkdtemp(suffix=suffix)
    try:
        yield path
    finally:
        shutil.rmtree(path)

def max_version(v1, v2):
    v1_nums = [int(x) for x in version.split('.')]
    v2_nums = [int(x) for x in min_version.split('.')]
    # The highest one is the one with the highest left-most character
    for i in range(len(v1_nums)):
        n1 = v1_nums[i]
        n2 = v2_nums[i]
        if n1 == n2:
            continue
        elif n1 > n2:
            return v1
        else:
            return v2
    # We have compared all the numbers and they are identical
    return v1
