# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models import Otteludata
from flask import current_app
from config import Config


def get_db():
    if 'db' not in current_app.config:
        current_app.config['db'] = Database(Config.SQLALCHEMY_DATABASE_URI)
    return current_app.config['db']

class Database:
    def __init__(self, database_uri):
        self.engine = create_engine(database_uri, echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def list_matches(self):
        matches = self.session.query(Otteludata).all()
        return matches
    
    def get_match_by_ottelunumero(self, ottelunumero):
        ottelu = self.session.query(Otteludata).filter_by(ottelunumero=ottelunumero).first()
        return ottelu

    def update_match(self, ottelunumero, params):
        ottelu = self.get_match_by_ottelunumero(ottelunumero)
        if ottelu:
            ottelu.kotijoukkue = params['kotijoukkue']
            try:
                self.session.commit()
                return True
            except IntegrityError:
                self.session.rollback()
                return False
        return False
        