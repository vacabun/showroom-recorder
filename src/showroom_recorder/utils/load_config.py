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
    "rooms":[],
    "biliup": {
        "rooms":[],
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
        self.sessdata = ""
        self.bili_jct = ""
        self.DedeUserID__ckMd5 = ""
        self.DedeUserID = ""
        self.access_token = ""


class Config:
    def __init__(self):
        self.interval = 10
        self.debug = False
        self.webdav = WebdavConfig()
        self.rooms = []
        self.biliup = BiliupConfig()

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
            self.webdav.upload = config["webdav"]["upload"]
            self.webdav.url = config["webdav"]["url"]
            self.webdav.username = config["webdav"]["username"]
            self.webdav.password = config["webdav"]["password"]
            self.webdav.delete_source_file = config["webdav"]["delete_source_file"]
            self.rooms = config["rooms"]
            self.biliup.rooms = config["biliup"]["rooms"]
            self.biliup.line = config["biliup"]["line"]
            self.biliup.sessdata = config["biliup"]["sessdata"]
            self.biliup.bili_jct = config["biliup"]["bili_jct"]
            self.biliup.DedeUserID__ckMd5 = config["biliup"]["DedeUserID__ckMd5"]
            self.biliup.DedeUserID = config["biliup"]["DedeUserID"]
            self.biliup.access_token = config["biliup"]["access_token"]
            





