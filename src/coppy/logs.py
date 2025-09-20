from enum import Enum
import functools
import inspect
import logging

import click
import colorlog


_logs_init = False
_top_module = __name__.split('.')[0]
_logger_names = [_top_module, f'{_top_module}_tests', '__main__']


class LogLevel(Enum):
    quiet = logging.WARNING
    info = logging.INFO
    debug = logging.DEBUG


def init_logging(log_level: str):
    global _logs_init
    assert not _logs_init

    logging.addLevelName(logging.DEBUG, 'debug')
    logging.addLevelName(logging.INFO, 'info')
    logging.addLevelName(logging.WARNING, 'warning')
    logging.addLevelName(logging.ERROR, 'error')
    logging.addLevelName(logging.CRITICAL, 'critical')

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)8s%(reset)s  %(message)s',
        log_colors={
            'debug': 'white',
            'info': 'cyan',
            'warning': 'yellow',
            'error': 'red',
            'critical': 'red',
        },
    )
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=(handler,))
    for name in _logger_names:
        logging.getLogger(name).setLevel(LogLevel[log_level].value)

    _logs_init = True


def opts_init(click_func):
    click.option('--quiet', 'log_level', flag_value=LogLevel.quiet.name, help='WARN+ logging')(
        click_func,
    )
    click.option(
        '--info',
        'log_level',
        flag_value=LogLevel.info.name,
        help='INFO+ logging',
        default=True,
    )(
        click_func,
    )
    click.option('--debug', 'log_level', flag_value=LogLevel.debug.name, help='DEBUG+ logging')(
        click_func,
    )

    @functools.wraps(click_func)
    def wrapper(*args, log_level: str, **kwargs):
        init_logging(log_level)
        return click_func(*args, **kwargs)

    return wrapper


def logger():
    frame = inspect.stack()[1].frame  # caller's frame
    module = inspect.getmodule(frame)
    return logging.getLogger(module.__name__)
