"""Services for hitomi controller"""
# Retic
from retic import App as app

# Requests
import requests

# bs4
from bs4 import BeautifulSoup

# Asyncio
import asyncio

# Aiohttp
import aiohttp

# Re
import re

# Services
from retic.services.responses import success_response, error_response
from retic.services.general.urls import urlencode, slugify
from retic.services.general.json import parse

# Utils
from services.utils.general import get_node_item, get_node_light_novel_item
from services.utils.dataview import DataView

# Constants
YEAR = app.config.get('HITOMI_YEAR', callback=int)
URL_API_BASE = app.config.get('HITOMI_URL_API_BASE')
HEADERS = {
    'accept': '*/*',
    'accept-encoding': 'identity',
    'accept-language': 'es-ES, es;q=0.9',
    'origin': 'https://hitomi.la',
    'Range': 'bytes=0-99',
    'referer': 'https://hitomi.la/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0 Win64 x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
}


class Hitomi(object):

    def __init__(self, lang='EN'):
        """Set the variables"""
        self.site = app.config.get("HITOMI_"+lang+"_SITE")
        self.host = app.config.get("HITOMI_"+lang+"_HOST")
        self.url_base = app.config.get("HITOMI_"+lang+"_URL")
        self.lang = app.config.get("HITOMI_"+lang+"_LANG")
        self.nozomi = app.config.get("HITOMI_"+lang+"_NOZOMI")
        self.hreflang = app.config.get("HITOMI_"+lang+"_HREFLANG")
        self.langname = app.config.get("HITOMI_"+lang+"_LANGNAME")
        self.gallery = app.config.get("HITOMI_"+lang+"_GALLERY")
        self.chapter_prefix = app.config.get("HITOMI_"+lang+"_CHAPTER_PREFIX")


def get_text_from_req(url, headers={}):
    """GET Request to url"""
    _req = requests.get(url, headers=headers)
    """Check if status code is 200"""
    if _req.status_code != 200:
        raise Exception("The request to {0} failed".format(url))
    return _req.text


def get_data_items_json(instance, page=0, limit=25):
    """Declare all variables"""
    _items = list()
    _nozomi_list = []
    _items_nozomi = []
    """ Set url to consume"""  # ?page={1}
    _url = "{0}".format(
        instance.nozomi,
        # page
    )
    HEADERS['Range'] = 'bytes=0-{0}'.format((limit*4)-1)
    """GET Request to url"""
    _req = requests.get(_url, headers=HEADERS)
    _data_view = DataView(_req.content, bytes_per_element=1)
    _length = int(_req.headers['content-length'])
    _total = int(_length/4)
    for idx in range(0, _total):
        _value = _data_view.get_uint_32(idx*4, byteorder='big')
        _nozomi_list.append(_value)
    """Get info of items"""
    for id in _nozomi_list:
        """Validate if has the max"""
        if len(_items) >= limit:
            break
        _url_item = "{0}/galleryblock/{1}.html".format(URL_API_BASE, id)
        """Get info"""
        _items_nozomi.append({
            u'url': _url_item,
            u'id': id,
        })

    async def get_info_item_req(_item_nozomi):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=_item_nozomi['url']) as response:
                resp = await response.text()
                """Format the response"""
                _soup = BeautifulSoup(resp, 'html.parser')
                _items.append({
                    **_item_nozomi,
                    u'html': _soup
                })

    async def main():
        promises = [get_info_item_req(_item_nozomi)
                    for _item_nozomi in _items_nozomi]
        await asyncio.gather(*promises)

    asyncio.run(main())
    """Return all items"""
    return _items


def get_data_items_pages(instance, pages, limit):
    """Define the list"""
    _items = []
    for _page in range(0, pages):
        _items_json_page = get_data_items_json(instance, _page, limit)
        """Combine the pages"""
        _items += _items_json_page
        """Validate if has the max"""
        if len(_items) >= limit:
            break
    return _items


def get_data_item_json(instance, item):
    try:
        html = item['html']
        """Find the a element"""
        _data_item = html.find('a', href=True)
        """Get url"""
        _url = _data_item['href']
        """Check that the url exists"""
        _title = html.find('h1').text
        return get_node_item(item['id'], _url, _title, YEAR, instance.host, instance.site)
    except Exception as e:
        return None


def get_list_json_items(instance, pages, limit=100):
    """Declare all variables"""
    _items = list()
    """Get article html from his website"""
    _items_json = get_data_items_pages(instance, pages, limit)
    for _item_json in _items_json:
        _item_data = get_data_item_json(instance, _item_json)
        """Check if item exists"""
        if not _item_data:
            continue
        """If lang is different than en(english), add lang to slug"""
        _title = "{0}-{1}".format(_item_data['title'], instance.langname)
        """Slugify the item's title"""
        _item_data['slug'] = slugify(_title)
        """Add item"""
        _items.append(_item_data)
        """Validate if has the max"""
        if len(_items) >= limit:
            break
    """Return items"""
    return _items


