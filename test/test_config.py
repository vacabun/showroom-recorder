from configparser import ConfigParser
import csv

configparser = ConfigParser()
configparser.read('config.ini', encoding='utf-8')
sections = configparser.sections()
print(sections)
for section in sections:
    items = configparser.items(section)
    print(items)

with open('rooms.ini', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        print(row)
