import re
import traceback
import urllib
import json

import kodiaddonutils
import dramaspkmodels


def _fetch_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; U; en; CPU iPhone OS 4_2_1 like Mac OS X; en) AppleWebKit/533.17.9 '
                      '(KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5'
    }
    return kodiaddonutils.fetch_url(url, headers)


def fetch_channels_list():
    #TODO: load channel list by parsing page
    create_entry = dramaspkmodels.create_channel_entry
    category_url = 'http://dramaspk.com/category/%s-Dramas/'

    channel_list = [
        {
        'title': 'Recent Episodes',
        'url': 'http://dramaspk.com/dramas/',
        'pagetype': 'recent-episodes',
        'thumbnail': 'http://i.imgur.com/qSzxay9.png'
        },

        create_entry('Hum TV',                    category_url % 'Hum-Tv', 'http://i.imgur.com/SPbcdsI.png'),
        create_entry('Hum Sitaray',               category_url % 'Hum-Sitaray', 'http://i.imgur.com/GtoMqkd.png'),
        create_entry('Express Entertainment',     category_url % 'Express-Entertainment', 'http://i.imgur.com/RBlvLwp.png'),
        create_entry('APlus',                     category_url % 'Aplus', 'http://i.imgur.com/wynK0iI.png'),
        create_entry('Urdu1',                     category_url % 'Urdu1', 'http://i.imgur.com/9i396WG.jpg'),
        create_entry('Ptv',                       category_url % 'Ptv-Home', 'http://i.imgur.com/vJPo6xO.png'),
        create_entry('Geo TV',                    category_url % 'Geo-Tv', 'http://i.imgur.com/YELzFHv.png'),
        create_entry('ARY',                       category_url % 'Ary-digital', 'http://i.imgur.com/Qpvx9N4.png'),
        create_entry('ARY Zindagi',               category_url % 'Ary-Zindagi', 'http://i.imgur.com/a1PH1wk.png'),
        create_entry('Geo Kahani',                category_url % 'Geo-Kahani', 'http://i.imgur.com/7BN4odI.png'),
        create_entry('See TV',                    category_url % 'See-TV', 'http://i.imgur.com/BkJ1440.png'),
        create_entry('TV One',                    category_url % 'Tv-one', 'http://i.imgur.com/Ez7d4mi.png')
    ]

    return channel_list


def _fetch_list(reToMatch, indices, create_entry, params, paging_params = {}):
    url = unicode(urllib.unquote(params.get('url'))).decode('utf8')
    print '_fetch_list url is: %s' % url

    html = _fetch_url(url)

    matches = re.findall(reToMatch, html, re.M)

    all_items = list()

    index_title = indices['title']
    index_url = indices['url']
    index_thumbnail = indices['thumbnail']

    import HTMLParser
    html_parser = HTMLParser.HTMLParser()

    thumbnail_lambda = None
    if index_thumbnail < 0:
        thumbnail_lambda = lambda m: ''
    else:
        thumbnail_lambda = lambda m: m[index_thumbnail]

    for match in matches:

        #title = urllib.unquote(match[index_title]).encode('utf8')
        title = html_parser.unescape(match[index_title].decode('utf-8'))

        url = match[index_url]
        thumbnail = thumbnail_lambda(match)

        entry = create_entry(title, url, thumbnail)

        if entry:
            all_items.append(entry)

    if paging_params:
        next_page_link = _fetch_next_page_link(html)
        print 'next_page_link: %s' % next_page_link

        title = kodiaddonutils.lang(paging_params.get('title_id'))
        # a function pointer to create entry for next page item
        create_entry = paging_params.get('create_entry')

        if next_page_link:
            all_items.append(create_entry(title, next_page_link, ''))

    return {
            'html': html,
            'items': all_items
        }


def _fetch_next_page_link(html):
    reToMatch = '<li><a href="(.*)">Next Page<\/a><\/li>'

    the_iter = re.finditer(reToMatch, html, re.M)
    url = None

    for match in the_iter:
        url = match.group(1)
        break

    return url


def fetch_channel_shows(params):

    # TODO: support paging
    # show-name:3, thumbnail: 2, url: 1
    reToMatch = '<a href=\"([^\"]*)\" [^>]*><img.* src=\"([^\"]*)\"\ .* />([^<]*)<\/a>\s+'

    indices = {'title': 2, 'url': 0, 'thumbnail': 1}

    paging_params = {
            'title_id': 32019,
            'create_entry': dramaspkmodels.create_channel_entry
        }

    result = _fetch_list(reToMatch, indices, dramaspkmodels.create_show_entry, params, paging_params)
    shows = result.get('items')

    return shows


