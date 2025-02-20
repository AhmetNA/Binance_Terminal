import customtkinter as ctk
from tkinter import END
import json
import sys
import os
from Get_Price import *
from Binance_Client import *
import time


client = prepare_client()
root = ctk.CTk()

# Loads favorite coin data from a JSON file
def load_fav_coin():
    json_path = 'Binance_Terminal/app/fav_coins.json'
    with open(json_path, 'r') as file:
        return json.load(file)

def retrieve_coin_symbol(col):
    data = load_fav_coin()
    coins = data['coins']
    if col == -1:
        return data['dynamic_coin'][0]['symbol']
    else:
        return coins[col]['symbol']

# Dinamik coin bilgilerini ve aksiyon butonlarını gösteren yan paneli oluşturur.
def dynamic_coin_panel(root):
    side_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="transparent",
        width=100,
        height=300
    )
    side_frame.place(x = 600, y=25)
    side_inner = ctk.CTkFrame(side_frame, corner_radius=15, fg_color="#4A9195")
    side_inner.pack(expand=True, anchor="center")

    button_configs = [
        ("Hard Buy", hard_buy_button_click, "darkgreen"),
        ("Soft Buy", soft_buy_button_click, "green"),
        ("Soft Sell", soft_sell_button_click, "red"),
        ("Hard Sell", hard_sell_button_click, "darkred")
    ]
    
    for row in range(2):
        text, command, color = button_configs[row]
        for col in range(1):
            btn = ctk.CTkButton(
                side_inner,
                text=text,
                fg_color=color,
                text_color="white",
                corner_radius=12,
                width=70,
                height=30,
                command=lambda cmd=command, c=6: cmd(c)     # This coin is dynamic coin so its index is 6
            )
            btn.grid(row=row, column=col, padx=10, pady=10)
    
    coin_buttons = []
    coins = load_fav_coin()['dynamic_coin']
    for col in range(1):
        coin_text = f"{coins[col]['symbol']}\n{coins[col]['values']['current']}"
        btn = ctk.CTkButton(
            side_inner,
            text=coin_text,
            fg_color="gray",
            text_color="white",
            corner_radius=12,
            width=80,
            height=40
        )
        btn.grid(row=2, column=col, padx=13, pady=13)
        coin_buttons.append(btn)
        
    for row in range(2, 4):
        text, command, color = button_configs[row]
        for col in range(1):
            btn = ctk.CTkButton(
                side_inner,
                text=text,
                fg_color=color,
                text_color="white",
                corner_radius=12,
                width=70,
                height=30,
                command=lambda cmd=command, c=6: cmd(c)
            )
            btn.grid(row=row+1, column=col, padx=10, pady=10)
            
    def update_coin_prices():
        new_coins = load_fav_coin()['dynamic_coin']
        for i, btn in enumerate(coin_buttons):
            new_text = f"{new_coins[i]['symbol']}\n{new_coins[i]['values']['current']}"
            btn.configure(text=new_text)
        side_inner.after(1000, update_coin_prices)
        
    update_coin_prices()
    
    
def fav_coin_panel(root):
    top_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="transparent",
        width=100,
        height=50
    )
    top_frame.place(x=15, y=15)

    button_inner_frame = ctk.CTkFrame(
        top_frame,
        corner_radius=15,
        fg_color="#4A9195"
    )
    button_inner_frame.pack(expand=True, fill='both', padx=10, pady=10)

    # Dört tür işlem için buton tanımlamaları (4 satır)
    button_configs = [
        ("Hard Buy", hard_buy_button_click, "darkgreen"),
        ("Soft Buy", soft_buy_button_click, "green"),
        ("Soft Sell", soft_sell_button_click, "red"),
        ("Hard Sell", hard_sell_button_click, "darkred")
    ]

    # Üst iki satırdaki butonlar (2 satır x 5 sütun)
    for row in range(2):
        text, command, color = button_configs[row]
        for col in range(5):
            btn = ctk.CTkButton(
                button_inner_frame,
                text=text,
                fg_color=color,
                text_color="white",
                corner_radius=12,
                width=70,
                height=30,
                command=lambda cmd=command, c=col:  cmd(c)
            )
            btn.grid(row=row, column=col, padx=10, pady=10)

    # Coin bilgilerini gösteren butonlar için referansları saklayacağımız liste
    coin_buttons = []
    coins = load_fav_coin()['coins']
    for col in range(5):
        coin_text = f"{coins[col]['symbol']}\n{coins[col]['values']['current']}"
        btn = ctk.CTkButton(
            button_inner_frame,
            text=coin_text,
            fg_color="gray",
            text_color="white",
            corner_radius=12,
            width=80,
            height=40
            # Bu butonlara isterseniz bir command da ekleyebilirsiniz.
        )
        btn.grid(row=2, column=col, padx=13, pady=13)
        coin_buttons.append(btn)

    # Alt iki satırdaki butonlar (2 satır x 5 sütun) - grid row'ları 3 ve 4 olacak şekilde yerleştiriyoruz.
    for row in range(2, 4):
        text, command, color = button_configs[row]
        for col in range(5):
            btn = ctk.CTkButton(
                button_inner_frame,
                text=text,
                fg_color=color,
                text_color="white",
                corner_radius=12,
                width=70,
                height=30,
                command=lambda cmd=command , c=col: cmd(c)
            )
            btn.grid(row=row+1, column=col, padx=10, pady=10)

    # Coin butonlarındaki değerleri her 2 saniyede güncelleyecek fonksiyon
    def update_coin_prices():
        new_coins = load_fav_coin()['coins']
        for i, btn in enumerate(coin_buttons):
            new_text = f"{new_coins[i]['symbol']}\n{new_coins[i]['values']['current']}"
            btn.configure(text=new_text)
        # 2000 ms (2 saniye) sonra tekrar çağır
        button_inner_frame.after(1000, update_coin_prices)

    # Güncellemeyi başlatıyoruz
    update_coin_prices()

