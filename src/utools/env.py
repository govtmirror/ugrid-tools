import os
from importlib import import_module

import logbook

from utools.constants import UgridToolsConstants


class Environment(object):
    def __init__(self):
        self.LOGGING_DIR = EnvParm('LOGGING_DIR', os.getcwd())
        self.LOGGING_FILE_PREFIX = EnvParm('LOGGING_FILE_PREFIX', UgridToolsConstants.PROJECT_PREFIX)
        self.LOGGING_LEVEL = EnvParm('LOGGING_LEVEL', logbook.ERROR)
        self.LOGGING_STDOUT = EnvParm('LOGGING_STDOUT', False, formatter=self._format_bool_)

    def __str__(self):
        msg = []
        for value in self.__dict__.itervalues():
            if isinstance(value, EnvParm):
                msg.append(str(value))
        msg.sort()
        return '\n'.join(msg)

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        try:
            ret = attr.value
        except AttributeError:
            ret = attr
        return ret

    def __setattr__(self, name, value):
        if isinstance(value, EnvParm) or name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            attr = object.__getattribute__(self, name)
            attr.value = value
            if attr.on_change is not None:
                attr.on_change()

    def reset(self):
        """
        Reset values to defaults (Values will be read from any overloaded system environment variables.
        """

        for value in self.__dict__.itervalues():
            if isinstance(value, EnvParm):
                value._value = 'use_env'
                getattr(value, 'value')

    @staticmethod
    def _format_bool_(value):
        """
        Format a string to boolean.

        :param value: The value to convert.
        :type value: int or str
        """

        from ocgis.util.helpers import format_bool

        return format_bool(value)


class EnvParm(object):
    def __init__(self, name, default, formatter=None, on_change=None):
        self.name = name.upper()
        self.env_name = '{0}_{1}'.format(UgridToolsConstants.PROJECT_PREFIX.upper(), self.name)
        self.formatter = formatter
        self.default = default
        self.on_change = on_change
        self._value = 'use_env'

    def __str__(self):
        return '{0}={1}'.format(self.name, self.value)

    @property
    def value(self):
        if self._value == 'use_env':
            ret = os.getenv(self.env_name)
            if ret is None:
                ret = self.default
            else:
                # attempt to use the parameter's format method.
                try:
                    ret = self.format(ret)
                except NotImplementedError:
                    if self.formatter is not None:
                        ret = self.formatter(ret)
        else:
            ret = self._value
        return ret

    @value.setter
    def value(self, value):
        self._value = value

    def format(self, value):
        raise NotImplementedError


class EnvParmImport(EnvParm):
    def __init__(self, name, default, module_names):
        self.module_names = module_names
        super(EnvParmImport, self).__init__(name, default)

    @property
    def value(self):
        if self._value == 'use_env':
            ret = os.getenv(self.env_name)
            if ret is None:
                if self.default is None:
                    ret = self._get_module_available_()
                else:
                    ret = self.default
            else:
                ret = Environment._format_bool_(ret)
        else:
            ret = self._value
        return ret

    @value.setter
    def value(self, value):
        self._value = value

    def _get_module_available_(self):
        results = []
        for m in get_iter(self.module_names):
            try:
                import_module(m)
                app = True
            except ImportError:
                app = False
            results.append(app)
        return any(results)


env = Environment()
