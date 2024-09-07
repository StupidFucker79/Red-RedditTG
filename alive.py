import time
from flask import Flask
from threading import Thread
from datetime import datetime


app = Flask('')

@app.route('/')
def home():
    return f"I'm Alive... Fuck Off {datetime.now()}"




@app.route('/log')
def long():
    file = "PHVDL.log"
    with open(file) as logfile:
        log = logfile.readlines()  
        return "<br>".join(log)


def run():
  app.run(host='0.0.0.0',port=80)

def keep_alive():  
    t = Thread(target=run)
    t.start()


