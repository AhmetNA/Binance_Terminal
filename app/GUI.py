import customtkinter as ctk
from tkinter import END
import json
import sys
import os
from Get_Price import *
from Binance_Client import *

client = prepare_client()
root = ctk.CTk()

# Loads favorite coin data from a JSON file
def load_fav_coin():
    json_path = 'Binance_Terminal/app/fav_coins.json'
    with open(json_path, 'r') as file:
        return json.load(file)

# İndeksleri tutarlı hale getirmek için:
# Fav coin panelinde 0-index kullanıyoruz; dinamik coin için ise -1 kullanılacak.
def get_coin_info_column(col):
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
        width=200,
        height=800
    )
    side_frame.place(x=1070, y=30)
    side_inner = ctk.CTkFrame(side_frame, corner_radius=15, fg_color="#4A9195")
    side_inner.pack(expand=True, anchor="center")

    def update_dynamic_coin():
        for widget in side_inner.winfo_children():
            widget.destroy()
        data = load_fav_coin()
        dynamic_coin = data['dynamic_coin'][0]
        dynamic_coin_text = f"{dynamic_coin['symbol']}\n{dynamic_coin['values']['current']}"
        
        dynamic_coin_label = ctk.CTkLabel(
            side_inner,
            text=dynamic_coin_text,
            text_color="black",
            fg_color="#4A9195",
            corner_radius=8,
            width=180,
            height=40
        )
        dynamic_coin_label.pack(pady=10)

        button_configs = [
            ("Hard Buy", hard_buy_button_click, "darkgreen"),
            ("Soft Buy", soft_buy_button_click, "green"),
            (dynamic_coin['values']['current'], coin_info_button_click, "white"),
            ("Soft Sell", soft_sell_button_click, "red"),
            ("Hard Sell", hard_sell_button_click, "darkred"),
        ]

        for text, command, color in button_configs:
            width_val, height_val = 80, 40
            if text == "Coin Info":
                width_val, height_val = 100, 60

            rect_button = ctk.CTkButton(
                side_inner,
                fg_color=color,
                text_color="black",
                corner_radius=15,
                width=width_val,
                height=height_val,
                text=text,
                # Dinamik coin için -1 indeks kullanılıyor
                command=lambda cmd=command, c=6: cmd(c)
            )
            rect_button.pack(pady=10)
        
        root.after(1000, update_dynamic_coin)

    update_dynamic_coin()
    
# Favori coinlerin bulunduğu ana paneli oluşturur.
def fav_coin_panel(root):
    top_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="transparent",
        width=800,
        height=400
    )
    top_frame.place(x=80, y=30)

    button_inner_frame = ctk.CTkFrame(top_frame, corner_radius=15, fg_color="#4A9195")
    button_inner_frame.pack(expand=True, anchor='center')

    def update_buttons():
        for widget in button_inner_frame.winfo_children():
            widget.destroy()
        
        data = load_fav_coin()
        coins = data['coins']
        
        button_configs = [
            [("Hard Buy", hard_buy_button_click, "darkgreen")] * 5,
            [("Soft Buy", soft_buy_button_click, "green")] * 5,
            [("Coin Info", coin_info_button_click, "white")] * 5,
            [("Soft Sell", soft_sell_button_click, "red")] * 5,
            [("Hard Sell", hard_sell_button_click, "darkred")] * 5
        ]

        for row in range(5):
            for col in range(5):
                text, command, color = button_configs[row][col]
                if row == 2 and color == "white":
                    btn_width, btn_height = 150, 60
                    if col < len(coins):
                        coin = coins[col]
                        text = f"{coin['symbol']}\n{coin['values']['current']}"
                else:
                    btn_width, btn_height = 100, 40

                btn = ctk.CTkButton(
                    button_inner_frame,
                    fg_color=color,
                    text_color="black",
                    corner_radius=12,
                    width=btn_width,
                    height=btn_height,
                    text=text,
                    # 0-index kullanılıyor; dinamik coin bu panelde yer almaz.
                    command=lambda cmd=command, c=col: cmd(c)
                )
                btn.grid(row=row, column=col, padx=20, pady=15)
        
        root.after(1000, update_buttons)

    update_buttons()


