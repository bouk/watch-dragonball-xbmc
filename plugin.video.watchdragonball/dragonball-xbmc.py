import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import urllib
import urllib2
import re
import os
from BeautifulSoup import BeautifulSoup

ADDON_NAME = "plugin.video.watchdragonball"
Addon =  xbmcaddon.Addon(id=ADDON_NAME)
PLUGINDIR = os.getcwd()
RESOURCESDIR = os.path.join(PLUGINDIR,"resources")
MEDIADIR = os.path.join(RESOURCESDIR,"media")
CONFIGDIR = os.path.join(PLUGINDIR, "config")

if((Addon.getSetting("savefile") != "") and (os.path.isfile(Addon.getSetting("savefile")))):
    WATCHEDFILE = Addon.getSetting("savefile")
else:
    WATCHEDFILE = os.path.join(CONFIGDIR, "watched")


DRAGONBALL = 0
DRAGONBALLZ = 1
DRAGONBALLGT = 2

PARAMETER_KEY_MENU = "menu"
PARAMETER_KEY_EPISODE_URL = "episodeurl"
PARAMETER_KEY_WATCHED = "watched"



handle = int(sys.argv[1])

def main():
    print sys.argv[2]
    params = parametersStringToDict(sys.argv[2])
    if not sys.argv[2]:
        showShows()
    else :
        print params
        if(params.has_key(PARAMETER_KEY_EPISODE_URL)):
            showEpisode(params.get(PARAMETER_KEY_EPISODE_URL))
        elif(params.has_key(PARAMETER_KEY_WATCHED)):
            addWatched(params.get(PARAMETER_KEY_WATCHED))
        elif(params.has_key(PARAMETER_KEY_MENU)):
            showEpisodeList(int(params.get(PARAMETER_KEY_MENU)))
        

def showShows():
    addDirectoryItem(name="Dragonball" , isFolder=True, thumbnailImage=os.path.join(MEDIADIR, "dragonball-poster.jpg")  , parameters={PARAMETER_KEY_MENU : DRAGONBALL})
    addDirectoryItem(name="Dragonball Z" , isFolder=True, thumbnailImage=os.path.join(MEDIADIR, "dragonballz-poster.jpg") , parameters={PARAMETER_KEY_MENU : DRAGONBALLZ})
    addDirectoryItem(name="Dragonball GT", isFolder=True, thumbnailImage=os.path.join(MEDIADIR, "dragonballgt-poster.jpg"), parameters={PARAMETER_KEY_MENU : DRAGONBALLGT})
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True, cacheToDisc=True)

def showEpisodeList(show):
    watched = loadWatched()
    pageContents = getURLContents("http://watch-dragonball.com/")
    soup =  BeautifulSoup(pageContents)
    episodes = soup.find("div", {"id":"side-a"} ).find("tr").findAll("td")[1:][show].findAll("a")
    for episode in reversed(episodes):
        url = sys.argv[0] + '?' + urllib.urlencode({PARAMETER_KEY_EPISODE_URL : episode['href']})
        watchedUrl = "PlayMedia("+sys.argv[0] + '?' + urllib.urlencode({PARAMETER_KEY_WATCHED : episode['href'], PARAMETER_KEY_MENU:show})+")"
        episodenumber = int(re.search("([0-9]{1,3})", episode['title'], re.I|re.M|re.S).group(1))
        if isWatched(episode['href'], watched):
            thumb = os.path.join(MEDIADIR, "plus.png")
        else:
            thumb = os.path.join(MEDIADIR, "cross.png")
        li = xbmcgui.ListItem(label=episode['title'], thumbnailImage=thumb, path=url)
        li.setInfo('video', {'title':episode['title'], 'episode':episodenumber, 'season':1})
        li.addContextMenuItems(items=[("Mark as watched",watchedUrl)], replaceItems=False)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True, cacheToDisc=False)

def showEpisode(episodeurl):
    addWatched(episodeurl)
    soup = BeautifulSoup(getURLContents(episodeurl))
    sidea = soup.find("div", {"id":"side-a"})
    episodetitle = sidea.findAll('td', {'class':'style100'})[3].contents[0]
    episodenumber = int(re.search("([0-9]{1,3})", sidea.find('h1').contents[0], re.I|re.M|re.S).group(1))
    li = xbmcgui.ListItem(label=episodetitle)
    li.setInfo('video', {'Title':episodetitle, 'Episode':episodenumber, 'Season':1, 'Genre':'Anime'})
    fileurl = re.search('file=(https?:\/\/[^&]+)', sidea.find("embed")['flashvars'], re.S|re.I).group(1)
    xbmc.Player().play(item=fileurl, listitem=li)

def addDirectoryItem(name, isFolder=True, parameters={}, thumbnailImage=""):
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    li = xbmcgui.ListItem(label=name, thumbnailImage=thumbnailImage, path=url)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=url,
                                        listitem=li,
                                        isFolder=isFolder)

def loadWatched():
    setupWatched()
    loadedWatched = []
    f = open(WATCHEDFILE, 'r')
    for line in f:
       loadedWatched.append(line.strip())
    f.close()
    return loadedWatched
        
def addWatched(url):
    if isWatched(url, loadWatched()):
        return
    watched = []
    watched.extend(loadWatched())
    watched.append(url)
    f = open(WATCHEDFILE, 'w')
    for u in watched:
        f.write(u+os.linesep)
    f.close()

def setupWatched():
    if not os.path.isfile(WATCHEDFILE):
        if not os.path.isdir(CONFIGDIR):
            os.mkdir(CONFIGDIR)
    if not os.path.isfile(WATCHEDFILE):
        open(WATCHEDFILE, 'w').close()
    

def isWatched(url, watchedlist):
    for u in watchedlist:
        if u == url:
            return True
    return False    

def parametersStringToDict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[urllib.unquote_plus(paramSplits[0])] = urllib.unquote_plus(paramSplits[1])
    return paramDict

def getURLContents(url):
        try:
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            link = response.read()
            response.close()
        except urllib2.HTTPError, e:
            print "HTTP error: %d" % e.code
        except urllib2.URLError, e:
            print "Network error: %s" % e.reason.args[1]
        else:
            return link

main()