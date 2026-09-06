import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import stdlib logging BEFORE this package shadows it
import importlib
_logging = importlib.import_module("logging")


class CVLogger:
    _instance: Optional["CVLogger"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CVLogger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.log_dir = Path("client/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._logger = _logging.getLogger("cv_creator")
        self._logger.setLevel(_logging.DEBUG)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        if self._logger.handlers:
            return

        formatter = _logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Consola
        console_handler = _logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_logging.DEBUG)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # Archivo diario
        file_handler = _logging.FileHandler(
            self._get_log_file(), encoding="utf-8", mode="a"
        )
        file_handler.setLevel(_logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def _get_log_file(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        return str(self.log_dir / f"logs_{today}.log")

    def _rotate_file_if_needed(self) -> None:
        current_file = self._get_log_file()
        for handler in self._logger.handlers:
            if isinstance(handler, _logging.FileHandler) and handler.baseFilename != str(
                Path(current_file).resolve()
            ):
                handler.close()
                self._logger.removeHandler(handler)
                new_handler = _logging.FileHandler(
                    current_file, encoding="utf-8", mode="a"
                )
                new_handler.setLevel(_logging.DEBUG)
                new_handler.setFormatter(self._logger.handlers[0].formatter)
                self._logger.addHandler(new_handler)
                break

    def _log(
        self,
        level: int,
        module: str,
        function: str,
        message: str,
        user_id: Optional[str] = None,
        exc_info=None,
    ) -> None:
        self._rotate_file_if_needed()
        prefix = f"[user={user_id}] " if user_id else ""
        full_message = f"{prefix}{message}"
        self._logger.log(level, full_message, extra={"module": module, "funcName": function}, exc_info=exc_info)

    def debug(self, module: str, function: str, message: str, user_id: Optional[str] = None) -> None:
        self._log(_logging.DEBUG, module, function, message, user_id)

    def info(self, module: str, function: str, message: str, user_id: Optional[str] = None) -> None:
        self._log(_logging.INFO, module, function, message, user_id)

    def warning(self, module: str, function: str, message: str, user_id: Optional[str] = None) -> None:
        self._log(_logging.WARNING, module, function, message, user_id)

    def error(self, module: str, function: str, message: str, user_id: Optional[str] = None, exc_info=None) -> None:
        self._log(_logging.ERROR, module, function, message, user_id, exc_info=exc_info)

    def critical(self, module: str, function: str, message: str, user_id: Optional[str] = None) -> None:
        self._log(_logging.CRITICAL, module, function, message, user_id)


logger = CVLogger()
