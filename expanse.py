import telebot
from telebot import types
import sqlite3
from datetime import datetime


bot = telebot.TeleBot("7384864093:AAHLe0c-h6HzhRQx2CDIbDjhpbQ1DaiZK3Q")

@bot.message_handler(commands=['start','hi','hello', 'add'])
def start(message):
    #bot.send_message(message.chat.id, "Welcome! I'll help you to track your expanses.  ")

    markup = types.InlineKeyboardMarkup(row_width=4)
    groceries = types.InlineKeyboardButton('Groceries🥦', callback_data='groceries')
    shopping = types.InlineKeyboardButton('Shopping🛍', callback_data='shopping')
    diningOut = types.InlineKeyboardButton('Dining out🍝', callback_data='dining_out')
    transportation = types.InlineKeyboardButton('Travel🚖', callback_data='transportation')
    entertainment = types.InlineKeyboardButton('Entertainment🎠', callback_data='entertainment')
    subscriptions = types.InlineKeyboardButton('Subscriptions🔌', callback_data='subscriptions')
    savingsAndInvestments = types.InlineKeyboardButton('Savings & Investments🧠', callback_data='savings')
    other = types.InlineKeyboardButton('Other🗑', callback_data='other')
    markup.add(groceries, shopping, diningOut, transportation, entertainment,
               subscriptions, savingsAndInvestments, other)
    bot.send_message(message.chat.id, 'Pick a category', reply_markup=markup)
    bot.register_next_step_handler(message,start)



def setup_database():
    #database setup
    conn = sqlite3.connect('venv/expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            description TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

setup_database()



@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    category = call.data
    bot.send_message(call.message.chat.id, f"You selected {category}. Please enter the amount (and optionally a description).")
    bot.register_next_step_handler(call.message, lambda msg: save_expense(msg, category))

def save_expense(message, category):
    try:
        user_input = message.text.split(maxsplit=1)
        amount = float(user_input[0])
        description = user_input[1] if len(user_input) > 1 else " "
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save to database
        conn = sqlite3.connect('venv/expenses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO expenses (user_id, category, amount, description, date) VALUES (?, ?, ?, ?, ?)',
                       (message.chat.id, category, amount, description, date))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"Expense recorded: {amount} for {category} ({description}).")
    except Exception as e:
        bot.send_message(message.chat.id, "Error: Please enter a valid amount. Example: `20 lunch`")



@bot.message_handler(commands=['view'])
def view_expenses(message):
    conn = sqlite3.connect('/Users/alisasamohval/IdeaProjects/FinanceTelegramBot/venv/expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, amount, description, date FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10', (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        response = "Your recent expenses:\n"
        for row in rows:
            response += f"{row[3]}: {row[0]} - {row[1]} ({row[2]})\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "No expenses recorded yet.")






bot.polling(none_stop=True)

