# plugin.video.eptv is in alpha so don't bite my head off just yet, and please contribute!
from bs4 import BeautifulSoup
import json
import re
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin

BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ARGS = urlparse.parse_qs(sys.argv[2][1:])

SCHEDULE_URL = 'http://www.europarl.europa.eu/ep-live/'
EPTV_URL = 'https://www.europarltv.europa.eu'

xbmcplugin.setContent(handle=ADDON_HANDLE, content='movies')


def build_url(query):
    return BASE_URL + '?' + urllib.urlencode(query)


def main_menu():
    categories = ['Schedule', 'Live', 'Categories']
    defunct_categories = ['Plenary on demand', 'Committees on demand', 'Other events on demand']

    for category in categories:
        url = build_url({'mode': category, 'foldername': category})
        li = xbmcgui.ListItem(category, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    for category in defunct_categories:
        url = build_url({'mode': category, 'foldername': category})
        li = xbmcgui.ListItem('[COLOR grey]' + category + '[/COLOR]', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def live_menu():
    schedule_page = BeautifulSoup(urllib.urlopen(SCHEDULE_URL), 'html.parser')

    live_broadcasts = [elem.parent for elem in schedule_page.find_all(class_='ep_live')]

    for broadcast in live_broadcasts:
        time = broadcast.find('span', class_='ep_time').text
        title = broadcast.find('span', class_='ep_title').text
        subtitle = broadcast.find('span', class_='ep_subtitle').text

        url = build_url({'mode': 'play_live_video', 'vidurl': broadcast['href']})
        li = xbmcgui.ListItem("[" + title + "] " + subtitle + " (" + time + ")", iconImage='DefaultFolder.png')
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def categories_menu():
    """Build the categories menu."""
    categories = ['EU-affairs', 'Economy', 'Security', 'Society', 'World']

    for category in categories:
        url = build_url({'mode': 'Topic', 'foldername': category, 'page': 1})
        li = xbmcgui.ListItem(category, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def topics_menu(topic, pagenum):
    topic_url = EPTV_URL + '/category/' + topic + '?page=' + pagenum
    topic_page = BeautifulSoup(urllib.urlopen(topic_url), 'html.parser')

    for videoItem in topic_page.find_all('article'):
        url = build_url({'mode': 'Video', 'vidurl': videoItem.a['href']})
        li = xbmcgui.ListItem(videoItem.a['title'], iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=False)

    url = build_url({'mode': 'Topic', 'foldername': topic, 'page': int(pagenum) + 1})
    li = xbmcgui.ListItem('Next page', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def committees_menu():
    recorded_url = SCHEDULE_URL + '/en/committees/search'

    recorded_page = BeautifulSoup(urllib.urlopen(recorded_url), 'html.parser')

    for recorded_committee in recorded_page.find_all('li', class_='ep_media'):
        url = build_url({'mode': 'Committee', 'comitteeUrl': recorded_committee.a['href']})
        li = xbmcgui.ListItem(recorded_committee.find('span', class_='ep_title').string, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def agenda():
    schedule_page = BeautifulSoup(urllib.urlopen(SCHEDULE_URL), 'html.parser')
    scheduled_days = schedule_page.find_all('div', class_='ep_elementtime')

    for day in scheduled_days:
        events = day.ul.find_all('li')
        day_string = '[B][COLOR = blue]{}:[/COLOR][/B]'.format(day.find('div', class_='ep_title').string.strip())

        li = xbmcgui.ListItem(day_string)
        li.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='', listitem=li, isFolder=False)

        for event in events:
            li = xbmcgui.ListItem('   [' + event.find(class_='ep_time').text + '] ' + event.find(class_='ep_subtitle').text)
            li.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='', listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def play_topic_video(vidurl):
    video_link = EPTV_URL + vidurl
    first_vid_page = BeautifulSoup(urllib.urlopen(video_link), 'html.parser')
    thumb_link = first_vid_page.find('meta', {'property': 'og:image'})['content']

    '''Extract iframe number from 'thumb_link'.'''
    iframe_num = thumb_link.split('/')[4]

    '''Link to JSON object containing the "entry_id".'''
    json_link = EPTV_URL + '/europarltv_services/services/getIframe/' + iframe_num
    '''Get the "entry_id".'''
    entry_id = json.load(urllib.urlopen(json_link))['data']['entry']

    video_location_url = 'https://eurounprodkmc-a.akamaihd.net/p/102/sp/10200/raw/entry_id/' + \
                         entry_id + \
                         '?relocate = f.mov'

    play_item = xbmcgui.ListItem(path=video_location_url)
    xbmcplugin.setResolvedUrl(handle=ADDON_HANDLE, succeeded=True, listitem=play_item)


def play_live_video(vidurl):
    url = SCHEDULE_URL.strip('/ep-live/') + vidurl.replace('/en/', '/en/json/', 1)
    url = BeautifulSoup(json.loads(urllib.urlopen(url).readline())['event']['embedCode'], 'html.parser').iframe[
        'src']
    media_json = json.loads(re.search('var mediaSetup = ({.*?});', urllib.urlopen(url).read()).group(1))
    media_server = media_json['server']
    media_application = media_json['application']
    # media_track = media_json['playlist'][0]['source']['languages']
    # media_clientip = media_json['clientIp']
    # TODO: Stream selection by user
    media_stream = media_json['playlist'][0]['source']['qualities'].values()[0]['en']

    url = '/'.join(['https:/', media_server, media_application, media_stream, 'playlist.m3u8'])
    li = xbmcgui.ListItem(path=url)

    xbmcplugin.setResolvedUrl(handle=ADDON_HANDLE, succeeded=True, listitem=li)


def defunct():
    xbmcgui.Dialog().notification('EuroparlTV', 'Under construction.', xbmcgui.NOTIFICATION_ERROR, 5000)


mode = ARGS.get('mode', None)

if mode is None:
    main_menu()

elif mode[0] == 'Categories':
    categories_menu()

elif mode[0] == 'Topic':
    topic = ARGS.get('foldername')[0]
    pagenum = ARGS.get('page')[0]
    topics_menu(topic, pagenum)

elif mode[0] == 'Video':
    play_topic_video(ARGS.get('vidurl')[0])

elif mode[0] == 'Live':
    live_menu()

elif mode[0] == 'Schedule':
    agenda()

elif mode[0] == 'play_live_video':
    play_live_video(ARGS.get('vidurl')[0])

elif mode[0] == 'Plenary on demand':
    defunct()

elif mode[0] == 'Committees on demand':
    defunct()
    committees_menu()

elif mode[0] == 'Other events on demand':
    defunct()
