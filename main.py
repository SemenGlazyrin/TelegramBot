import telebot
from telebot import types
import asyncio
from telebot.async_telebot import AsyncTeleBot
from selenium import webdriver
from selenium.webdriver.common.by import By

bot = AsyncTeleBot('7317266086:AAGLD4wYYy3N45il6XbBI3OeS_AWMZc-vwU')

tracked_products = []
previous_info = []

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, "Выберите действие:",
                     reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True).add(
                            types.KeyboardButton("Частота проверки"),
                            types.KeyboardButton("Просмотреть статус товаров"),
                            types.KeyboardButton("Начинаем")
                     ))

@bot.message_handler(regexp="Частота проверки")
async def settings(message):
    await bot.send_message(message.chat.id, "Цены обновляются автоматически, когда пользователи делают похожий запрос ")
    await start(message)

@bot.message_handler(regexp="Просмотреть статус товаров")
async def show_products(message):
    global tracked_products

    if len(tracked_products[1]) != 0:
        for j in range(0, len(tracked_products[1])):
            await bot.send_message(message.chat.id, "Отслеживаемые товары:\n" + tracked_products[1][j])
    else:
        await bot.send_message(message.chat.id, "У вас нет отслеживаемых товаров.")

    await start(message)

@bot.message_handler(regexp="Начинаем")
async def start_tracking(message):
    await bot.send_message(message.chat.id, "Какой товар вы бы хотели найти?\nВведите название товара:",
                           reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
                               types.KeyboardButton("Главное меню")))

    bot.register_message_handler(find_product)# bot.register_message_handler(message, find_product)

async def get_product_info(message):
    product_names = []
    urls = []
    prices = []

    options = webdriver.ChromeOptions()
    options.headless = True

    driver = webdriver.Chrome(options=options)
    driver.get(f"https://sbermarket.ru/multisearch?q={message}")

    await asyncio.sleep(5)

    products = driver.find_elements(By.CLASS_NAME, "ProductCardLink_root__69qxV")

    for product in products:

        price_string = product.find_element(By.CLASS_NAME, "CommonProductCard_priceText__bW6F9").text
        product_names.append(product.find_element(By.CLASS_NAME, "ProductCard_titleContainer__5SZT1").text)

        urls.append(product.get_attribute("href"))

        price_string = price_string.replace("Цена за 1 шт.\n", "")
        price_string = price_string.replace("Цена со скидкой за 1 шт.\n", "")

        price_string = price_string.replace(" ", "")

        price_string = price_string.replace("₽", "")

        prices.append(float(price_string.replace(",", ".")))

    driver.quit()

    print(len(product_names))

    return [product_names, prices, urls]

async def check_other_price(message):
    if message in tracked_products[0]:
        tracked_products[1][tracked_products[0].index(message)] = get_product_info(message)

async def text(info):
    t1 = ""
    t2 = ""
    prices = []

    for i in range(0, len(info[0])):
        if i <= len(info[0]) // 2:
            t1 += info[0][i] + '\n' + str(info[1][i]) + " рублей" + '\n' + info[2][i] + "\n\n"
        else:
            t2 += info[0][i] + '\n' + str(info[1][i]) + " рублей" + '\n' + info[2][i] + "\n\n"

    return [t1,t2]

async def find_product(message):
    global previous_info

    if message.text == "Главное меню":
        await start(message)
    elif message.text == "Да":
        await save_product(message)
    elif message.text == "Нет":
        await bot.send_message(message.chat.id, "Возвращаемся к поиску товара.")
    else:
        info = await get_product_info(message.text)

        mes = await text(info)


        if len(info[0]) != 0:
            min_i = info[1].index(min(info[1]))
            previous_info = [message, info[0][min_i] + '\n' + str(min(info[1])) + " рублей" + '\n' + info[2][min_i] + "\n\n"]

            await bot.send_message(message.chat.id, "По вашему запросу, с минимальной ценой, нашелся: \n" + info[0][min_i] + '\n' + str(info[1][min_i]) + " рублей" + '\n' + info[2][min_i] + "\n\n")

            await bot.send_message(message.chat.id, "Желаете ли вы отслеживать данный товар?",
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True).add(
                                 types.KeyboardButton("Да"),
                                  types.KeyboardButton("Нет")
                         ))
            bot.register_message_handler(save_product, regexp="Да")
        else:
            await bot.send_message(message.chat.id, "Вашего товара нет, введите название товара еще раз:")

async def save_product(message):
    global tracked_products
    global previous_info

    if message.text == "Да":
        print(previous_info)
        tracked_products.append(previous_info)
        await bot.send_message(message.chat.id, "Ваш товар был сохранен.")
    await start(message)

asyncio.run(bot.polling(none_stop=True, interval=0))