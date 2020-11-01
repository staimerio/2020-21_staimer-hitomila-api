# Retic
from retic import Request, Response, Next, App as app

# Services
from retic.services.responses import success_response
from services.hitomi import hitomi
HITOMI_LIMIT_LATEST = app.config.get('HITOMI_LIMIT_LATEST')
HITOMI_PAGES_LATEST = app.config.get('HITOMI_PAGES_LATEST')
HITOMI_EN_HREFLANG = app.config.get('HITOMI_EN_HREFLANG')


def get_latest(req: Request, res: Response, next: Next):
    """Get all novel from latests page"""
    hentai = hitomi.get_latest(
        lang=req.param('lang', HITOMI_EN_HREFLANG),
        limit=req.param('limit', HITOMI_LIMIT_LATEST, int),
        pages=req.param('pages', HITOMI_PAGES_LATEST, int),
    )
    """Check if exist an error"""
    if hentai['valid'] is False:
        return res.bad_request(hentai)
    """Transform the data response"""
    _data_response = {
        u"hentai": hentai.get('data')
    }
    """Response the data to client"""
    res.ok(success_response(_data_response))


def get_chapters_by_slug(req: Request, res: Response, next: Next):
    """Get all chapters from novel page"""
    _chapters = hitomi.get_chapters_by_slug(
        slug=req.param('slug'),
        galleryid=req.param('id'),
        lang=req.param('lang', HITOMI_EN_HREFLANG),
    )
    """Check if exist an error"""
    if _chapters['valid'] is False:
        return res.bad_request(_chapters)
    else:
        """Response the data to client"""
        res.ok(_chapters)
