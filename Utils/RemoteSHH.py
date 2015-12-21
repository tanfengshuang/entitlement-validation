import paramiko
import commands
import logging

# Create logger
logger = logging.getLogger("entLogger")

class RemoteSHH(object):
    def __init__(self):
        pass

    def run_cmd(self, system_info, cmd, cmd_desc="", timeout=None):
        logger.info(cmd_desc)
        logger.info("# {0}".format(cmd))

        if system_info == None:
            # Run commands locally
            ret, output = commands.getstatusoutput(cmd)
            return ret, output
        else:
            # Run commands remotely
            ip = system_info["ip"]
            username = system_info["username"]
            password = system_info["password"]

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, username, password)

        if timeout == None:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            ret = stdout.channel.recv_exit_status()
            error_output = stderr.read()
            output = stdout.read()
            if ret != 0:
                output = error_output + output
            ssh.close()
        else:
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
            ret = channel.channel.recv_exit_status()

        if output.strip() != "":
            output = output.strip()
            if len(output.splitlines()) < 100:
                logger.info(output)
            else:
                logger.debug(output)
        return ret, output

    def run_cmd_interact(self, system_info, cmd, cmd_desc=""):
        logger.info(cmd_desc)
        logger.info("# {0}".format(cmd))

        ip = system_info["ip"]
        username = system_info["username"]
        password = system_info["password"]

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, username, password)

        channel = ssh.get_transport().open_session()
        channel.settimeout(600)
        channel.get_pty()
        channel.exec_command(cmd)

        output = ""
        while True:
            data = channel.recv(1048576)
            output += data
            if channel.send_ready():
                if data.strip().endswith('[y/n]:'):
                    channel.send("y\n")
                if channel.exit_status_ready():
                    break
        if channel.recv_ready():
            data = channel.recv(1048576)
            output += data

        if output.strip() != "":
            output = output.strip()
            if len(output.splitlines()) < 100:
                logger.info(output)
            else:
                logger.debug(output)

        return channel.recv_exit_status(), output

    def download_file(self, system_info, remote_path, local_path):
        # Download file from remote system to local system
        logger.info("Trying to download remote file {0} to local {0}...".format(remote_path, local_path))

        ip = system_info["ip"]
        username = system_info["username"]
        password = system_info["password"]

        t = paramiko.Transport((ip, 22))
        t.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.get(remote_path, local_path)
        t.close()

    def upload_file(self, system_info, local_path, remote_path):
        # Upload file from local system to remote system
        logger.info("Trying to download remote file {0} to local {0}...".format(remote_path, local_path))

        ip = system_info["ip"]
        username = system_info["username"]
        password = system_info["password"]

        t = paramiko.Transport((ip, 22))
        t.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(local_path, remote_path)
        t.close()