import telebot
from telebot import types
import sqlite3
import config
from datetime import datetime, timedelta


bot = telebot.TeleBot(config.TOKEN)


# Function to set up the database
def setup_database():
    conn = sqlite3.connect('expenses.db')
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


# Start command handler
@bot.message_handler(commands=['start'])
def start(message):
    # Initialize the database
    setup_database()

    # Send a welcome message
    bot.send_message(message.chat.id, "Welcome! I'll help you track your expenses. Use the buttons below to add expenses.")

    # Call the /add functionality to display category options
    add_expenses(message)


# Add expenses function (category selection)
def add_expenses(message):
    # Create the inline keyboard for expense categories
    markup = types.InlineKeyboardMarkup(row_width=2)
    groceries = types.InlineKeyboardButton('Groceries🥦', callback_data='groceries')
    shopping = types.InlineKeyboardButton('Shopping🛍', callback_data='shopping')
    dining_out = types.InlineKeyboardButton('Dining out🍝', callback_data='dining_out')
    transportation = types.InlineKeyboardButton('Travel🚖', callback_data='transportation')
    entertainment = types.InlineKeyboardButton('Entertainment🎠', callback_data='entertainment')
    subscriptions = types.InlineKeyboardButton('Subscriptions🔌', callback_data='subscriptions')
    savings = types.InlineKeyboardButton('Savings & Investments🧠', callback_data='savings')
    other = types.InlineKeyboardButton('Other🗑', callback_data='other')
    markup.add(groceries, shopping, dining_out, transportation, entertainment, subscriptions, savings, other)

    # Display the inline keyboard
    bot.send_message(message.chat.id, 'Pick a category to add an expense:', reply_markup=markup)





# Function to save an expense
def save_expense(message, category):
    try:
        user_input = message.text.split(maxsplit=1)
        amount = float(user_input[0])
        description = user_input[1] if len(user_input) > 1 else " "
        date = datetime.now().strftime('%B %d, %I:%M %p')

        # Save to the database
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO expenses (user_id, category, amount, description, date) VALUES (?, ?, ?, ?, ?)',
                       (message.chat.id, category, amount, description, date))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"Expense recorded: {amount} for {category} ({description}) on {date}.")
    except Exception as e:
        bot.send_message(message.chat.id, "Error: Please enter a valid amount. Example: `20 lunch`")


# View recent expenses without deletion option
@bot.message_handler(commands=['recent'])
def view_recent_expenses(message):
    conn = sqlite3.connect('expenses.db')
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


# View expenses for today
@bot.message_handler(commands=['today'])
def view_today_expenses(message):
    today = datetime.now().strftime('%B %d')  # Format: "January 08"
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, amount, description, date FROM expenses WHERE user_id = ? AND date LIKE ? ORDER BY date DESC',
                   (message.chat.id, f'{today}%'))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        total = sum(row[1] for row in rows)  # Calculate total expenses
        response = f"Your expenses for today ({today}):\n"
        for row in rows:
            response += f"{row[3]}: {row[0]} - {row[1]} ({row[2]})\n"
        response += f"\nTotal: {total}"  # Add total at the bottom
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "No expenses recorded today.")


# View expenses for this week
@bot.message_handler(commands=['week'])
def view_week_expenses(message):
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Start of the week (Monday)
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, amount, description, date FROM expenses WHERE user_id = ? AND date >= ? ORDER BY date DESC',
                   (message.chat.id, start_of_week.strftime('%B %d, %Y')))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        total = sum(row[1] for row in rows)  # Calculate total expenses
        response = f"Your expenses for this week (since {start_of_week.strftime('%B %d, %Y')}):\n"
        for row in rows:
            response += f"{row[3]}: {row[0]} - {row[1]} ({row[2]})\n"
        response += f"\nTotal: {total}"  # Add total at the bottom
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "No expenses recorded this week.")


# View expenses for this month
@bot.message_handler(commands=['month'])
def view_month_expenses(message):
    today = datetime.now()
    start_of_month = today.replace(day=1)  # Start of the current month
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, amount, description, date FROM expenses WHERE user_id = ? AND date >= ? ORDER BY date DESC',
                   (message.chat.id, start_of_month.strftime('%B %d, %Y')))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        total = sum(row[1] for row in rows)  # Calculate total expenses
        response = f"Your expenses for this month (since {start_of_month.strftime('%B %d, %Y')}):\n"
        for row in rows:
            response += f"{row[3]}: {row[0]} - {row[1]} ({row[2]})\n"
        response += f"\nTotal: {total}"  # Add total at the bottom
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "No expenses recorded this month.")

# View recent expenses with delete option
@bot.message_handler(commands=['deleterecent'])
def view_and_delete_recent_expenses(message):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, category, amount, description, date FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10', (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        for row in rows:
            expense_id, category, amount, description, date = row
            text = f"{date}: {category} - {amount} ({description})"

            # Add a delete button for each expense
            markup = types.InlineKeyboardMarkup()
            delete_button = types.InlineKeyboardButton(
                text="Delete ❌",
                callback_data=f"delete_{expense_id}"
            )
            markup.add(delete_button)

            bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "No expenses recorded yet.")

