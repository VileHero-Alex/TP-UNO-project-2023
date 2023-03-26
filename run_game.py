import threading
import random
import time
from src.server import Server
from src.table import Table
from src.terminal_client import TerminalInterface
from src.bot import Bot
import configparser

# Load the config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Get the values from the sections
HEADER = config.getint('SYSTEM CONFIG', 'HEADER')
FORMAT = config.get('SYSTEM CONFIG', 'FORMAT')
DISCONNECT_MESSAGE = config.get('SYSTEM CONFIG', 'DISCONNECT_MESSAGE')
SERVER = config.get('CONNECTION SETTINGS', 'SERVER')
PORT = config.getint('CONNECTION SETTINGS', 'PORT')
NICKNAME = config.get('GAME LAUNCH PARAMETERS', 'NICKNAME')
HOST_OR_JOIN = config.get('GAME LAUNCH PARAMETERS', 'HOST_OR_JOIN')
INITIAL_NUMBER_OF_CARDS = config.getint('GAME RULES', 'INITIAL_NUMBER_OF_CARDS')
SEVEN_ZERO = config.getboolean('GAME RULES', 'SEVEN_ZERO')
JUMP_IN = config.getboolean('GAME RULES', 'JUMP_IN')
FORCE_PLAY = config.getboolean('GAME RULES', 'FORCE_PLAY')
NO_BLUFFING = config.getboolean('GAME RULES', 'NO_BLUFFING')
DRAW_TO_MATCH = config.getboolean('GAME RULES', 'DRAW_TO_MATCH')


if __name__ == "__main__":
    if HOST_OR_JOIN == "HOST":
        try:
            server = Server(SERVER, PORT)
        except OSError:
            print(f"[CONNECTION ERROR] can't start server on {SERVER}:{PORT}")
            exit()
        player = TerminalInterface(threading.Lock(), server=SERVER, port=PORT, name=NICKNAME)
        print("Waiting for other connections. Type 'start' when all your friends are connected")
        start = input()
        while start != "start":
            start = input()
        if len(server.clients) > 4:
            print("Can't start game with more that 4 people")
            exit()
        random.shuffle(Bot.BOT_NAMES)
        bots = []
        for i in range(4 - len(server.clients)):
            bots.append(Bot(threading.Lock(), server=SERVER, port=PORT, name=f"AI {Bot.BOT_NAMES[i]}"))
        time.sleep(1)
        players = server.clients.copy()
        random.shuffle(players)
        Table(players)
        player.thread_listen.start()