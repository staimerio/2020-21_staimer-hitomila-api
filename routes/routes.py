# Retic
from retic import Router

# Controllers
import controllers.hitomi as hitomi

router = Router()

router.get("/hentai/latest", hitomi.get_latest)
router.get("/hentai/chapters", hitomi.get_chapters_by_slug)
