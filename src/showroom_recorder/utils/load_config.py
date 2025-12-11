import os
import logging
import json

configTempTxt = """
{
    "interval": 10,
    "debug": false,
    "webdav": {
        "upload": false,
        "url": "",
        "username": "",
        "password": "",
        "delete_source_file": false
    },
    "best_quality": true,
    "rooms":[""],
    "biliup": {
        "rooms":[""],
        "line": "AUTO",
        "sessdata": "",
        "bili_jct": "",
        "DedeUserID__ckMd5": "",
        "DedeUserID": "",
        "access_token": ""
    }
}

"""


class WebdavConfig:
    def __init__(self):
        self.upload = False
        self.url = "",
        self.username = ""
        self.password = ""
        self.delete_source_file = False


class BiliupConfig:
    def __init__(self):
        self.rooms = []
        self.line = "AUTO"


class Config:
    def __init__(self):
        self.interval = 10
        self.debug = False
        self.webdav = WebdavConfig()
        self.rooms = []
        self.biliup = BiliupConfig()
        self.best_quality = True

    def LoadConfig(self, fileName):
        # create file if not present
        filePath = os.path.join(os.getcwd(), fileName)
        if not os.path.isfile(filePath):
            with open(filePath, 'w', encoding='utf8') as fp:
                fp.write(configTempTxt)
            logging.info(f'File {filePath} is not exist, create it.')

        with open(filePath, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.interval = config["interval"]
            self.debug = config["debug"]
            self.rooms = config["rooms"]
            self.best_quality = config["best_quality"]
            self.webdav.upload = config["webdav"]["upload"]
            self.webdav.url = config["webdav"]["url"]
            self.webdav.username = config["webdav"]["username"]
            self.webdav.password = config["webdav"]["password"]
            self.webdav.delete_source_file = config["webdav"]["delete_source_file"]
            self.biliup.rooms = config["biliup"]["rooms"]
            self.biliup.line = config["biliup"]["line"]
            
            