# View expenses by category for this month
@bot.message_handler(commands=['viewByCategory'])
def view_by_category(message):
    # Ask the user to pick a category
    markup = types.InlineKeyboardMarkup(row_width=2)
    groceries = types.InlineKeyboardButton('Groceries🥦', callback_data='groceries')
    shopping = types.InlineKeyboardButton('Shopping🛍', callback_data='shopping')
    dining_out = types.InlineKeyboardButton('Dining out🍝', callback_data='dining_out')
    transportation = types.InlineKeyboardButton('Travel🚖', callback_data='transportation')
    entertainment = types.InlineKeyboardButton('Entertainment🎠', callback_data='entertainment')
    subscriptions = types.InlineKeyboardButton('Subscriptions🔌', callback_data='subscriptions')
    savings = types.InlineKeyboardButton('Savings & Investments🧠', callback_data='savings')
    other = types.InlineKeyboardButton('Other🗑', callback_data='other')
    markup.add(groceries, shopping, dining_out, transportation, entertainment, subscriptions, savings, other)

    # Display the inline keyboard
    bot.send_message(message.chat.id, 'Pick a category to view expenses for this month:', reply_markup=markup)


# Generate monthly report
@bot.message_handler(commands=['report'])
def generate_monthly_report(message):
    today = datetime.now()
    start_of_month = today.replace(day=1)  # Start of the current month

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Get all expenses for the month
    cursor.execute('''
        SELECT category, amount, description, date 
        FROM expenses 
        WHERE user_id = ? AND date >= ? 
        ORDER BY date DESC''',
                   (message.chat.id, start_of_month.strftime('%B %d, %Y')))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "No expenses recorded this month.")
        conn.close()
        return

    # Calculate basic statistics
    total_expenses = sum(row[1] for row in rows)
    num_transactions = len(rows)
    avg_transaction = total_expenses / num_transactions

    # Calculate category-wise totals and percentages
    category_totals = {}
    for row in rows:
        category = row[0]
        amount = row[1]
        category_totals[category] = category_totals.get(category, 0) + amount

    # Find highest and lowest expenses
    highest_expense = max(rows, key=lambda x: x[1])
    lowest_expense = min(rows, key=lambda x: x[1])

    # Generate the report
    response = f"📊 Monthly Report for {start_of_month.strftime('%B %Y')}\n\n"

    # Overall summary
    response += "💰 OVERALL SUMMARY\n"
    response += f"Total Expenses: {total_expenses:.2f}\n"
    response += f"Number of Transactions: {num_transactions}\n"
    response += f"Average Transaction: {avg_transaction:.2f}\n\n"

    # Category breakdown
    response += "📈 CATEGORY BREAKDOWN\n"
    for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_expenses) * 100
        response += f"{category}: {amount:.2f} ({percentage:.1f}%)\n"

    # Highlights
    response += "\n🔍 HIGHLIGHTS\n"
    response += f"Highest Expense: {highest_expense[1]:.2f} ({highest_expense[0]}) on {highest_expense[3]}\n"
    response += f"Lowest Expense: {lowest_expense[1]:.2f} ({lowest_expense[0]}) on {lowest_expense[3]}\n"

    # Daily average
    days_in_month = (today - start_of_month).days + 1
    daily_average = total_expenses / days_in_month
    response += f"\n📅 DAILY AVERAGE\n"
    response += f"Average Daily Spending: {daily_average:.2f}\n"

    # Most active category
    most_active_category = max(category_totals.items(), key=lambda x: x[1])[0]
    response += f"\n🏆 Most Spent Category: {most_active_category}\n"

    # Get spending trend (compare with previous month if available)
    previous_month = start_of_month - timedelta(days=1)
    previous_month_start = previous_month.replace(day=1)

    cursor.execute('''
        SELECT SUM(amount)
        FROM expenses 
        WHERE user_id = ? AND date >= ? AND date < ?''',
                   (message.chat.id, previous_month_start.strftime('%B %d, %Y'),
                    start_of_month.strftime('%B %d, %Y')))

    previous_total = cursor.fetchone()[0]
    conn.close()

    if previous_total:
        change = ((total_expenses - previous_total) / previous_total) * 100
        trend = "📈" if change > 0 else "📉"
        response += f"\n📊 MONTH-OVER-MONTH COMPARISON\n"
        response += f"Previous Month Total: {previous_total:.2f}\n"
        response += f"Change: {change:+.1f}% {trend}\n"

    bot.send_message(message.chat.id, response)

# Callback query handler for category selection in /viewByCategory
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Handle delete callbacks
    if call.data.startswith('delete_'):
        expense_id = int(call.data.split('_')[1])
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?',
                       (expense_id, call.message.chat.id))
        conn.commit()
        conn.close()

        # Update the message to show it's deleted
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"{call.message.text}\n[DELETED]"
        )
        bot.answer_callback_query(call.id, "Expense deleted!")
        return

    # Handle category selection for adding expenses
    if call.data in ['groceries', 'shopping', 'dining_out', 'transportation',
                     'entertainment', 'subscriptions', 'savings', 'other']:
        category = call.data
        # Check if this is for viewing or adding
        if call.message.text.startswith('Pick a category to view'):
            # View expenses for category
            today = datetime.now()
            start_of_month = today.replace(day=1)

            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, amount, description, date 
                FROM expenses 
                WHERE user_id = ? AND category = ? AND date >= ? 
                ORDER BY date DESC''',
                           (call.message.chat.id, category, start_of_month.strftime('%B %d, %Y')))
            rows = cursor.fetchall()
            conn.close()

            if rows:
                total = sum(row[1] for row in rows)  # Calculate total for category
                response = f"Your expenses for '{category}' this month (since {start_of_month.strftime('%B %d, %Y')}):\n"
                for row in rows:
                    response += f"{row[3]}: {row[0]} - {row[1]} ({row[2]})\n"
                response += f"\nTotal for {category}: {total}"  # Add category total
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=response)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=f"No expenses recorded for '{category}' this month.")
        else:
            # Add new expense
            bot.send_message(call.message.chat.id,
                             f"You selected {category}. Please enter the amount (and optionally a description).")
            bot.register_next_step_handler(call.message, lambda msg: save_expense(msg, category))


# Run the bot
bot.polling(none_stop=True)