# Creates the wallet panel displaying the available USDT balance
def wallet_panel(root):
    available_usdt = retrieve_usdt_balance(client)
    wallet_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="#32B14A",
        width=280,
        height=170
    )
    wallet_frame.place(x=30, y=470)

    w_label = ctk.CTkLabel(
        wallet_frame,
        text=f"Wallet\n${available_usdt:.2f}",
        text_color="black",
        fg_color="#32B14A",
        font=("Arial", 14, "bold")
    )
    w_label.place(x=120, y=13)

# Updates the wallet panel with the latest USDT balance
def update_wallet(root):
    available_usdt = retrieve_usdt_balance(client)
    wallet_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="#32B14A",
        width=280,
        height=170
    )
    wallet_frame.place(x=30, y=470)

    w_label = ctk.CTkLabel(
        wallet_frame,
        text=f"Wallet\n${available_usdt:.2f}",
        text_color="black",
        fg_color="#32B14A",
        font=("Arial", 14, "bold")
    )
    w_label.place(x=120, y=13)
    
    root.after(1000, lambda: update_wallet(root))

# Creates the coin entry panel for entering new coin names
def coin_entry_panel(root):
    entry_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="gray",
        width=500,
        height=120
    )
    entry_frame.place(x=370, y=470)

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
        add_dynamic_coin(full_coin_name)
        print_to_terminal(f"Coin added to dynamic coin panel: {full_coin_name}")

# Creates the terminal panel for displaying messages
def terminal_panel(root):
    terminal_frame = ctk.CTkFrame(
        root,
        corner_radius=15,
        fg_color="#1A1A1A",
        width=500,
        height=200
    )
    terminal_frame.place(x=620, y=450)

    global terminal_output
    terminal_output = ctk.CTkTextbox(
        terminal_frame,
        width=580,
        height=180,
        fg_color="black",
        text_color="white",
        font=("Arial", 12)
    )
    terminal_output.pack(padx=10, pady=10)

# Prints a message to the terminal panel
def print_to_terminal(message):
    global terminal_output
    if terminal_output:
        terminal_output.insert(END, f"{message}\n")
        terminal_output.see(END)

# Prints the entered coin name to the terminal
def print_coin_name(coin_entry=None):
    if coin_entry:
        text = coin_entry.get()
        print_to_terminal(f"Coin searching '{text}' ...")

# Retrieves the coin symbol from the favorite coins data based on the column index
def get_coin_info_column(col):
    data = load_fav_coin()
    coins = data['coins']
    
    if col == 6:
        return data['dynamic_coin'][0]['symbol']
    else:
        print(coins[col]['symbol'])
        return coins[col]['symbol']
    

# Handles the hard buy button click event
def hard_buy_button_click(col):
    symbol = get_coin_info_column(col)
    order = hard_buy_order(client, symbol)
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Hard bought {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT")
    update_wallet(root)

# Handles the hard sell button click event
def hard_sell_button_click(col):
    symbol = get_coin_info_column(col)
    order = hard_sell_order(client, symbol)
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Hard sold {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT")
    update_wallet(root)

# Handles the soft buy button click event
def soft_buy_button_click(col):
    symbol = get_coin_info_column(col)
    order = soft_buy_order(client, symbol)
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Soft bought {symbol} for {cost:.2f} USDT coin amount {amount} price {price} USDT")
    update_wallet(root)

# Handles the soft sell button click event
def soft_sell_button_click(col):
    symbol = get_coin_info_column(col)
    order = soft_sell_order(client, symbol)
    amount = float(order['fills'][0]['qty'])
    price = float(order['fills'][0]['price'])
    cost = amount * price
    print_to_terminal(f"Soft sell {symbol} for {cost:.2f} USDT amount {amount} price {price} USDT")
    update_wallet(root)

# Handles the coin info button click event
def coin_info_button_click(col):
    print_to_terminal(f"Coin Info button clicked in column {col}")

# Main function to initialize and run the application
def main():
    th1 = threading.Thread(target=upgrade_price)
    th1.start()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root.title("GAIN")
    root.configure(bg="#3C5152")
    
    window_width = 1250
    window_height = 750

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

if __name__ == "__main__":
    main()
