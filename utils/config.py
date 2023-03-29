import os

def readRoomsFile(filename):
    roomsTxt = """
#######################################################################################
#
# To add a room for recording comments:
#   The room url address is: "https://www.showroom-live.com/ROOM_URL_KEY".
#   Just copy and paste only the last part "ROOM_URL_KEY".
#
# Anything after the symbol "#" on a line is ignored by the program.
#
#######################################################################################


"""
    # create file if not present
    path = os.getcwd()
    filenamepath = os.path.join(path, filename)
    if not os.path.isfile(filenamepath):
        with open(filenamepath, 'w', encoding='utf8') as fp:
            fp.write(roomsTxt)
        print('Created {}'.format(filename))

    with open(filenamepath, 'r', encoding='utf8') as fp:
        lines = fp.readlines()

    room_url_keys = []
    sr_url = 'https://www.showroom-live.com/'
    for line in lines:
        # remove # and line after it
        sharp = line.find('#')
        if sharp > -1:
            line = line[:sharp]
        line = line.strip()
        if len(line) == 0:
            continue

        # remove showroom url
        srIdx = line.find(sr_url)
        if srIdx > -1:
            line = line[len(sr_url):]
        room_url_keys.append(line)
    return room_url_keys



def readSettingsFile(filename):
    settingsTxt = """
[program_settings]
interval = 10                    # seconds, time interval to check rooms are on live or not
show_comments = 0                # 1: enable, 0: disable
show_debug_message = 0           # 1: enable, 0: disable
save_program_debug_log = 0       # 1: enable, 0: disable
save_comments_debug_log = 0      # 1: enable, 0: disable

[danmaku_settings]
width = 640
height = 360
font_name = MS PGothic
font_size = 18
alpha = 10                       # transparency percentage, a number between 0 and 100

"""
    # create file if not present
    path = os.getcwd()
    filenamepath = os.path.join(path, filename)
    if not os.path.isfile(filenamepath):
        with open(filenamepath, 'w', encoding='utf8') as fp:
            fp.write(settingsTxt)
        print('Created {}'.format(filename))

    with open(filenamepath, 'r', encoding='utf8') as fp:
        lines = fp.readlines()

    foundProgSettings = False
    foundDanmakuSettings = False
    program_settings = {}
    danmaku_settings = {}
    for line in lines:
        # remove # and line after it
        sharp = line.find('#')
        if sharp > -1:
            line = line[:sharp]
        line = line.strip()
        if len(line) == 0:
            continue

        if line.lower().find('[program_settings]') > -1:
            foundProgSettings = True
            foundDanmakuSettings = False
            continue
        if line.lower().find('[danmaku_settings]') > -1:
            foundProgSettings = False
            foundDanmakuSettings = True
            continue

        if foundProgSettings:
            s1, s2 = line.split("=", 1)
            program_settings.update(
                {s1.lower().strip(): int(s2.lower().strip())})
            continue

        if foundDanmakuSettings:
            s1, s2 = line.split("=", 1)
            s1 = s1.lower().strip()
            s2 = s2.strip()
            if s1.find('font_name') < 0:
                s2 = int(s2)
            danmaku_settings.update({s1: s2})
            continue

    settings = {'program_settings': program_settings,
                'danmaku_settings': danmaku_settings}
    return settings

