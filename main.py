import os

from threading import Thread
from core.app import app
from core.database import DBManager
from core.logger_config import setup_logger
from core.utils import load_wallets_from_file
from loguru import logger


if __name__ == '__main__':
    setup_logger()

    wallets_list = load_wallets_from_file("data/wallets.txt")
    proxy_list = load_wallets_from_file("data/proxies.txt")

    # logger.info("wallets_list: %s" % wallets_list);
    # logger.info("proxy_list: %s" % proxy_list);

    DBManager.create_database(
        wallet_list=wallets_list,
        proxy_list=proxy_list,
    )

    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        logger.info("Запущен локальный сервер: http://127.0.0.1:5000")

    Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()