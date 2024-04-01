"""Top level script for reading device ID."""

import argparse
import os
import socket
import subprocess
import sys
import threading

import numpy as np
from nengo_fpga.fpga_config import fpga_config


class IDExtractor:
    """
    Class that connects to the FPGA and extracts the Device ID.

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

        # Check if the desired FPGA name is defined in the configuration file
        if self.config_found:
            # Handle the tcp port selection: Use the config specified port.
            # If none is provided (i.e., the specified port number is 0),
            # choose a random tcp port number between 20000 and 65535.
            # We will use the udp port number from the config but use tcp.
            self.tcp_port = int(fpga_config.get(fpga_name, "udp_port"))
            if self.tcp_port == 0:
                self.tcp_port = int(np.random.uniform(low=20000, high=65535))

            # Make the TCP socket for receiving Device ID.
            self.tcp_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_init.bind((fpga_config.get("host", "ip"), self.tcp_port))
            self.tcp_init.settimeout(self.timeout)
            self.tcp_init.listen(1)  # Ready to accept a connection
            self.tcp_recv = None  # Placeholder until socket is connected

        else:
            # FPGA name not found, unable to retrieve ID
            print(
                "ERROR: Specified FPGA configuration '" + fpga_name + "' not found.",
                flush=True,
            )
            sys.exit()

    def cleanup(self):
        """Shutdown socket and SSH connection."""
        self.tcp_init.close()

        if self.tcp_recv is not None:
            self.tcp_recv.close()

    def connect(self):
        """Connect to device via SSH."""
        print(
            f"<{fpga_config.get(self.fpga_name, 'ip')}> Starting subprocess",
            flush=True,
        )

        subprocess.Popen(
            [
                "python",
                fpga_config.get(self.fpga_name, "id_script"),
                f"--host_ip={fpga_config.get('host', 'ip')}",
                f"--tcp_port={self.tcp_port}",
            ]
        )

    def recv_id(self):
        """Read device ID from device."""

        # Try to connect to FPGA socket a few times
        connect_attempts = 0
        while True:
            try:
                self.tcp_recv, _addr = self.tcp_init.accept()
                break
            except socket.timeout as e:
                connect_attempts += 1
                if connect_attempts >= self.max_attempts:
                    self.cleanup()
                    raise RuntimeError(
                        f"Could not connect to {self.fpga_name}"
                        ", please ensure you have the correct"
                        " FPGA configuration or increase the"
                        " number of connection attempts."
                    ) from e
                else:
                    print(
                        f"WARNING: Could not connect to {self.fpga_name} for "
                        f"{self.timeout:.1f}s,"
                        " trying again...",
                        flush=True,
                    )

        # Read ID once socket connected successfully
        self.id_bytes = self.tcp_recv.recv(8)
        self.id_int = int.from_bytes(self.id_bytes, "big")


def main(fpga_name):
    """Main script to extract device ID."""
    filename = "id_" + fpga_name + ".txt"

    # Connect to FPGA, run script to get ID, write ID to file
    fpga = IDExtractor(fpga_name)
    fpga.connect()
    fpga.recv_id()

    id_str = f"Found board ID: {fpga.id_int:#018X}"

    with open(filename, "w", encoding="ascii") as file:
        file.write(id_str)
    fpga.cleanup()
    print(id_str)
    print(f"Written to file {filename}")


def run():
    """Wrapped in a function so we can call this in tests."""
    if __name__ == "__main__":
        parser = argparse.ArgumentParser(
            description="Generic script for running the ID Extractor on the "
            + "FPGA board."
        )

        # FPGA board name
        parser.add_argument(
            "fpga_name",
            type=str,
            help="Name of the FPGA board as specified in the fpga_config file",
        )

        # Print full help text, otherwise error message isn't very useful
        if len(sys.argv) != 2:
            parser.print_help()
            sys.exit()

        # Parse the arguments
        args = parser.parse_args()

        main(args.fpga_name)


run()  # Run the __name__ == __main__ case by default (wrapper function)
