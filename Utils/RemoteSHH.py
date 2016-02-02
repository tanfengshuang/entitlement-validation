import paramiko
import commands
import logging
import time

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
            channel.settimeout(timeout)
            channel.exec_command(cmd)

            terminate_time = time.time() + timeout
            output = ""
            ret = 0

            while True:
                if channel.recv_ready():
                    data = channel.recv(1048576)
                    output += data
                    if channel.exit_status_ready():
                        ret = channel.recv_exit_status()
                        break

                else:
                    time.sleep(10)

                if channel.recv_stderr_ready():
                    error_data = channel.recv_stderr(1048576)
                    output += error_data
                    ret = channel.recv_exit_status()
                    break

                if terminate_time < time.time():
                    output += "\nCommand timeout exceeded ..."
                    ret = -1
                    break

            time.sleep(10)
            if channel.recv_ready():
                data = channel.recv(1048576)
                output += data

        if output.strip() != "":
            output = output.strip()
            if len(output.splitlines()) < 100:
                logger.info(output)
            else:
                logging.info("<< Note: since the output is too long(more than 100 lines) here, logged it as debug info. >>")
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
                logging.info("<< Note: since the output is too long(more than 100 lines) here, logged it as debug info. >>")
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

if __name__ == '__main__':
    system_info = {
                "ip": "amd-dinar-01.lab.bos.redhat.com",
                "username": "root",
                "password": "QwAo2U6GRxyNPKiZaOCx"
            }
    cmd = 'repoquery --all --repoid=rhel-7-server-optional-rpms --qf "%{name}"'
    #cmd = 'repoquery --all --repoid=rhel-7-server-rpms --qf "%{name}"'
    #cmd = 'repoquery --pkgnarrow=available --all --repoid=rhel-7-server-supplementary-source-rpms --archlist=src --qf "%{name}-%{version}-%{release}.src"'
    #cmd = "ll /root/"
    print cmd
    ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to clean the yum cache after register...")
    print "----------------"
    print ret
    print output
    print len(output.splitlines())
    j=0
    for i in output.splitlines():
        j += len(i)
    print j