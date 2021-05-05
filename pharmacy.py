import telebot
import requests
from bs4 import BeautifulSoup
from config import TOKEN
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(TOKEN)


def get_instructions(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # получаем информацию о показаниях к применению
    item1 = soup.find("div", id="pokazaniya")
    indications = [indication.text for indication in item1.find_all("li")]

    # получаем информацию о режиме дозирования
    item2 = soup.find("div", id="rezhim-dozirovaniya")
    dosage = [paragraph.text for paragraph in item2.find_all("p")]

    # получаем информацию о противопоказаниях
    item3 = soup.find("div", id="protivopokazaniya-k-primeneniyu")
    contraindications = [contraindication.text for contraindication in item3.find_all("li")]

    return indications, dosage, contraindications


def parse(message):
    pills = {}
    pill = message.text
    print(pill)
    url = 'https://yandex.ru/health/apteki/'
    newUrl = f"{url}search?text={pill}"
    response = requests.get(newUrl)
    soup = BeautifulSoup(response.text, 'html.parser')

    if soup.find("div", class_="pharmacy-search-page__title").text == "Ничего не найдено":
        bot.send_message(message.chat.id, "Некорректное название")
        return

    items = soup.find_all("div", class_="pharmacy-search-page__search-item")
    for item in items:
        button = item.find("button", class_="pharmacy-button")
        if "_disabled" not in button.attrs["class"]:
            pill_name = item.find("a", class_="pharmacy-search-item__title").text
            pill_link = item.find("a", class_="pharmacy-search-item__image").attrs["href"]
            pill_info = item.find("div", class_="pharmacy-search-item__form").text
            pill_price = item.find("div", class_="pharmacy-product-variants__variant-price").text

            # сохраняем лекарство в список со всеми лекарствами
            pills.update({pill_name: {
                "pill name": pill_name,
                "pill link": pill_link,
                "pill info": pill_info,
                "pill price": pill_price,
            }})
            bot.send_message(message.chat.id, f"{pills[pill_name]['pill name']}({pills[pill_name]['pill info']}):"
                                              f" {pills[pill_name]['pill price']}.\n"
                                              f"<a href=\"{pills[pill_name]['pill link']}\">Ссылка на сайт</a>",
                             parse_mode='HTML', disable_web_page_preview=True, reply_markup=gen_markup())
    if len(pills) == 0:
        bot.send_message(message.chat.id, "Нет в наличии")


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, я pharmacy бот! Чтобы попасть в меню, введи /menu или напиши меню')
    menu(message)


@bot.message_handler(commands=['menu'])
def menu(message):
    menu_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    keys = ['Поиск лекарства', 'Другое']
    menu_keyboard.add(*keys)
    bot.send_message(message.chat.id, 'Что вас интересует?', reply_markup=menu_keyboard)


@bot.message_handler(func=lambda message: message.text is not None and message.text == 'Поиск лекарства')
def surname(message):
    bot.send_message(message.chat.id, 'Введите название лекарства: ', )
    bot.register_next_step_handler(message, parse)


@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, f'{message.location.latitude}, {message.location.longitude}')


def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Показания к применению", callback_data="cb_1"),
               InlineKeyboardButton("Противопоказания", callback_data="cb_2"),
               InlineKeyboardButton("Дозировка", callback_data="cb_3"))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    if call.data == "cb_1":
        bot.send_message(call.message.chat.id, )
    elif call.data == "cb_2":
        bot.send_message(call.message.chat.id, "Если есть непереносимость дискретки")
    elif call.data == "cb_3":
        bot.send_message(call.message.chat.id, "Слушать 1 лексию раз в день")


@bot.message_handler(func=lambda message: message.text is not None and message.text == 'Тест')
def message_handler(message):
    bot.send_message(message.chat.id, "Yes/no?", reply_markup=gen_markup())


bot.polling()
