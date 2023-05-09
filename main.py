import telebot
import config
from telebot import types
from create_profile import create_profile, process_create_profile_step
from edit_profile import edit_profile, process_edit_choice
from delete_profile import delete_profile
from search_companion import search_companions, search_companion_handler, select_companions
from database import get_selected_companions, add_selected_companion, get_companion_by_id, create_selected_companions_table
create_selected_companions_table()
# Создаем экземпляр бота
bot = telebot.TeleBot(config.TOKEN)

# Создаем клавиатуру с функциями бота
def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add('Создать профиль', 'Редактировать профиль')
    keyboard.add('Поиск попутчиков', 'Мои попутчики')
    keyboard.add('Удалить профиль', 'Создать групповой чат')
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Добро пожаловать в бота для поиска попутчиков в путешествиях!',
                     reply_markup=create_keyboard())

user_states = {}

# Обработчик для текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    chat_id = message.chat.id

    if chat_id in user_states:
        process_create_profile_step(user_states, message, bot)
    else:
        if message.text == 'Создать профиль':
            create_profile(user_states, message, bot)
        elif message.text == 'Редактировать профиль':
            edit_profile(message, user_states, bot)
        elif message.text == 'Удалить профиль':
            delete_profile(message, bot)
        elif message.text == 'Поиск попутчиков':
            search_companion_handler(message, bot)
        # Добавьте обработчики для других функций бота здесь

# Обработчик для callback-данных инлайн-клавиатуры
@bot.callback_query_handler(func=lambda call: call.data.startswith("search_criteria"))
def handle_callback_query(call):
    chat_id = call.message.chat.id
    _, criteria_type, criteria_value = call.data.split(":")

    if criteria_type == "travel_type":
        criteria = {
            'travel_type': criteria_value
        }

        # Добавляем отладочное сообщение
        bot.send_message(chat_id, f"Ищем попутчиков с типом отдыха: {criteria['travel_type']}")

        companions = search_companions(chat_id, criteria)

        # Добавляем отладочное сообщение
        bot.send_message(chat_id, f"Найдено попутчиков: {len(companions)}")

        if companions:
            for companion in companions:
                companion_info = f"Имя: {companion[2]}\nВозраст: {companion[3]}\nПол: {companion[4]}\nСтраны и города: {companion[5]}\nТип отдыха: {companion[6]}\nКонтактная информация: {companion[7]}"
                bot.send_message(chat_id, companion_info)
                select_companions(chat_id, companions, bot)
        else:
            bot.send_message(chat_id, "К сожалению, не удалось найти подходящих попутчиков.")

selected_companions = {}

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("select_companion") or call.data == "finish_selecting_companions")
def handle_select_companion_callback(call):
    chat_id = call.message.chat.id

    if call.data == "finish_selecting_companions":
        selected_companions = get_selected_companions(chat_id)

        if not selected_companions:
            bot.send_message(chat_id, "Вы не выбрали ни одного попутчика.")
        else:
            for companion_id in selected_companions:
                companion = get_companion_by_id(companion_id)
                if companion:
                    companion_info = f"Имя: {companion[2]}\nВозраст: {companion[3]}\nПол: {companion[4]}\nСтраны и города: {companion[5]}\nТип отдыха: {companion[6]}\nКонтактная информация: {companion[7]}"
                    bot.send_message(chat_id, f"Контактная информация попутчика:\n{companion_info}")
                else:
                    bot.send_message(chat_id, f"Попутчик с ID {companion_id} не найден.")
    else:
        companion_id = int(call.data.split(":")[-1])
        add_selected_companion(chat_id, companion_id)
        bot.answer_callback_query(call.id, "Попутчик добавлен в выбранные.")

# Запускаем бота
bot.polling(none_stop=True)