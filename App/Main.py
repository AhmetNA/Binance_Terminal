import sys
import os

from packages.GUI import initialize_gui

# TODO: Ensure the user's purchase is executed within a specified volatility.
# TODO: Create a exe file to run the code without the need of python.
# TODO: Ensure the purchase's recieved and print the purchase's details correctly.

def main():
    print("Starting the application...")
    initialize_gui()

if __name__ == "__main__":
    main()