# Creates the wallet panel displaying the available USDT balance
def wallet_panel(root):
    wallet_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="#32B14A",
        width=200,
        height=145
    )
    wallet_frame.place(x=730, y=25)

    def update_wallet():
        available_usdt = retrieve_usdt_balance(client)
        for widget in wallet_frame.winfo_children():
            widget.destroy()
        w_label = ctk.CTkLabel(
            wallet_frame,
            text=f"Wallet\n${available_usdt:.2f}",
            text_color="black",
            fg_color="#32B14A",
            font=("Arial", 14, "bold")
        )
        w_label.place(x=75, y=10)
        root.after(1000, update_wallet)

    update_wallet()

# Creates the coin entry panel for entering new coin names
def coin_entry_panel(root):
    entry_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="gray",
        width=250,
        height=60
    )
    entry_frame.place(x=730, y=180)

    label_entry = ctk.CTkLabel(entry_frame, text="Enter coin name", text_color="black", fg_color="gray")
    label_entry.pack(anchor="center", pady=5)

    coin_entry = ctk.CTkEntry(entry_frame, width=200)
    coin_entry.pack(pady=5)

    coin_entry.bind("<Return>", lambda event: process_coin_entry(coin_entry))

    submit_button = ctk.CTkButton(
        entry_frame,
        text="Submit",
        corner_radius=15,
        command=lambda: process_coin_entry(coin_entry)
    )
    submit_button.pack(pady=5)

# Processes the entered coin name and adds it to the dynamic coin panel
def process_coin_entry(coin_entry):
    if coin_entry:
        coin_name = coin_entry.get().strip().lower()
        full_coin_name = f"{coin_name}.usdt"
        print_to_terminal(f"Coin searching '{full_coin_name}' ...")
        set_dynamic_coin_symbol(full_coin_name)
        print_to_terminal(f"Coin added to dynamic coin panel: {full_coin_name}")
        # Creates the terminal panel for displaying messages
        
def terminal_panel(root):
    terminal_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="#1A1A1A",
        width=900,  # Changed width to 1000
        height=50
    )
    terminal_frame.place(x=20, y=320)

    global terminal_output
    terminal_output = ctk.CTkTextbox(
        terminal_frame,
        width=900,  # Changed width to 1000
        height=120,
        fg_color="black",
        text_color="white",
        font=("Arial", 12),
        state="disabled"  # Make the textbox read-only
    )
    terminal_output.pack(padx=10, pady=10)

# Prints a message to the terminal panel with a specified color
def print_to_terminal(message, color="white"):
    global terminal_output
    if terminal_output:
        terminal_output.configure(state="normal")  # Enable writing
        terminal_output.insert(END, f"{message}\n")
        terminal_output.tag_add("color", "end-2l", "end-1l")
        terminal_output.tag_config("color", foreground=color)
        terminal_output.configure(state="disabled")  # Disable writing
        terminal_output.see(END)

# Prints the entered coin name to the terminal
def print_coin_name(coin_entry=None):
    if coin_entry:
        text = coin_entry.get()
        print_to_terminal(f"Coin searching '{text}' ...")

# Retrieves the coin symbol from the favorite coins data based on the column index
def retrieve_coin_symbol(col):
    data = load_fav_coin()
    coins = data['coins']
    
    if col == 6:
        return data['dynamic_coin'][0]['symbol']
    else:
        return coins[col]['symbol']
    

# Handles the hard buy button click event
def hard_buy_button_click(col):
    symbol = retrieve_coin_symbol(col)
    order = hard_buy_order(client, symbol)
    if order is None:
        print_to_terminal(f"Hard buy failed for {symbol}")
        return
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Hard bought {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT", "green")

# Handles the hard sell button click event
def hard_sell_button_click(col):
    symbol = retrieve_coin_symbol(col)
    order = hard_sell_order(client, symbol)
    if order is None:
        print_to_terminal(f"Hard sell failed for {symbol}")
        return
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Hard sold {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT", "red")

# Handles the soft buy button click event
def soft_buy_button_click(col):
    symbol = retrieve_coin_symbol(col)
    order = soft_buy_order(client, symbol)
    if order is None:
        print_to_terminal(f"Soft buy failed for {symbol}")
        return
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Soft bought {symbol} for {cost:.2f} USDT coin amount {amount} price {price} USDT", "green")

# Handles the soft sell button click event
def soft_sell_button_click(col):
    symbol = retrieve_coin_symbol(col)
    order = soft_sell_order(client, symbol)
    if order is None:
        print_to_terminal(f"Soft sell failed for {symbol}")
        return
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Soft sell {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT", "red")

# Handles the coin info button click event
def coin_info_button_click(col):
    print_to_terminal(f"Coin Info button clicked in column {col}")

# Main function to initialize and run the application
def initialize_gui():
    th1 = threading.Thread(target=start_price_websocket)
    th1.start()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root.title("GAIN")
    root.configure(bg="#3C5152")
    
    window_width = 950
    window_height = 500

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))

    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    root.configure(fg_color="#3C5152")

    fav_coin_panel(root)
    wallet_panel(root)
    coin_entry_panel(root)
    dynamic_coin_panel(root)
    terminal_panel(root)

    root.mainloop()
    ws.close()
    os._exit(0)

def main():
    initialize_gui()

if __name__ == "__main__":
    main()
