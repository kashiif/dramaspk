
def _make_full_url(url):
    if len(url) == 0:
        return ''
    if url[0] == '/':
        return 'http://dramaspk.com' + url

    return url

def create_channel_entry(title, url, thumbnail):
    return {
        'title': title,
        'url': url,
        'pagetype': 'channel-list',
        'thumbnail': thumbnail
    }


def create_show_entry(title, url, thumbnail):
    print 'create_show_entry', url
    return {
        'title': title,
        'url': url,
        'pagetype': 'channel-show',
        'thumbnail': _make_full_url(thumbnail)
    }


def create_episode_entry(title, url, thumbnail):

    if title.lower().find('promo') >= 0:
        # Skip promos
        return None

    return {
        'title': title.replace('Dailymotion ', '')
                      .replace('Online Download', '')
                      .replace('Latest ', ''),
        'url': url.decode('utf-8'),
        'pagetype': 'show-episode',
        'thumbnail': _make_full_url(thumbnail)
    }
