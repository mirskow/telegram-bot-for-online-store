from config import Settings
import telebot
from telebot import types
from sqlalchemy import create_engine
import database
from sqlalchemy.orm import sessionmaker
import json

bot = telebot.TeleBot(Settings.BOT_TOKEN)
engine = create_engine(Settings.db_url)

Session = sessionmaker(
    bind=engine
)

authorized_users = {}
user_orders = {}
user_search = {}
choose_trip = {}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Профиль')
    btn2 = types.KeyboardButton('Главное меню')
    btn4 = types.KeyboardButton('Поиск')
    markup.row(btn1)
    markup.row(btn2, btn4)
    bot.send_message(message.chat.id, f'Добро пожаловь в чат-бот нашего интернет магазина!\n\n'
                                      f'Вам доступны кнопки меню на панели клавиатуры\n\n'
                                      f'"Профиль" - переход в личный кабинет\n'
                                      f'"Главное меню" - открыть главное меню чат-бота\n'
                                      f'"Поиск" - выполнить поиск по каталогу магазина\n\n'
                                      f'Удачных покупок!', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Главное меню')
def start(message):
    markup = types.InlineKeyboardMarkup()
    # btn1 = types.InlineKeyboardButton('Профиль')
    # btn4 = types.InlineKeyboardButton('Поиск')
    # markup.row(btn1)
    # markup.row(btn4)
    bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Профиль')
def callback_profile(message):
    if authorized_users.get(message.chat.id):
        user_id = authorized_users[message.chat.id]
        with Session() as session:
            user = database.get_user_for_id(user_id, session)
        show_user_info(message, user)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Авторизация', callback_data='autorization'))
        bot.send_message(message.chat.id, 'Необходимо авторизироваться. Нажмите на кнопку:',
                         reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Поиск')
def callback_search(message):
    bot.send_message(message.chat.id, "Введите запрос, чтобы продолжить.\n\n"
                                      f"Пример: 2024-03-15 Москва - Сочи")
    bot.register_next_step_handler(message, handle_trip)


def handle_trip(message):
    trip_date, trip_start, _, trip_end = message.text.split(" ")
    with Session() as session:
        trips = database.get_trips(session, trip_date, trip_start, trip_end)
    if trips:
        user_search[message.chat.id] = {'trips': trips, 'index': 0}
        send_trip_info(message.chat.id, 0, None)
    else:
        bot.send_message(message.chat.id, "Нет доступных поездок")


@bot.callback_query_handler(func=lambda callback: callback.data == 'autorization')
def callback_autorization(callback):
    bot.send_message(callback.message.chat.id, "Введите вашу почту, чтобы продолжить.")
    bot.register_next_step_handler(callback.message, handle_user_email)


@bot.callback_query_handler(func=lambda callback: callback.data == 'history')
def callback_history(callback):
    user_id = authorized_users[callback.message.chat.id]
    with Session() as session:
        orders = database.get_history(session, user_id)
    if orders:
        user_orders[user_id] = {'orders': orders, 'index': 0}
        send_order_info(callback.message.chat.id, user_id, 0, callback.message.message_id)
    else:
        bot.send_message(callback.message.chat.id, "У вас нет заказов.")


@bot.callback_query_handler(func=lambda callback: callback.data == 'exit')
def callback_exit(callback):
    del authorized_users[callback.message.chat.id]
    bot.send_message(callback.message.chat.id, 'Выход выполнен успешно! Возвращайтесь скорее...')


@bot.callback_query_handler(func=lambda callback: callback.data in ('prev_order', 'next_order'))
def button(callback):
    user_id = authorized_users[callback.message.chat.id]
    direction = callback.data
    orders_data = user_orders.get(user_id)
    if orders_data:
        index = orders_data['index']
        orders = orders_data['orders']
        if direction == 'prev_order':
            index -= 1
        elif direction == 'next_order':
            index += 1
        if 0 <= index < len(orders):
            user_orders[user_id]['index'] = index
            send_order_info(callback.message.chat.id, user_id, index, callback.message.message_id)
        else:
            bot.answer_callback_query(callback.id, "Нет больше заказов.")
    else:
        bot.answer_callback_query(callback.id, "У вас нет заказов.")


@bot.callback_query_handler(func=lambda callback: callback.data in ('prev_trip', 'next_trip'))
def button_trip(callback):
    chat_id = callback.message.chat.id
    message_id = user_search[chat_id]['sent_message']
    direction = callback.data
    search_data = user_search.get(chat_id)
    trips = search_data['trips']
    index = search_data['index']
    if direction == 'prev_trip':
        index -= 1
    elif direction == 'next_trip':
        index += 1

    if 0 <= index < len(trips):
        search_data['index'] = index
        send_trip_info(chat_id, index, message_id)
    else:
        bot.answer_callback_query(callback.id, "Нет больше поездок.")


@bot.callback_query_handler(func=lambda callback: callback.data == 'check_trip')
def show_trip(callback):
    choose_trip[callback.message.chat.id] = {}

    search_data = user_search.get(callback.message.chat.id)
    trips = search_data['trips']
    trip = trips[search_data['index']]

    choose_trip[callback.message.chat.id]['trip'] = trip

    message = f"ID поездки: {trip.id_trip}\n" \
              f"Отправление: {trip.t_from} - {trip.time_s}\n" \
              f"Прибытие: {trip.t_to} - {trip.time_e}\n" \
              f"Поезд: {trip.train_id}\n\n" \
              f"Выберите тип вагона:"

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Купе', callback_data='купе')
    btn2 = types.InlineKeyboardButton('Плацкарт', callback_data='плацкарт')
    markup.row(btn1, btn2)

    bot.send_message(callback.message.chat.id, message, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data in ('купе', 'плацкарт'))
def callback_train(callback):
    search_data = user_search.get(callback.message.chat.id)
    trips = search_data['trips']
    trip = trips[search_data['index']]
    type_car = callback.data
    with Session() as session:
        cars = database.get_cars(session, trip.id_route, type_car)
    if cars:
        keyboard = []
        for car in cars:
            but = types.InlineKeyboardButton(f'Вагон {car.id_car}', callback_data=f'car_{car.id_car}')
            keyboard.append([but])
        reply_markup = types.InlineKeyboardMarkup(keyboard)
        bot.send_message(callback.message.chat.id, 'Выберите вагон:', reply_markup=reply_markup)
    else:
        bot.send_message(callback.message.chat.id, 'Нет доступных вагонов данного типа.')


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('car_'))
def callback_cars(callback):
    car_id = callback.data.split('_')[1]
    with Session() as session:
        places = database.get_places(session, car_id)
    choose_trip[callback.message.chat.id]['places'] = places
    choose_trip[callback.message.chat.id]['index'] = 0
    choose_trip[callback.message.chat.id]['car'] = car_id

    places_keyboard = []
    for i in range(min(4, len(places))):
        places_keyboard.append(types.InlineKeyboardButton(places[i].id_place,
                                                          callback_data=f'place_{places[i].id_place}'))

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('<', callback_data='prev_places'),
        *places_keyboard,
        types.InlineKeyboardButton('>', callback_data='next_places')
    )

    bot.send_message(callback.message.chat.id, 'Выберите место:', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'prev_places' or callback.data == 'next_places')
