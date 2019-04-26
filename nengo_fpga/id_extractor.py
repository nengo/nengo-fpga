import socket
import os
import threading
import paramiko
import numpy as np

from nengo_fpga.fpga_config import fpga_config


class IDExtractor(object):
    """ Class that connects to the FPGA and extracts the Device ID

    Parameters
    ----------
    fpga_name : str
        The name of the fpga defined in the config file.
    max_attempts : int, optional (Default: 5)
        The number of times the socket will attempt to connect to the board.
    timeout : float, optional (Default: 5)
        The number of seconds the socket will wait to connect.

    """
    def __init__(self, fpga_name, max_attempts=5, timeout=5):

        self.config_found = fpga_config.has_section(fpga_name)
        self.fpga_name = fpga_name
        self.max_attempts = max_attempts
        self.timeout = timeout

        # Make SSHClient object
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_info_str = ''
        self.ssh_lock = False

        # Check if the desired FPGA name is defined in the configuration file
        if self.config_found:
            # Handle the tcp port selection: Use the config specified port.
            # If none is provided (i.e., the specified port number is 0),
            # choose a random tcp port number between 20000 and 65535.
            # We will use the udp port number from the config but use tcp.
            self.tcp_port = int(fpga_config.get(fpga_name, 'udp_port'))
            if self.tcp_port == 0:
                self.tcp_port = int(np.random.uniform(low=20000, high=65535))

            # Make the TCP socket for receiving Device ID.
            self.tcp_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_init.bind((fpga_config.get('host', 'ip'), self.tcp_port))
            self.tcp_init.settimeout(self.timeout)
            self.tcp_init.listen(1)  # Ready to accept a connection
            self.tcp_recv = None  # Placeholder until socket is connected

        else:
            # FPGA name not found, throw a warning.
            print("WARNING: Specified FPGA configuration '" + fpga_name +
                  "' not found.", flush=True)
            self.tcp_socket = None

    def cleanup(self):
        self.tcp_init.close()
        self.ssh_client.close()

        if self.tcp_recv is not None:
            self.tcp_recv.close()

    def connect_thread_func(self):
        # Get the IP of the remote device from the fpga_config file
        remote_ip = fpga_config.get(self.fpga_name, 'ip')

        # Get the SSH options from the fpga_config file
        ssh_port = fpga_config.get(self.fpga_name, 'ssh_port')
        ssh_user = fpga_config.get(self.fpga_name, 'ssh_user')

        if fpga_config.has_option(self.fpga_name, 'ssh_pwd'):
            ssh_pwd = fpga_config.get(self.fpga_name, 'ssh_pwd')
        else:
            ssh_pwd = None

        if fpga_config.has_option(self.fpga_name, 'ssh_key'):
            ssh_key = os.path.expanduser(fpga_config.get(self.fpga_name,
                                                         'ssh_key'))
        else:
            ssh_key = None

        # Connect to remote location over ssh
        if ssh_key is not None:
            # If an ssh key is provided, just use it
            self.ssh_client.connect(remote_ip, port=ssh_port,
                                    username=ssh_user, key_filename=ssh_key)
        elif ssh_pwd is not None:
            # If an ssh password is provided, just use it
            self.ssh_client.connect(remote_ip, port=ssh_port,
                                    username=ssh_user, password=ssh_pwd)
        else:
            # If no password or key is specified, just use the default connect
            # (paramiko will then try to connect using the id_rsa file in the
            #  ~/.ssh/ folder)
            self.ssh_client.connect(remote_ip, port=ssh_port,
                                    username=ssh_user)

        # Invoke a shell in the ssh client
        ssh_channel = self.ssh_client.invoke_shell()

        # If board configuration specifies using sudo to run scripts
        # - Assume all non-root users will require sudo to run the scripts
        # - Note: Also assumes that the fpga has been configured to allow
        #         the ssh user to run sudo commands WITHOUT needing a password
        #         (see specific fpga hardware docs for details)
        if ssh_user != 'root':
            print('<%s> Script to be run with sudo. Sudoing.' %
                  remote_ip, flush=True)
            ssh_channel.send('sudo su\n')

        # Send required ssh string
        print("<%s> Sending cmd to fpga board: \n%s" %
              (fpga_config.get(self.fpga_name, 'ip'),
               self.ssh_string), flush=True)
        ssh_channel.send(self.ssh_string)

        # Variable for remote error handling
        got_error = 0
        error_strs = []

        # Get and process the information being returned over the ssh
        # connection
        while True:
            data = ssh_channel.recv(256)
            if not data:
                # If no data is received, the client has been closed, so close
                # the channel, and break out of the while loop
                ssh_channel.close()
                break

            self.process_ssh_output(data)
            info_str_list = self.ssh_info_str.split('\n')
            for info_str in info_str_list[:-1]:
                if info_str.startswith('Killed'):
                    print('<%s> ENCOUNTERED ERROR!' % remote_ip, flush=True)
                    got_error = 2

                if info_str.startswith('Traceback'):
                    print('<%s> ENCOUNTERED ERROR!' % remote_ip, flush=True)
                    got_error = 1
                elif got_error > 0 and info_str[0] != ' ':
                    # Error string is no longer tabbed, so the actual error
                    # is bring printed. Collect and terminate (see below)
                    got_error = 2

                if got_error > 0:
                    # Once an error is encountered, keep collecting error
                    # messages until the termination condition (above)
                    error_strs.append(info_str)
                else:
                    print('<%s> %s' % (remote_ip, info_str), flush=True)
            self.ssh_info_str = info_str_list[-1]

            # The traceback usually contains 3 lines, so collect the first
            # three lines then display it.
            if got_error == 2:
                ssh_channel.close()
                raise RuntimeError(
                    'Received the following error on the remote side <%s>:\n%s'
                    % (remote_ip, '\n'.join(error_strs)))

    def connect(self):
        print("<%s> Open SSH connection" %
              fpga_config.get(self.fpga_name, 'ip'), flush=True)
        # Start a new thread to open the ssh connection. Use a thread to
        # handle the opening of the connection because it can lag for certain
        # devices, and we dont want it to impact the rest of the build process.
        connect_thread = threading.Thread(target=self.connect_thread_func,
                                          args=())
        connect_thread.start()

    def process_ssh_output(self, data):
        # Clean up the data stream coming back over ssh
        str_data = data.decode('latin1').replace('\r\n', '\r')
        str_data = str_data.replace('\r\r', '\r')
        str_data = str_data.replace('\r', '\n')

        # Process and dump the returned ssh data to logger. Data (strings)
        # returned over SSH are terminated by a newline, so, keep track of
        # the data and write the data to logger only when a newline is
        # received.
        self.ssh_info_str += str_data

    @property
    def ssh_string(self):
        # Generate the string to be sent over the ssh connection to run the
        # remote side ssh script (with appropriate arguments)
        if self.config_found:
            ssh_str = \
                ('python ' + fpga_config.get(self.fpga_name, 'id_script') +
                 ' --host_ip="%s"' % fpga_config.get('host', 'ip') +
                 ' --tcp_port=%i' % self.tcp_port +
                 '\n')
        else:
            ssh_str = ''
        return ssh_str

    def recv_id(self):
        # Try to connect to FPGA socket a few times
        connect_attempts = 0
        while True:
            try:
                self.tcp_recv, _addr = self.tcp_init.accept()
                break
            except socket.timeout as e:
                connect_attempts += 1
                if connect_attempts >= self.max_attempts:
                    e.args = ("ERROR: Could not connect to %s"
                              ", please ensure you have the correct"
                              " FPGA configuration or increase the"
                              " number of connection attempts." %
                              self.fpga_name,)
                    self.cleanup()
                    raise
                else:
                    print("WARNING: Could not connect to %s for %0.1fs,"
                          " trying again..." % (self.fpga_name, self.timeout),
                          flush=True)

        # Read ID once socket connected successfully
        self.id_bytes = self.tcp_recv.recv(8)
        self.id_int = int.from_bytes(self.id_bytes, 'big')


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Generic script for running the ID Extractor on the ' +
        'FPGA board.')

    # FPGA board name
    parser.add_argument(
        'fpga_name', type=str,
        help='Name of the FPGA board as specified in the fpga_config file')

    # Print full help text, otherwise error message isn't very useful
    if len(sys.argv) != 2:
        parser.print_help()
        sys.exit()

    # Parse the arguments
    args = parser.parse_args()
    filename = 'id_' + args.fpga_name + '.txt'

    # Connect to FPGA, run script to get ID, write ID to file
    fpga = IDExtractor(args.fpga_name)
    fpga.connect()
    fpga.recv_id()

    id_str = "Found board ID: %#0.16X" % fpga.id_int

    with open(filename, 'w') as file:
        file.write(id_str)
    fpga.cleanup()
    print(id_str)
    print("Written to file %s" % filename)
