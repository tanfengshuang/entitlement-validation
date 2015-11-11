import paramiko
import logging

class RemoteSHH(object):
    def __init__(self):
        pass

    def run_cmd(self, system_info, cmd, cmd_desc=""):
        logging.info(cmd_desc)

        ip = system_info["ip"]
        username = system_info["username"]
        password = system_info["password"]

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, username, password)

        channel = ssh.get_transport().open_session()
        channel.exec_command(cmd)

        output = ""
        while True:
            data = channel.recv(1048576)
            output += data
            if channel.exit_status_ready():
                break
        if channel.recv_ready():
            data = channel.recv(1048576)
            output += data
        logging.info("# {0}".format(cmd))
        if output.strip() != "":
            logging.info(output.strip())
        return channel.recv_exit_status(), output