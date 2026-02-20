import logging

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "[PID: %(process)d] - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[handler])

logger = logging.getLogger(__name__)