def callback_change_places(callback):
    chat_id = callback.message.chat.id

    trip_data = choose_trip[chat_id]
    places = trip_data['places']
    index = trip_data['index']

    if callback.data == 'prev_places':
        index -= 4
    elif callback.data == 'next_places':
        index += 4
    if index == -4 or index > len(places):
        bot.answer_callback_query(callback.id, "Нет доступных мест")
    else:
        trip_data['index'] = index

        places_keyboard = []
        for i in range(index, min(index + 4, len(places))):
            places_keyboard.append(
                types.InlineKeyboardButton(places[i].id_place, callback_data=f'place_{places[i].id_place} '
                                                                             f'cost_{places[i].cost_place}'))

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('<', callback_data='prev_places'),
            *places_keyboard,
            types.InlineKeyboardButton('>', callback_data='next_places')
        )

        bot.edit_message_text(chat_id=chat_id, message_id=callback.message.message_id, text='Выберите место:',
                              reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('place_'))
def callback_place(callback):
    chat_id = callback.message.chat.id

    place_id = int(callback.data.split(' ')[0].split('_')[1])
    cost_place = int(callback.data.split(' ')[1].split('_')[1])

    choose_trip[callback.message.chat.id]['place'] = place_id
    choose_trip[callback.message.chat.id]['cost'] = cost_place

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Оформить', callback_data='buy'))
    trip = choose_trip[chat_id]['trip']
    bot.send_message(chat_id, f'Сформирована поездка:\n\n'
                                               f'Отправление: {trip.t_from} - {trip.data_s} - {trip.time_s}\n'
                                               f'Прибытие: {trip.t_to} - {trip.data_e} - {trip.time_e}\n\n'
                                               f'Поезд: {trip.train_id}\n'
                                               f'Вагон: {choose_trip[chat_id]["car"]}\n'
                                               f'Место: {choose_trip[chat_id]["place"]}\n\n'
                                               f'Стоимость: {choose_trip[chat_id]["cost"]}',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'buy')
