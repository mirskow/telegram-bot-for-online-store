from sqlalchemy import Column, Integer, String, Numeric, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BonusCards(Base):
    __tablename__ = 'bonus_cards'

    id_card = Column(Integer, primary_key=True)
    proc = Column(Integer)


class Cars(Base):
    __tablename__ = 'cars'

    id_car = Column(Integer, primary_key=True)
    type_car = Column(String(50))
    train_id = Column(Integer, ForeignKey('trains.id_train'))
    count_place = Column(Integer)


class Clients(Base):
    __tablename__ = 'clients'

    id_client = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    patronymic = Column(String(50))
    email = Column(String(50))
    phone = Column(String(50))
    ser_doc = Column(String(10))
    num_doc = Column(String(10))
    sex = Column(String(1))
    hash_pass = Column(String(100))
    card_id = Column(Integer, ForeignKey('bonus_cards.id_card'))
    account_date = Column(Date)

    bonus_card = relationship("BonusCards")


class Orders(Base):
    __tablename__ = 'orders'

    id_order = Column(Integer, primary_key=True)
    date_order = Column(Date)
    client_id = Column(Integer, ForeignKey('clients.id_client'))
    cost_order = Column(Numeric)
    status_order = Column(String(50))
    payment_id = Column(Integer, ForeignKey('payments.id_payment'))

    client = relationship("Clients")
    payment = relationship("Payments")


class Payments(Base):
    __tablename__ = 'payments'

    id_payment = Column(Integer, primary_key=True)
    type_payment = Column(String(50))


class Places(Base):
    __tablename__ = 'places'

    id_place = Column(Integer, primary_key=True)
    car_id = Column(Integer, ForeignKey('cars.id_car'))
    cost_place = Column(Numeric)


class Routes(Base):
    __tablename__ = 'routes'

    id_route = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id_trip'))
    train_id = Column(Integer, ForeignKey('trains.id_train'))
    data_s = Column(Date)
    time_s = Column(Time)
    data_e = Column(Date)
    time_e = Column(Time)


class Stations(Base):
    __tablename__ = 'station'

    id_station = Column(Integer, primary_key=True)
    name_station = Column(String(50))
    town = Column(String(50))


class Tickets(Base):
    __tablename__ = 'tickets'

    id_ticket = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey('places.id_place'))
    order_id = Column(Integer, ForeignKey('orders.id_order'))
    route_id = Column(Integer, ForeignKey('routes.id_route'))


class Trains(Base):
    __tablename__ = 'trains'

    id_train = Column(Integer, primary_key=True)
    type_train = Column(String(50))
    comment_train = Column(String(100))


class Trips(Base):
    __tablename__ = 'trips'

    id_trip = Column(Integer, primary_key=True)
    station_s = Column(Integer, ForeignKey('station.id_station'))
    station_e = Column(Integer, ForeignKey('station.id_station'))
    distance = Column(Integer)
    duration = Column(Time)
