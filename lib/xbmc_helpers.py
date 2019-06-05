# -*- coding: utf-8 -*-

import json
import xbmc
import xbmcaddon

__addon__ = xbmcaddon.Addon()

def jsonRPC(method, params, id = 1):
    response = xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": id}))
    return json.loads(response)

def localize(id, params = ()):
    try:
        return __addon__.getLocalizedString(id).encode('utf-8', 'ignore') % params
    except:
        return __addon__.getLocalizedString(id).encode('utf-8', 'ignore')


def search_movie(title):
    method = "VideoLibrary.GetMovies"
    params = {"filter": {"operator": "is", "field": "title", "value": title}, "properties": ["title"]}
    res = jsonRPC(method, params)

    if "movies" in res["result"]:
        return res["result"]["movies"][0]
    else:
        return None

def search_episode(tvshow, season, episode):
    method = "VideoLibrary.GetEpisodes"
    params = {
        "filter": {"and": [
            {"operator": "is", "field":"tvshow", "value": tvshow},
            {"operator": "is", "field":"season", "value": season},
            {"operator": "is", "field":"episode", "value": episode}]},
        "properties": ["showtitle", "season", "episode"]
    }

    res = jsonRPC(method, params)

    if "episodes" in res["result"]:
        return res["result"]["episodes"][0]
    else:
        return None

def get_movie_details(movieid):
    method = "VideoLibrary.GetMovieDetails"
    params = {"movieid": movieid, "properties": ["title", "file"]}

    res = jsonRPC(method, params)

    if "error" in res:
        return None
    else:
        return res["result"]["moviedetails"]

def get_episode_details(episodeid):
    method = "VideoLibrary.GetEpisodeDetails"
    params = {"episodeid": episodeid, "properties": ["showtitle", "season", "episode", "file"]}

    res = jsonRPC(method, params)

    if "error" in res:
        return None
    else:
        return res["result"]["episodedetails"]