def get_instance_from_lang(lang):
    """Get an MTLNovel instance from a language"""
    if lang == "en":
        return Hitomi(lang.upper())
    elif lang == "it":
        return Hitomi(lang.upper())
    elif lang == "de":
        return Hitomi(lang.upper())
    raise ValueError("Language {0} is invalid.".format(lang))


def get_latest(lang="en", pages=1, limit=10):
    """Settings environment"""
    hitomi = get_instance_from_lang(lang)
    """Request to hitomi web site for latest novel"""
    _items_raw = get_list_json_items(
        hitomi, pages, limit)
    """Validate if data exists"""
    if not _items_raw:
        """Return error if data is invalid"""
        return error_response(
            msg="Files not found."
        )
    """Response data"""
    return success_response(
        data=_items_raw
    )


def get_publication_by_slug(instance, slug, galleryid):
    _url_item = "{0}/galleries/{1}.js".format(URL_API_BASE, galleryid)
    _content = get_text_from_req(_url_item)
    _galleryinfo = parse(_content.replace('var galleryinfo = ', ''))

    """Set url to consume"""
    _url = "{0}{1}".format(instance.url_base, slug)
    """Get content from url"""
    _content = get_text_from_req(_url)
    """Format the response"""
    _soup = BeautifulSoup(_content, 'html.parser')
    _cover_html = _soup.find(class_='cover').find('img')

    """Get all metadata"""
    _title = _galleryinfo['title']
    _cover = 'https:'+_cover_html.attrs['srcset'].split(' ')[0]

    _alt_name = _galleryinfo['japanese_title']
    _type = _galleryinfo['type']
    _categories = [tag['tag'].lower() for tag in _galleryinfo['tags']
                   ] if _galleryinfo['tags'] else []

    _serie_data = _soup.find(
        class_='gallery-info').find(class_='comma-list')  # .find('li').text
    if not _serie_data:
        _serie = "original"
    else:
        _serie = _serie_data.find('li').text.replace('\n', '').strip()
    _author = _soup.find('h2').text.replace('\n', '').strip()
    """Chapters"""
    _chapters = []
    _images = []
    for idx, file in enumerate(_galleryinfo['files']):
        # url_img = instance.gallery+'/galleries/' + \
        #     str(galleryid)+'/'+file['name']
        type = 'jpg'
        # size = type+'bigtn'
        size = 'bigtn'
        _img_src = url_from_url_from_hash(
            galleryid, file,  # size, type, 'tn'
        )
        _images.append(
            {
                u"title": file['name'],
                u"url": _img_src,
                u"number": idx+1,
                u"hash":  file['hash'],
            }
        )
    _chapters.append(
        {
            u'number': 1,
            u'title': "{0} 01".format(instance.chapter_prefix),
            u'images': _images,
        }
    )
    return get_node_light_novel_item(
        _url, _title, YEAR, _type, _author,
        _cover, _categories, _serie, _alt_name, instance.lang,
        instance.host, instance.site, instance.hreflang, _chapters
    )


def url_from_url_from_hash(galleryid, image, dir=None, ext=None, base=None):
    url, m = url_from_hash(galleryid, image, dir, ext)
    return url_from_url(url, base, m)


def url_from_hash(galleryid, image, dir, ext):
    ext = ext or dir or image['name'].split('.')[-1]
    dir = dir or 'images'
    code, m = full_path_from_hash(image['hash'])
    return 'https://a.hitomi.la/'+dir+'/'+code+'.'+ext, m


def full_path_from_hash(hash):
    if (len(hash) < 3):
        return hash
    code = "{0}/{1}/{2}".format(hash[-1], hash[-3:-1], hash)
    m = ["/{0}/{1}/".format(hash[-1], hash[-3:-1]), hash[-3:-1]]
    return code, m


def url_from_url(url, base=None, m=None):
    folder = url.split('hitomi.la/')[1]
    subdom = 'https://' + \
        subdomain_from_url(url, base, m)+'.hitomi.la/'
    return subdom+folder


def subdomain_from_url(url, base=None, m=None):
    retval = 'b'
    if base:
        retval = base
    number_of_frontends = 3
    b = 16

    if not m:
        return 'a'

    g = int(m[1], b)

    if g:
        if g < 0x30:
            number_of_frontends = 2
        if g < 0x09:
            g = 1
        retval = subdomain_from_galleryid(g, number_of_frontends) + retval
    return retval


def subdomain_from_galleryid(g, number_of_frontends):
    o = g % number_of_frontends
    return chr(97 + o)


def get_chapters_by_slug(slug, galleryid, lang="en"):
    """Define all variables"""
    _chapters_list = []
    """Settings environment"""
    _hitomi = get_instance_from_lang(lang)
    """Get chapters by id"""
    _hentai_publication = get_publication_by_slug(_hitomi, slug, galleryid)
    """Transform data"""
    _data_response = {
        u"hentai": _hentai_publication,
    }
    """"Response to client"""
    return success_response(
        data=_data_response
    )
