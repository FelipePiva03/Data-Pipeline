import logging

class Logger():
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Configura e retorna um logger com o nome e nível especificados.

        Args:
            name (str): Nome do logger.
            level (int): Nível de log (padrão: logging.INFO).

        Returns:
            logging.Logger: Logger configurado.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.hasHandlers():
            ch = logging.StreamHandler()
            ch.setLevel(level)

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)

            logger.addHandler(ch)

        return logger