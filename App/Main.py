import sys
import os

# `packages` dizinini Python path'ine ekleyin

# `initialize_gui` fonksiyonunu `packages.gui` modülünden import edin
from packages.GUI import initialize_gui

# TODO: Ensure the user's purchase is executed within a specified volatility.
# TODO: Sometimes purchase cost does't match the actual cost. Fix this.
# TODO: Create a exe file to run the code without the need of python.
# TODO: When new coin name added in gui pressing enter should add the coin to the list.
"""In my case I was trying to import a folder that I created, and ended up here. 
I solved that problem by removing __init__.py from the main folder, skeeping the __init__.py in the subfolders that I was importing."""
def main():
    print("Starting the application...")
    initialize_gui()

if __name__ == "__main__":
    main()