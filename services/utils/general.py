"""Services for general utils"""

# Services
from retic.services.general.urls import slugify


def get_node_item(id, url, title, year, host, site=''):
    """Set item structure"""
    _item = {
        u'id': id,
        u'url': url,
        u'title': title,
        u'year': int(year),
        u'service': host,
        u'site': site
    }
    return _item


def get_node_light_novel_item(
    url, title, year, type, author, cover,
    categories, serie, alt_name, lang, host, site='', hreflang='',
    chapters=[],
):
    """"If lang is different than en(english), add lang to slug"""
    _title = "{0}-{1}".format(title, hreflang)
    _item = {
        u'url': url.replace(",", " "),
        u'slug': slugify(_title),
        u'title': title,
        u'year': int(year) if (year != 'N/A') else 2020,
        u'type': type,
        u'author': author,
        u'cover': cover,
        u'categories': categories,
        u'serie': serie,
        u'alt_name': alt_name if alt_name else "",
        u'lang': lang,
        u'service': host,
        u'site': site,
        u'chapters': chapters,
    }
    return _item