def callback_buy(callback):
    chat_id = callback.message.chat.id
    if chat_id in authorized_users:
        try:
            invoice = types.InlineKeyboardMarkup()
            invoice.add(types.InlineKeyboardButton(text="Оплатить", pay=True))
            trip = choose_trip[callback.message.chat.id]['trip']

            provider_data = {
                'receipt': {
                    'items': [
                        {
                            'description': 'Железнодорожный билет',
                            'quantity': '1.00',
                            'amount': {
                                'value': 100.00,
                                'currency': 'RUB'
                            },
                            'vat_code': 1
                        }
                    ]
                },
                "test": True
            }

            bot.send_invoice(callback.message.chat.id,
                             title='Железнодорожный билет',
                             description=f'Отправление: {trip.t_from} - {trip.data_s} - {trip.time_s}\n'
                                               f'Прибытие: {trip.t_to} - {trip.data_e} - {trip.time_e}\n\n'
                                               f'Поезд: {trip.train_id}\n'
                                               f'Вагон: {choose_trip[callback.message.chat.id]["car"]}\n'
                                               f'Место: {choose_trip[callback.message.chat.id]["place"]}\n',
                             invoice_payload='invoice_payload',
                             provider_token=Settings.PAYMENT_TOKEN,
                             currency='RUB',
                             prices=[types.LabeledPrice('Билет', amount=100 * 100)],
                             reply_markup=invoice,
                             need_email=True,
                             send_email_to_provider=True,
                             provider_data=json.dumps(provider_data))
        except Exception as e:
            print(f'Ошибка при обработке платежа: {e}')
    else:
        bot.send_message(chat_id, 'Необходимо авторизоваться. Введите вашу почту, чтобы продолжить.')
        bot.register_next_step_handler(callback.message, handle_user_email)


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    try:
        chat_id = message.chat.id
        with Session() as session:
            trip = choose_trip[chat_id]["trip"]
            place = choose_trip[chat_id]["place"]
            cost = choose_trip[chat_id]["cost"]
            client = authorized_users[chat_id]
            order_id = database.insert_order(session=session, place_id=place, total_cost=cost, route_id=trip.id_route,
                                             client_id=client)
        bot.send_message(chat_id, f'Спасибо за оплату! Идентификатор заказа: {order_id}')
    except Exception as e:
        print(f'Ошибка при обработке платежа!\nИнформация об ошибке: {e}')


@bot.callback_query_handler(func=lambda callback: callback.data == 'personal')
def callback_personal(callback):
    user_id = authorized_users[callback.message.chat.id]
    with Session() as session:
        user = database.get_user_for_id(user_id, session)
    show_user_info(callback.message, user)


def handle_user_email(message):
    user_email = message.text
    with Session() as session:
        user = database.get_user_for_email(user_email, session)
    if user is not None:
        show_user_info(message, user)
        authorized_users[message.chat.id] = user.id_client
        if message.chat.id in choose_trip:
            bot.send_message(message.chat.id, 'Теперь можете приступать к оформлению заказа. Повторите нажатие на кнопку "Оформить"')
    else:
        bot.send_message(message.chat.id, 'Пользователь не найден')


def show_user_info(message, user):
    markup = types.InlineKeyboardMarkup()
    btn_history = types.InlineKeyboardButton('История заказов', callback_data='history')
    btn_exit = types.InlineKeyboardButton('Выйти', callback_data='exit')
    markup.row(btn_history, btn_exit)
    bot.send_message(message.chat.id, f'Персональная информация:\n\n'
                                      f'{user.last_name} {user.first_name} {user.patronymic}\n\n'
                                      f'Контакты:\n'
                                      f'Почта - {user.email}\n'
                                      f'Телефон - {user.phone}', reply_markup=markup)


def send_order_info(chat_id, user_id, order_index, message_id):
    orders_data = user_orders[user_id]
    orders = orders_data['orders']
    order = orders[order_index]
    text = f"ID заказа: {order.id_order}\n\n" \
              f"Дата заказа: {order.date_order}\n\n" \
              f"Отправление: {order.data_s} - {order.town_s}\n" \
              f"Прибытие: {order.data_e} - {order.town_e}\n\n" \
              f"Стоимость заказа: {order.cost_order}\n\n" \
              f"{order_index+1}/{len(orders)}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("Вернуться", callback_data=f"personal"),
        telebot.types.InlineKeyboardButton("Назад", callback_data=f"prev_order"),
        telebot.types.InlineKeyboardButton("Вперед", callback_data=f"next_order")
    )
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)


def send_trip_info(chat_id, trip_index, message_id):
    search_data = user_search.get(chat_id)
    trips = search_data['trips']
    trip = trips[trip_index]

    message = f"ID поездки: {trip.id_route}\n" \
              f"Отправление: {trip.t_from} - {trip.time_s}\n" \
              f"Прибытие: {trip.t_to} - {trip.time_e}\n" \
              f"{trip_index+1}/{len(trips)}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("Назад", callback_data=f"prev_trip"),
        telebot.types.InlineKeyboardButton("Посмотреть", callback_data=f"check_trip"),
        telebot.types.InlineKeyboardButton("Вперед", callback_data=f"next_trip")
    )
    try:
        if message_id:
            bot.edit_message_text(message, chat_id, message_id, reply_markup=markup)
        else:
            sent_message = bot.send_message(chat_id, message, reply_markup=markup).message_id
            user_search[chat_id]['sent_message'] = sent_message
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error editing message: {e}")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            print('Troubles with Telegram API: ', error)
