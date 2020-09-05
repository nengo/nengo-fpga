"""Modified Nengo Simulator to integrate FPGA interfaces"""

import atexit

import nengo
from .networks import FpgaPesEnsembleNetwork


class Simulator(nengo.simulator.Simulator):
    """Modified Nengo Simulator to integrate FPGA interfaces"""

    def __init__(self, network, **kwargs):
        # Keep a record of the SSH connection details
        self.fpga_networks_list = []

        # Iterate through all of the probes and generate a list of probe
        # targets
        probe_target_list = [p.target for p in network.all_probes]

        # Iterate through the given network and identify all of the
        # RemotePESEnembleNetworks that will require an SSH connection
        for net in network.networks:
            if (
                isinstance(net, FpgaPesEnsembleNetwork)
                and net not in self.fpga_networks_list
            ):
                # Add network to the list of FPGA networks in the simulation
                self.fpga_networks_list.append(net)

                # Set the 'using_fpga_sim' flag in all FPGA networks
                net.using_fpga_sim = True

                # Check if FpgaPesEnsembleNetwork dummy ensemble or dummy
                # connection are being probed. If they are throw an error.
                for target in probe_target_list:
                    if isinstance(target, nengo.Ensemble) and target is net.ensemble:
                        raise nengo.exceptions.BuildError(
                            "FPGA PES Ensembles are currently non-probable."
                        )
                    elif (
                        isinstance(target, nengo.ensemble.Neurons)
                        and target.ensemble is net.ensemble
                    ):
                        raise nengo.exceptions.BuildError(
                            "FPGA PES Neurons are currently non-probable."
                        )
                    elif (
                        isinstance(target, nengo.Connection)
                        and target is net.connection
                    ):
                        raise nengo.exceptions.BuildError(
                            "FPGA PES Connections are currently non-probable."
                        )

        # NOTE: Originally, a connect function was used to iterate and open
        #       all necessary SSH connections to the FPGA networks. However,
        #       a connect function is not called because the reset function
        #       should be called before the simulation is run.

        # Register OS signal handler to handle ctrl+C or any abnormal
        # termination
        atexit.register(self.terminate)

        # Call nengo.Simulator super constructor
        super().__init__(network, **kwargs)

    def close(self):
        """Close all connections to the remote networks"""
        for net in self.fpga_networks_list:
            net.close()
        super().close()

    def reset(self, seed=None):
        """Call the reset function for each remote network"""
        for net in self.fpga_networks_list:
            net.reset()
        super().reset(seed)

    def terminate(self):
        """
        Terminate the simulation.

        - Close all open UDP / SSH connections
        - Cleanup any existing temporary files
        """
        self.close()
        for net in self.fpga_networks_list:
            net.cleanup()
