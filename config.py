import configparser
import logging
import os
import glob
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', level=logging.ERROR)


class Config(object):
    """Class to read config file
    """

    def __init__(self, config_file):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)

        env_config = os.getenv('VSPACE_CONFIG')
        if env_config:
            print('VSPACE_CONFIG=', env_config)
            # overwrite config if VSPACE_CONFIG is set
            config_file = env_config

        self.config = configparser.ConfigParser()
        self.log.info('Read config file %s', config_file)
        read_ok = self.config.read(config_file)
        if not read_ok:
            msg = 'Cannot read config from %s' % config_file
            self.log.error(msg)
            raise Exception(msg)

    def get_section(self, section):
        try:
            return self.config[section]
        except KeyError:
            return None

    def get(self, section, key, default=None):
        section = self.get_section(section)
        return section.get(key, default) if section is not None else default

    def getboolean(self, section, key, default=None):
        section = self.get_section(section)
        return section.getboolean(key, default) if section is not None else default

    def getint(self, section, key, default=None):
        section = self.get_section(section)
        return section.getint(key, default) if section is not None else default


# example to get setting values from config
def main():
    conf = Config()
    print(conf.get('url', 'api.endpoint'))


if __name__ == '__main__':
    main()
