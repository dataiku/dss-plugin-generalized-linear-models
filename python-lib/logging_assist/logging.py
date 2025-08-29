import logging

class LazyLogger:
    _logger = None
    _initialized = False

    @classmethod
    def _initialize_logger(cls):
        if not cls._initialized:
            try:
                log_level = 'DEBUG'
            except Exception as e:
                log_level = 'DEBUG'

            level = getattr(logging, log_level.upper(), logging.DEBUG)
            if not isinstance(level, int):
                raise ValueError(f'Invalid log level: {log_level}')

            if cls._logger is None:
                cls._logger = logging.getLogger(__name__)
            cls._logger.setLevel('DEBUG')

            if not cls._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                cls._logger.addHandler(handler)
                cls._logger.propagate = False

            cls._initialized = True

    def debug(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._initialize_logger()
        self._logger.exception(msg, *args, **kwargs)


logger = LazyLogger()