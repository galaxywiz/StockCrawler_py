#pip install telepot
import telepot

class TelegramBot:
    def __init__(self, token, id):
      self.teleBot_ = telepot.Bot(token)
      self.id_ = id

    def sendMessage(self, message):
      self.teleBot_.sendMessage(self.id_, message)

    def sendPhoto(self, image, message):
      self.teleBot_.sendPhoto(self.id_, photo=open(image, 'rb'), caption=message)