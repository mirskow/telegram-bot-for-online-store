import models
from sqlalchemy.orm import aliased
from models import Orders, Clients, Tickets, Routes, Trips, Stations, Places, Cars
from datetime import datetime


def get_history(session, user_id):
    s_from = aliased(Stations, name='s_from')
    s_to = aliased(Stations, name='s_to')

    result = session.query(
        Orders.id_order,
        Tickets.id_ticket,
        Orders.date_order,
        s_from.town.label('town_s'),
        s_from.name_station.label('station_s'),
        s_to.town.label('town_e'),
        s_to.name_station.label('station_e'),
        Trips.distance,
        Tickets.place_id,
        Cars.id_car,
        Cars.train_id,
        Routes.train_id,
        Routes.id_route,
        Routes.data_e,
        Routes.data_s,
        Routes.time_e,
        Routes.time_s,
        Orders.cost_order
    ).join(
        Clients, Clients.id_client == Orders.client_id
    ).join(
        Tickets, Orders.id_order == Tickets.order_id
    ).join(
        Routes, Tickets.route_id == Routes.id_route
    ).join(
        Trips, Routes.trip_id == Trips.id_trip
    ).join(
        s_from, Trips.station_s == s_from.id_station
    ).join(
        s_to, Trips.station_e == s_to.id_station
    ).join(
        Places, Places.id_place == Tickets.place_id
    ).join(
        Cars, Places.car_id == Cars.id_car
    ).filter(
        Clients.id_client == user_id
    ).all()

    return result


def get_user_for_email(user_email, session):
    return session.query(models.Clients).filter_by(email=user_email).first()


def get_user_for_id(user_id, session):
    return session.query(models.Clients).filter_by(id_client=user_id).first()


def get_trips(session, date, town_start, town_end):
    s_from = aliased(Stations, name='s_from')
    s_to = aliased(Stations, name='s_to')

    result = session.query(
        Trips.id_trip,
        s_from.town.label('t_from'),
        s_from.name_station.label('s_from'),
        s_to.town.label('t_to'),
        s_to.name_station.label('s_to'),
        Trips.distance,
        Trips.duration,
        Routes.data_s,
        Routes.id_route,
        Routes.time_s,
        Routes.data_e,
        Routes.train_id,
        Routes.time_e
    ).join(
        Routes
    ).join(
        s_from, s_from.id_station == Trips.station_s
    ).join(
        s_to, s_to.id_station == Trips.station_e
    ).filter(
        s_from.town == town_start,
        s_to.town == town_end,
        Routes.data_s == date
    ).all()

    return result


def get_cars(session, routes_id, type_car):
    result = session.query(
        Cars.id_car
    ).join(
        Routes, Routes.train_id == Cars.train_id
    ).filter(
        Routes.id_route == routes_id, Cars.type_car == type_car
    ).all()

    return result


def get_places(session, car_id):
    result = session.query(
        Places.id_place,
        Places.cost_place
    ).join(
        Cars, Cars.id_car == Places.car_id
    ).filter(
        Cars.id_car == car_id
    ).all()

    return result


def insert_order(session, client_id, total_cost, place_id, route_id):
    date = datetime.now().strftime('%Y-%m-%d')
    order = Orders(date_order=date, client_id=client_id, cost_order=total_cost, status_order='оформлено')
    session.add(order)
    session.flush()

    order_id = order.id_order
    ticket = Tickets(place_id=place_id, order_id=order_id, route_id=route_id)
    session.add(ticket)

    session.commit()
    return order_id