def fetch_episodes(params):

    # show-name:3, thumbnail: 2, url: 1
    reToMatch = '<div class="post_body">\s+<div class="image_area">\s+<a href="([^\"]+)">' \
                '<img src="([^\"]+)" alt="([^\"]+)" [^\/]*/></a>'

    indices = {'title': 2, 'url': 0, 'thumbnail': 1}

    paging_params = {
            'title_id': 32018,
            'create_entry': dramaspkmodels.create_show_entry
        }

    result =_fetch_list(reToMatch, indices, dramaspkmodels.create_episode_entry, params, paging_params)
    episodes = result.get('items')

    return episodes


def _get_yt_resolved_url_from_id(video_id, short):
    playURL = 'https://www.youtube.com/watch?v=%s' % video_id

    print 'Youtube playURL - %s' % playURL

    if short:
        return playURL

    return get_resolved_url(playURL)


def _get_yt_resolved_url_from_embed_link(html, short):
    match = re.findall('src="https:\/\/www\.youtube\.com\/embed\/(.[^\"]*)"', html)

    if len(match):
        return _get_yt_resolved_url_from_id(match[0], short)

    return None


def _get_youtube_urls(html, short):
    try:
        # First look for direct youtube embed video
        playURL = _get_yt_resolved_url_from_embed_link(html, short)

        if playURL:
            return [playURL]

        # If direct youtube link is not found, look for ultatv encoded link
        match =re.findall('src=\"http:\/\/video\.ultatv\.com\/embed\?v=([^\"]*)\"',html)

        if len(match):
            return [_get_yt_resolved_url_from_id(match[0], short)]

    except:
        print 'Error fetching Youtube stream url'
        print traceback.format_exc()

    return None


def _get_ultatv_urls(html, short):
    try:
        match =re.findall('src=\"(http:\/\/www\.ultatv\.com\/embed\/*\?id=([^\"]*))\"',html)

        if len(match):
            ultaTvHtml = _fetch_url(match[0][0])

            match = re.findall('<source .* src="([^"]+)" type="video\/mp4" \/>',ultaTvHtml)

            print 'ultaTVUrl - %s' % match[0]

            return [ match[0] ]
    except:
        print 'Error fetching ultatv url'
        print traceback.format_exc()

    return None

def _get_tunepk_urls(html, short):

    try:
        match =re.findall('src="https+\:\/\/tune\.pk\/(.[^\"]|\s)*vid=(\d*).[^\"]*',html)

        if len(match):
            url = 'https://embed.tune.pk/play/%s?autoplay=yes&ssl=yes&inline=true' % match[0][1]
            print 'tunepk url', url

            tunepk_html = _fetch_url(url)

            match = re.findall('_details.player.sources = (\[.*\]);', tunepk_html)
            sources = json.loads(match[0])

            # TODO : find the highest quality url and not the first one
            print 'tunepk al sources - %s' % sources

            return [ sources[ len(sources) - 1 ].get('file') ]
    except:
        print 'Error fetching tunepk url'
        print traceback.format_exc()

    return None


def _get_dramasface_urls(html, short):

    try:
        match =re.findall('src="(http\:\/\/dramasface\.com\/embed\/\?id=\d+)"',html)

        if len(match):

            print 'dramasface url: %s' % match[0]

            dramasface_html = _fetch_url(match[0])

            playURL = _get_yt_resolved_url_from_embed_link(dramasface_html, short)
            if playURL:
                return [playURL]

            playURL = _get_tunepk_urls(dramasface_html, short)
            if playURL:
                return playURL


    except:
        print 'Error fetching dramasface url'
        print traceback.format_exc()

    return None

def _get_daily_motion_urls(html, short):
    try:
        match =re.findall('src="(.*?(dailymotion\.com\/).*?)"',html)

        if len(match):
            playURL=match[0][0]

            if playURL.startswith('//'):
                playURL = '%s%s' % ('http:', playURL)

            playURL = playURL.replace('embed/', '')

            print 'DailyMotion playURL - %s' % playURL
            if short:
                return [playURL]

            print 'DailyMotion get_resolved_url(playURL) - %s' % get_resolved_url(playURL)

            return [ get_resolved_url(playURL) ]
    except:
        print 'Error fetching DailyMotion stream url'
        print traceback.format_exc()

    return None


def get_resolved_url(play_url):
    import urlresolver

    # if play_url.startswith('//'):
    #     play_url = 'http:%s' % play_url

    stream_url = urlresolver.HostedMediaFile(play_url).resolve()
    return stream_url


def fetch_episode_sources(params):
    available_sources = {}

    url = urllib.unquote(params.get('url').encode('utf8'))
    print 'url is: %s' % url

    html = _fetch_url(url)

    fetchers = {
        'youtube': _get_youtube_urls,
        'dailymotion': _get_daily_motion_urls,
        'tunepk': _get_tunepk_urls,
        'ultatv': _get_ultatv_urls,
        'dramasface': _get_dramasface_urls
    }

    for key in fetchers:
        print 'Trying source: %s' % key

        urls = fetchers[key](html, False)
        if urls:
            available_sources[key] = {'urls': urls}
            break

    print 'video urls: %s' % urls

    return available_sources

