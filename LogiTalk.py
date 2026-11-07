from customtkinter import *
from socket import *
from PIL import Image
from tkinter import filedialog, messagebox
from queue import Queue
import threading, json, base64, io
HOST, PORT = '192.168.1.164', 12345  # IP та порт сервера
TITLE, COLOR, MODE = ('GameChat — Апгрейдер', '#2563eb', 'dark')
messages = Queue()
client_socket = None

def add_message(message, image=None):
    label = CTkLabel(tbx, text=message, image=image, compound='top', wraplength=400)
    label.image = image
    label.pack(anchor='w', padx=10, pady=5)

def send_data(data):
    try:
        client_socket.sendall((json.dumps(data, ensure_ascii=False) + '\n').encode('utf-8'))
        return True
    except OSError:
        messagebox.showerror('З’єднання', 'Сервер недоступний. Перезапусти чат.')
        return False

def send_msg(event=None):
    message = entry.get().strip()
    if message:
        send_data({'type': 'text', 'text': message})
        entry.delete(0, 'end')

def show_photo(author, data):
    photo = Image.open(io.BytesIO(data)).convert('RGB')
    photo.thumbnail((280, 200))
    image = CTkImage(photo, size=photo.size)
    add_message(author + ': фото', image)

def open_photo(path=None):
    path = path or filedialog.askopenfilename(filetypes=[('Фото', '*.png *.jpg *.jpeg')])
    if not path:
        return
    photo = Image.open(path).convert('RGB')
    photo.thumbnail((640, 480))
    memory = io.BytesIO()
    photo.save(memory, format='JPEG', quality=80)
    photo_text = base64.b64encode(memory.getvalue()).decode()
    send_data({'type': 'image', 'data': photo_text})

def handle_message(data):
    if data['type'] == 'text':
        add_message(data['username'] + ': ' + data['text'])
    elif data['type'] == 'image':
        show_photo(data['username'], base64.b64decode(data['data']))
    else:
        add_message(data.get('text', ''))

def receive_messages():
    try:
        for line in client_socket.makefile('r', encoding='utf-8'):
            messages.put(json.loads(line))
    except (OSError, ValueError):
        pass
    messages.put({'type': 'system', 'text': 'Сервер відключився. Перезапусти чат.'})

def check_messages():
    while not messages.empty():
        handle_message(messages.get())
    win.after(80, check_messages)

def register():
    global username, client_socket
    username = name_entry.get().strip()[:30]
    if not username:
        return
    try:
        client_socket = create_connection((HOST, PORT), timeout=3)
        client_socket.settimeout(None)
    except OSError:
        messagebox.showerror('Сервер', 'Не вдалося підключитися. Перевір IP та запуск сервера.')
        return
    if not send_data({'type': 'join', 'username': username}):
        client_socket.close()
        return
    registration.destroy()
    chat.pack(fill='both', expand=True, padx=12, pady=12)
    win.title(TITLE + ' — ' + username)
    threading.Thread(target=receive_messages, daemon=True).start()

# МОЯ ТЕМА: апгрейдер меча
from random import randint
coins, level = 100, 0
def upgrade():
    global coins, level
    price = 20 + level * 10
    if coins < price:
        result.configure(text='Не вистачає монет. Натисни Бонус!')
        return
    coins -= price
    if randint(1, 100) <= 70:
        level += 1
        text = 'Успіх! Меч покращено!'
    else:
        text = 'Невдача. Рівень меча збережено.'
    wallet.configure(text=f'Монети: {coins} | Меч +{level} | Ціна: {20 + level * 10}')
    result.configure(text=text)
    send_data({'type': 'text', 'text': f'[Апгрейдер] {text} Меч +{level}. Монети: {coins}'})
def bonus():
    global coins
    coins += 20
    send_data({'type': 'text', 'text': f'[Апгрейдер] Бонус +20. Монети: {coins}'})
    wallet.configure(text=f'Монети: {coins} | Меч +{level} | Ціна: {20 + level * 10}')

set_appearance_mode(MODE)
win = CTk()
win.geometry('660x560')
win.title(TITLE)
registration = CTkFrame(win)
registration.pack(expand=True)
CTkLabel(registration, text=TITLE + ': введи ім’я').pack(padx=15, pady=10)
name_entry = CTkEntry(registration, placeholder_text='Ім’я (до 30 символів)')
name_entry.pack(padx=15, pady=10)
CTkButton(registration, text='Увійти', command=register, fg_color=COLOR).pack(pady=10)
chat = CTkFrame(win)
title_label = CTkLabel(chat, text=TITLE, font=('Arial', 24, 'bold'), text_color=COLOR)
title_label.pack(pady=8)
wallet = CTkLabel(chat, text='Монети: 100 | Меч +0 | Ціна: 20')
wallet.pack()
result = CTkLabel(chat, text='Шанс покращення: 70%. Натисни Покращити меч!')
result.pack()
tools = CTkFrame(chat)
tools.pack(pady=5)
CTkButton(tools, text='Покращити меч', command=upgrade, fg_color=COLOR).pack(side='left', padx=5)
CTkButton(tools, text='Бонус +20', command=bonus, fg_color=COLOR).pack(side='left', padx=5)
tbx = CTkScrollableFrame(chat)
tbx.pack(fill='both', expand=True, padx=8)
entry = CTkEntry(chat, placeholder_text='Повідомлення')
entry.pack(fill='x', padx=8, pady=8)
entry.bind('<Return>', send_msg)
CTkButton(chat, text='Надіслати', command=send_msg, fg_color=COLOR).pack(side='left', padx=8, pady=8)
CTkButton(chat, text='Фото', command=open_photo, fg_color=COLOR).pack(side='right', padx=8)
if __name__ == '__main__':
    check_messages()
    win.mainloop()