import logging
import paramiko
from scp import SCPClient
from sshtunnel import SSHTunnelForwarder
from typing import List


logger = logging.getLogger("paramiko")
logger.setLevel(logging.ERROR)
logger = logging.getLogger("sshtunnel")
logger.propagate = False
logger.setLevel(logging.CRITICAL + 1)


class SSH_Manager(object):
    """SSH client for file transfer & local 2 remote experiment exec."""

    def __init__(
        self,
        user_name: str,
        pkey_path: str,
        main_server: str,
        jump_server: str = "",
        ssh_port: int = 22,
    ):
        """Set the credentials & resource details."""
        self.pkey_path = pkey_path
        self.main_server = main_server
        self.jump_server = jump_server
        self.port = ssh_port
        self.user = user_name

        # We are always using tunnel even if not necessary!
        if self.jump_server == "":
            self.jump_server = self.main_server

    def generate_tunnel(self):
        """Generate a tunnel through the jump host."""
        return SSHTunnelForwarder(
            (self.jump_server, self.port),
            ssh_username=self.user,
            ssh_password="",
            ssh_pkey=self.pkey_path,
            remote_bind_address=(self.main_server, self.port),
        )

    def connect(self, tunnel):
        """Connect to the ssh client."""
        while True:
            try:
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=tunnel.local_bind_host,
                    port=tunnel.local_bind_port,
                    username=self.user,
                    password="",
                    timeout=100,
                )
                break
            except Exception:
                continue
        return client

    def sync_dir(self, local_dir_name, remote_dir_name):
        """Clone/sync over a local directory to remote server."""
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            scp = SCPClient(client.get_transport())
            scp.put(local_dir_name, remote_dir_name, recursive=True)
            client.close()
        return

    def execute_command(self, cmds_to_exec: List[str]):
        """Execute a shell command on the remote server."""
        for cmd in cmds_to_exec:
            with self.generate_tunnel() as tunnel:
                client = self.connect(tunnel)
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                for line in stderr:
                    print(line)
                client.close()
        return stdin, stdout, stderr

    def read_file(self, file_name: str):
        """Read a file from remote server and return it."""
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            # Something doesnt work here
            remote_file = ftp.open(file_name)
            all_lines = []
            try:
                for line in list(remote_file):
                    all_lines.append(line)
            except Exception as e:
                print(e)
            ftp.close()
            client.close()
        return all_lines

    def write_to_file(self, str_to_write: str, file_name: str):
        """Write a string to a text file on remote server."""
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            file = ftp.file(file_name, "w", -1)
            file.write(str_to_write)
            file.flush()
            ftp.close()
            client.close()
        return

    def get_file(self, remote_dir_name: str, local_dir_name: str):
        """scp clone a remote directory to the local machine."""
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            scp = SCPClient(client.get_transport())
            scp.get(remote_dir_name, local_path=local_dir_name, recursive=True)
            client.close()
        return

    def delete_file(self, file_name: str):
        """Delete a file on the remote server."""
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            ftp.remove(file_name)
            ftp.close()
            client.close()
        return

    def delete_dir(self, file_name: str):
        """Delete a directory on the remote server."""
        cmd = "rm -rf " + file_name
        self.execute_command([cmd])
