import logging

import nengo_fpga.utils.paths
from nengo.utils.compat import configparser

logger = logging.getLogger(__name__)

FPGA_CONFIG_FILES = [nengo_fpga.utils.paths.fpga_config['nengo'],
                     nengo_fpga.utils.paths.fpga_config['system'],
                     nengo_fpga.utils.paths.fpga_config['user'],
                     nengo_fpga.utils.paths.fpga_config['project']]


class _FPGA_CONFIG(configparser.SafeConfigParser):
    def __init__(self):
        configparser.SafeConfigParser.__init__(self)
        self.reload_config()

    def _clear(self):
        for s in self.sections():
            self.remove_section(s)

    def read(self, filenames):
        logger.info('Reading FPGA configurations from {}'.format(filenames))
        return configparser.SafeConfigParser.read(self, filenames)

    def item_dict(self, section):
        items = self.items(section)
        item_dict = {}

        for k, v in items:
            item_dict[k] = v

        return item_dict

    def reload_config(self, filenames=None):
        if filenames is None:
            filenames = FPGA_CONFIG_FILES

        self._clear()
        self.read(filenames)


fpga_config = _FPGA_CONFIG()
