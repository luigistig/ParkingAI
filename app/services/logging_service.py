from app.utils.logger_config import logger


class LoggingService:

    @staticmethod
    def info(message):
        logger.info(message)

    @staticmethod
    def warning(message):
        logger.warning(message)

    @staticmethod
    def error(message):
        logger.error(message)

    @staticmethod
    def critical(message):
        logger.critical(message)

    @staticmethod
    def debug(message):
        logger.debug(message)


# LOG DE PRUEBA
logger.info("===== SISTEMA DE LOGGING INICIADO =====")