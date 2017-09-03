import sys
import xbmcgui
import xbmcplugin
import urllib
import urlparse
from BeautifulSoup import BeautifulSoup
import json


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
eptvMainUrl = 'https://www.europarltv.europa.eu'

xbmcplugin.setContent(addon_handle, 'movies')


def build_url(query):
    """Build the Kodi internal url."""
    return base_url + '?' + urllib.urlencode(query)


def main_menu():
    """Build the main menu."""

    categories = ['Live', 'Plenary on demand', 'Committees on demand', 'Other events on demand', 'Categories']

    for category in categories[0:4]:
        url = build_url({'mode': category, 'foldername': category})
        li = xbmcgui.ListItem('[COLOR grey]' + category + '[/COLOR]', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'Categories', 'foldername': 'Categories'})
    li = xbmcgui.ListItem('Categories', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def categories_menu():
    """Build the categories menu."""
    categories = ['EU-affairs', 'Economy', 'Security', 'Society', 'World']

    for category in categories:
        url = build_url({'mode': 'Topic', 'foldername': category, 'page': 1})
        li = xbmcgui.ListItem(category, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def topics_menu(topic, pagenum):
    topicUrl = eptvMainUrl + '/category/' + topic + '?page=' + pagenum
    topicPage = BeautifulSoup(urllib.urlopen(topicUrl))

    for videoItem in topicPage.findAll('article'):
        url = build_url({'mode': 'Video', 'vidurl': videoItem.a['href']})
        li = xbmcgui.ListItem(videoItem.a['title'], iconImage='DefaultFolder.png')
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    url = build_url({'mode': 'Topic', 'foldername': topic, 'page': int(pagenum) + 1})
    li = xbmcgui.ListItem('Next page', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def committees_menu():
    # upcomingUrl = 'http://www.europarl.europa.eu/ep-live/en/committees/schedule'
    recordedUrl = 'http://www.europarl.europa.eu/ep-live/en/committees/search'

    recordedPage = BeautifulSoup(urllib.urlopen(recordedUrl))

    for recordedCommittee in recordedPage.findAll('li', {'class': 'ep_media'}):
        url = build_url({'mode': 'Committee', 'comitteeUrl': recordedCommittee.a['href']})
        li = xbmcgui.ListItem(recordedCommittee.find('span', {'class': 'ep_title'}).string, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(addon_handle)


def play_topic_video(vidurl):
    videoLink = eptvMainUrl + vidurl
    firstVidPage = BeautifulSoup(urllib.urlopen(videoLink))
    thumbLink = firstVidPage.find('meta', {'property': 'og:image'})['content']

    '''Extract iframe number from 'thumbLink'.'''
    iframeNum = thumbLink.split('/')[4]

    '''Link to JSON object containing the "entry_id".'''
    jsonLink = eptvMainUrl + '/europarltv_services/services/getIframe/' + iframeNum
    '''Get the "entry_id".'''
    entryID = json.load(urllib.urlopen(jsonLink))['data']['entry']

    videoLocationUrl = 'https://eurounprodkmc-a.akamaihd.net/p/102/sp/10200/raw/entry_id/' + entryID + '?relocate=f.mov'

    playItem = xbmcgui.ListItem(path=videoLocationUrl)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=playItem)


def defunct():
    xbmcgui.Dialog().notification('EuroparlTV', 'Under construction.', xbmcgui.NOTIFICATION_ERROR, 5000)


mode = args.get('mode', None)

if mode is None:
    main_menu()

elif mode[0] == 'Categories':
    categories_menu()

elif mode[0] == 'Topic':
    topic = args.get('foldername')[0]
    pagenum = args.get('page')[0]
    topics_menu(topic, pagenum)

elif mode[0] == 'Video':
    play_topic_video(args.get('vidurl')[0])

elif mode[0] == 'Live':
    defunct()

elif mode[0] == 'Plenary on demand':
    defunct()

elif mode[0] == 'Committees on demand':
    defunct()
    committees_menu()

elif mode[0] == 'Other events on demand':
    defunct()
