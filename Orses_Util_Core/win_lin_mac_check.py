from subprocess import run

# dictionary mapping linux shell commands to windows
linux_to_win = dict()

linux_to_win["clear"] = 'cls'
linux_to_win["ls"] = 'dir'


def shell_command(cmd="clear"):
    """
    :param cmd: command to execute in shell, default is 'clear'
    used to clear shell command, compatible with linux, windows (not yet tested on mac)
    :return: None
    """
    try:
        run(cmd)
    except FileNotFoundError:  # windows 10
        if cmd in linux_to_win:
            cmd = linux_to_win[cmd]
            run(cmd, shell=True)
