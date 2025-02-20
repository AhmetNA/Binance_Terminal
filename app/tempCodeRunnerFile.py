def get_fav_coins_from_txt():
    with open('Binance_Terminal/app/fav_coins.txt', 'r') as file:
        for line in file:
            # if line starts with #, it is a comment
            if line.startswith("#"):
                continue
            yield line.strip()
            print(line.strip())