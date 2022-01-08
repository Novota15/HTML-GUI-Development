# database functions
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy import Index
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine, select

Base = declarative_base()

# Tables
class Temperature(Base):
    __tablename__ = 'temperature'
    id = Column(Integer, primary_key = True, autoincrement=True)
    # fahrenheit
    value_f = Column(Float)
    # celsius
    value_c = Column(Float)
    time = Column(DateTime)

class Humidity(Base):
    __tablename__ = 'humidity'
    id = Column(Integer, primary_key = True, autoincrement=True)
    value = Column(Float)
    time = Column(DateTime)

# general db functions
def create(database):
    # an engine that the session will use for resources
    engine = create_engine(database)
    # create a configured session class
    Session = sessionmaker(bind=engine)
    # create a session
    session = Session()
    return engine, session

def result_dict(r):
    return dict(zip(r.keys(), r))

def result_dicts(rs):
    return list(map(result_dict, rs))

def database_dump(session):
    Database = [Temperature, Humidity]
    for table in Database:
        stmt = select('*').select_from(table)
        result = session.execute(stmt).fetchall()
        print(result_dicts(result))
    return

def create_tables(engine):
    Base.metadata.create_all(engine)
    return

def init_session():
    engine, session = create("sqlite:///db.sqlite3")
    create_tables(engine)
    return session

def close(conn):
    conn.close()
    return

def delete_obj(session, obj):
    session.delete(obj)
    session.commit()
    return

# add rows to tables
def add_temp(session, value_f, value_c, time):
    temp = Temperature(value_f=value_f, value_c=value_c, time=time)
    session.add(temp)
    session.commit()
    return

def add_humidity(session, value, time):
    humidity = Humidity(value=value, time=time)
    session.add(humidity)
    session.commit()
    return

def get_all_temps(session, type):
    temp_list = []
    temp_times = []
    temps = session.query(Temperature).all()
    for temp in temps:
        if type == "f":
            temp_list.append(temp.value_f)
        else:
            temp_list.append(temp.value_c)
        temp_times.append(temp.time)
    return temp_list, temp_times

def get_all_humids(session):
    humid_list = []
    humid_times = []
    humids = session. query(Humidity).all()
    for humid in humids:
        humid_list.append(humid.value)
        humid_times.append(humid.time)
    return humid_list, humid_times
        