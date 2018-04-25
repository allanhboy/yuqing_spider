# -*- coding: utf-8 -*-

from importlib import import_module

from scrapy.settings import Settings
from scrapy.utils.conf import closest_scrapy_cfg

from six.moves.configparser import (NoOptionError, NoSectionError,
                                    SafeConfigParser)


def find_settings():
    project_config_path = closest_scrapy_cfg()
    if not project_config_path:
        raise RuntimeError('Cannot find scrapy.cfg file')
    project_config = SafeConfigParser()
    project_config.read(project_config_path)
    try:
        project_settings = project_config.get('settings', 'default')
    except (NoSectionError, NoOptionError) as e:
        raise RuntimeError(e.message)

    module = import_module(project_settings)
    crawler_settings = Settings()
    crawler_settings.setmodule(module, priority='project')
    return crawler_settings
