from item import Item
from logging import ERROR
from category import Category
import telebot
from telebot import types
import feedparser
import parameters
from dbhelper import DBHelper

class User():
    bot = None
    db = None
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db