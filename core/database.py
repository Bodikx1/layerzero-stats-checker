import os
from functools import wraps

from core.models import Base, Wallet
from loguru import logger
from sqlalchemy import create_engine, desc, func, asc, nullslast
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


def db_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "session" in func.__code__.co_varnames:
            session = DBManager.get_session()
            try:
                return func(*args, **kwargs, session=session)
            except IntegrityError as e:
                logger.error(f"{e.orig}")
            except Exception as e:
                logger.error(f"{e}")
            finally:
                session.close()
        else:
            return func(*args, **kwargs)
    return wrapper


class DBManager:
    DB_URL = 'sqlite:///database.sqlite'
    engine = create_engine(DB_URL)

    @staticmethod
    def get_session():
        Session = sessionmaker(bind=DBManager.engine)
        return Session()

    @staticmethod
    def create_database(
            wallet_list: list,
            proxy_list: list
    ):
        session = None
        try:
            Base.metadata.create_all(DBManager.engine)
            session = DBManager.get_session()

            existing_wallets = session.query(Wallet.address).all()
            existing_wallets = {wallet.address for wallet in existing_wallets}

            for wallet, proxy in zip(wallet_list, proxy_list):
                if wallet not in existing_wallets:
                    new_wallet = Wallet(address=wallet, proxy=proxy)
                    session.add(new_wallet)

            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            raise Exception(f"{e}")
        finally:
            if session:
                session.close()

    @staticmethod
    @db_exceptions
    def delete_database():
        db_path = DBManager.DB_URL.split('///')[-1]
        DBManager.engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)

    @staticmethod
    @db_exceptions
    def merge_wallet_data(wallet_data: dict, session=None):
        address = wallet_data['address']
        existing_wallet = session.query(Wallet).filter_by(address=address).first()

        if existing_wallet:
            for key, value in wallet_data.items():
                if key != 'address':
                    setattr(existing_wallet, key, value)
        else:
            wallet_record = Wallet(**wallet_data)
            session.add(wallet_record)

        session.commit()

    @staticmethod
    @db_exceptions
    def get_all_wallets(session=None):
        wallets = session.query(Wallet).all()
        return wallets

    @staticmethod
    @db_exceptions
    def get_sorted_wallets(sort_by: str, session=None):
        sort_options = {
            'rank': Wallet.rank,
            'txsCount': Wallet.txsCount,
            'volume': Wallet.volume,
            'distinctMonths': Wallet.distinctMonths,
            'networks': Wallet.networks,
            'contracts': Wallet.contracts,
            'destChains': Wallet.destChains
        }

        wallets = session.query(Wallet).all()

        # ENABLE sorting:
        # sort_column = sort_options.get(sort_by, Wallet.rank)
        # if sort_by == 'rank':
        #     wallets = session.query(Wallet).order_by(nullslast(asc(sort_column))).all()
        # else:
        #     wallets = session.query(Wallet).order_by(desc(sort_column)).all()

        min_rank = session.query(func.min(Wallet.rank)).filter(Wallet.rank > 0).scalar()
        total_volume = session.query(func.sum(Wallet.volume)).scalar()
        top_500k_wallets = session.query(Wallet).filter(Wallet.rank <= 500000).count()
        top_1m_wallets = session.query(Wallet).filter(Wallet.rank <= 1000000).count()

        return wallets, min_rank, total_volume, top_500k_wallets, top_1m_wallets
