"""Art checks: --media-release validates GIF-only publication; --release also requires text links."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_ROOT = ROOT.parent.parent / "rikiyanai.github.io"
GIF_HASHES = {
    "ae86-360.gif": "5af8457ac121bfd2ce975b30fd094a63b9aa1034337ce83c2b96a6bcc609d4d3",
    "bluebird510-360.gif": "5f8ace837a034c2432e023b4e8c68caa71c732eadaef3654a7a2a25f62147761",
    "cresta-gx71-360.gif": "3daa147986efdefb76d3100d6468bb603a7bef4fa9543bcfcb8758e0ba72b3ce",
    "sambar-360.gif": "b61234c888949c30a5f41c6b9f537d7476e2935f485d81909accbf5490916fa1",
    "porsche911-360.gif": "c6a9a224f1bec56edddf66d878893d85948bdac447a80acf882ddae84dca3549",
    "streamlined-car-360.gif": "38097276e5ce25e9c2baf24876b17ee470b7eceeb69fccfd748f57ff2db97c63",
    "david-360.gif": "1ce77d7d17777bd66ec06393ca70d9c24fd24b0eb2ca4d75f38b5d6281aa7988",
    "laocoon-360.gif": "020aa6d27005f1e7a3f33b74d0edb60cbfc338d4379285d457cf1e1d47da73db",
    "nike-360.gif": "0aea20e46b5d91fe4a4c6114f456cea1e00107bf58f6c40327113d5cbdf40066",
    "thinker-360.gif": "e5bc58adb8f4313ea68a712166d082ea34a04929b97a5b923995eaf7e0944bd2",
    "onion-360.gif": "fbc0e968d9e5feab9d661ce91bd97494171ad8fd0c69d93a09fd7a7893c2bbf8",
    "cloud-v2.gif": "2f07ff2bc38efa66e47573af434922c98de3bd1d0a973620afdaa05a7e047b20",
    "tree-v3.gif": "212f81b603bf70965d9c123b58b3ca67fac36dfa26fc6d4bdd775c4478e529c3",
    "rock-island-v3.gif": "2ff75e25a3e0745bab99acf122dcdf14a18299690992bc09854abd3e80c2bac6",
    "hand-v3.gif": "7fef116fd07d68f3031918745510f03447dba690115cf883787e9a4e13e816a0",
    "yuzu-360.gif": "1a74ef5f3f198f116af9192944d3acdd7f6d60700f70e54f260739fe719e88f9",
    "ginger-360.gif": "850d023042b8fecc72b7ef884f642617dcad153c9f0321ab655466a1cfaacd39",
    "cranberry-360.gif": "3455070c7fa2923730b21f91fdf576a665fd6ddd99e344447ad4a70998d1ccf7",
    "church-walkthrough.gif": "2c37f5131991b5e0935eb0589220cac71d2d30c3b574e9a0f11d7a2ec8e5b733",
    "onion-study-one.gif": "1992c5abceff56583173d9f934f1ec4ab73fa84fef21a803b78db7996e00f7f9",
    "onion-study-two.gif": "8cc8e33b3e7415aa0f720cb5079e13f5abc96341640632c1b962107248bd088f",
    "onion-study-three.gif": "623a06cd1fde3eb0df3ae304cff76da4a6cd92ce7b6b52f01f2365a05d75d0ce",
    "david-study-360.gif": "9b6603b282790c6c5b184a346f04aa3bcbc21b7c33c4f3025413d9abc789f97f",
    "laocoon-study-360.gif": "d0ef7ec974a7ab420bc8f0cdca32716acf0f021a0c761a218c019babc3b7141d",
    "winged-victory-study-360.gif": "c1b67810fd9c899a0488e2ac49dbce59ef849f53042ef767c75988c632320e92",
    "thinker-study-360.gif": "dbbe396ab1a2f9a2a0e94bebdb25e9110903f81f7b26f6e5bf199b9cf99b7cd0",
    "eve-360.gif": "05f094845c537f83f2f45a460879bab4a3dd29a0dcb41726f8fe96128d367d07",
    "veiled-woman-360.gif": "bd1bec798134a8c799f55e34c0ba004cb76b00ac6dd9c4c45744c8c481749c89",
    "woman-bust-360.gif": "09989aa3929847ff2ce285ee2791b1699707c45ebad6a0ee98e08ff3578c5676",
    "classical-woman-bust-360.gif": "9e4794c91b49dbc854fab454b0347efc8f2a504bcbd56406a088e3555d9b8dec",
}

PAINTING_KEYS = {
    "B0JleytJj_8-1", "B0JleytJj_8-2", "BoTND8oAWvO-1", "BoTND8oAWvO-2", "BoTND8oAWvO-3",
    "BmizH-sgz4r-1", "BmizH-sgz4r-2", "BmizH-sgz4r-3", "BmizH-sgz4r-4",
    "BmdMzLvA116-5", "BmQGDpVg-3O-1", "BlnKfnYAm9I-1", "BlZgbzQgU8t-1",
    "Bk1KXsOgNuO-1", "BkdWjDwgxMN-1", "BkdWjDwgxMN-2", "BkJSR-Eg1R0-1",
}

UNCERTAIN_PAINTING_KEYS = {
    "BybZJBupwBz-5",
    "BoTND8oAWvO-4", "BmzyZNagRpS-2", "BmdMzLvA116-4",
}


class ArtPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.heading = None
        self.figures = []
        self.figure = None
        self.in_caption = False
        self.images = []
        self.instagram_keys = []
        self.instagram_posts = []
        self.instagram_summaries = []
        self.in_summary = False
        self.category_stack = []
        self.ascii_category = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "figure" and "data-instagram-key" in attrs:
            self.instagram_keys.append(attrs["data-instagram-key"])
        if tag == "a" and attrs.get("href", "").startswith("https://www.instagram.com/") and "/p/" in attrs["href"]:
            self.instagram_posts.append(attrs["href"])
        if tag == "h2":
            self.heading = ""
        if tag == "summary":
            self.in_summary = True
            self.summary = ""
        if tag == "section":
            self.category_stack.append(self.ascii_category)
            if attrs.get("data-ascii-category"):
                self.ascii_category = attrs["data-ascii-category"]
        if tag == "figure" and "data-art-key" in attrs:
            self.figure = {"key": attrs["data-art-key"], "category": self.ascii_category,
                           "images": [], "caption": "", "links": []}
        if tag == "img" and attrs.get("src"):
            self.images.append(attrs)
            if self.figure is not None:
                self.figure["images"].append(attrs)
        if tag == "figcaption":
            self.in_caption = True
        if tag == "a" and self.in_caption and self.figure is not None:
            self.figure["links"].append(attrs.get("href", ""))

    def handle_data(self, data):
        if self.heading is not None:
            self.heading += data
        if self.in_summary:
            self.summary += data
        if self.in_caption and self.figure is not None:
            self.figure["caption"] += data

    def handle_endtag(self, tag):
        if tag == "h2":
            self.headings.append(self.heading.strip())
            self.heading = None
        if tag == "summary":
            self.instagram_summaries.append(self.summary.strip())
            self.in_summary = False
        if tag == "figcaption":
            self.in_caption = False
        if tag == "figure" and self.figure is not None:
            self.figures.append(self.figure)
            self.figure = None
        if tag == "section" and self.category_stack:
            self.ascii_category = self.category_stack.pop()


def load_page(root=ROOT):
    page = ArtPage()
    page.feed((root / "art.html").read_text())
    return page


def public_text_link(url):
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname == "aahub.org"
            and not parsed.username and not parsed.password and not parsed.query
            and bool(re.fullmatch(r"/mlts?/[^/]+/?", parsed.path)))


STATUE_PAIR_KEYS = {
    "david-study", "laocoon-study", "winged-victory-study", "thinker-study", "eve-study",
}

ASCII_CATEGORY_KEYS = {
    "Vehicles": {"ae86", "bluebird510", "cresta-gx71", "sambar", "porsche911", "streamlined-car"},
    "Statues and Studies": {"david-study", "laocoon-study", "winged-victory-study", "thinker-study", "eve-study", "hand"},
    "Fruits and Vegetables": {"onion", "onion-study-one", "onion-study-two", "onion-study-three", "yuzu", "ginger", "cranberry"},
    "Scenery": {"cloud", "tree", "rock-island", "church-walkthrough"},
}

REJECTED_ASSETS = {
    "veiled-woman-study": "veiled-woman-360.gif",
    "woman-bust-study": "woman-bust-360.gif",
    "classical-woman-bust-study": "classical-woman-bust-360.gif",
}

DUPLICATE_ASSETS = {
    "david": "david-360.gif", "laocoon": "laocoon-360.gif",
    "nike": "nike-360.gif", "thinker": "thinker-360.gif",
}


def release_blockers(page):
    blockers = []
    for figure in page.figures:
        needed = 2 if figure["key"] in STATUE_PAIR_KEYS else 1
        links = {url for url in figure["links"] if public_text_link(url)}
        if len(links) < needed:
            blockers.append(f"{figure['key']}: needs {needed} verified public AAHub text link(s)")
    return blockers


class ArtTests(unittest.TestCase):
    def setUp(self):
        self.page = load_page()

    def test_requested_section_order(self):
        principal = [h for h in self.page.headings if h in
                     {"Drawings & Digital", "Drawings", "Paintings", "ASCII Art", "Photography"}]
        self.assertEqual(principal, ["Drawings & Digital", "Drawings", "Paintings",
                                     "ASCII Art", "Photography"])

    def test_active_gifs_are_unique_and_byte_preserved(self):
        images = [image for figure in self.page.figures for image in figure["images"]]
        excluded = set(REJECTED_ASSETS.values()) | set(DUPLICATE_ASSETS.values())
        self.assertEqual(len(images), 23)
        self.assertEqual({Path(image["src"]).name for image in images}, set(GIF_HASHES) - excluded)
        for image in images:
            path = ROOT / image["src"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), GIF_HASHES[path.name])
            self.assertTrue(path.read_bytes().startswith((b"GIF87a", b"GIF89a")))

    def test_rejected_and_duplicate_cards_are_absent_but_assets_are_preserved(self):
        for root in (ROOT, DEPLOYMENT_ROOT):
            html = (root / "art.html").read_text()
            for key in set(REJECTED_ASSETS) | set(DUPLICATE_ASSETS):
                self.assertNotIn(f'data-art-key="{key}"', html)
            self.assertEqual(len(load_page(root).figures), 23)
        for filename in set(REJECTED_ASSETS.values()) | set(DUPLICATE_ASSETS.values()):
            asset = ROOT / "img/ascii" / filename
            self.assertTrue(asset.is_file())
            self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(), GIF_HASHES[filename])

    def test_all_original_ascii_gif_assets_remain_byte_exact_in_both_clones(self):
        self.assertEqual(len(GIF_HASHES), 30)
        for root in (ROOT, DEPLOYMENT_ROOT):
            for filename, digest in GIF_HASHES.items():
                asset = root / "img/ascii" / filename
                self.assertTrue(asset.is_file(), str(asset))
                self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(), digest)

    def test_gif_captions_and_accessibility(self):
        for figure in self.page.figures:
            self.assertTrue(figure["caption"].strip())
            if figure["key"] in {
                "tree", "rock-island", "hand",
            }:
                self.assertIn("Text source pending", figure["caption"])
                self.assertNotIn("AAHub", figure["caption"])
            else:
                self.assertIn("AAHub", figure["caption"])
            self.assertNotIn("#", figure["caption"])
            for image in figure["images"]:
                self.assertTrue(image.get("alt"))
                self.assertEqual(image.get("loading"), "lazy")
                self.assertGreater(int(image["width"]), 0)
                self.assertGreater(int(image["height"]), 0)

    def test_existing_images_remain(self):
        existing = [image["src"] for image in self.page.images
                    if not image["src"].startswith(("img/ascii/", "img/instagram/", "img/branding/"))]
        self.assertEqual(len(existing), 30)  # 11 drawings and 19 photographs.
        self.assertEqual(len(set(existing)), 30)
        for source in existing:
            self.assertTrue((ROOT / source).is_file(), source)

    def test_yuuz_logo_preserves_high_resolution_original(self):
        logos = [im for im in self.page.images if im["src"].startswith("img/branding/")]
        self.assertEqual(len(logos), 1)
        logo = logos[0]
        self.assertEqual(logo["src"], "img/branding/yuuz-logo-blue.png")
        self.assertEqual((logo["width"], logo["height"]), ("1659", "1659"))
        self.assertIn("dark blue square", logo["alt"])
        self.assertEqual(hashlib.sha256((ROOT / logo["src"]).read_bytes()).hexdigest(),
                         "ceb9a3656ed1131e1a746b985107be0b0b3ff267142fdce5a7eeda6871dd24b9")
        html = (ROOT / "art.html").read_text()
        self.assertIn('Logo artwork I drew for YUUZ. visit <a href="https://yuuz.co/">yuuz.co</a> to order some!', html)
        self.assertNotIn('img/branding/yuuz-logo.png', html)

    def test_plain_underlined_carousel_controls_and_no_internal_copy(self):
        html = (ROOT / "art.html").read_text()
        controls = re.search(r"\.carousel-controls button\s*\{([^}]+)\}", html).group(1)
        for declaration in ("border: 0;", "background: transparent;", "padding: 0;",
                            "text-decoration: underline;"):
            self.assertIn(declaration, controls)
        self.assertIn(".carousel-controls button:focus-visible", html)
        self.assertNotIn("references from the export manifest", html)
        self.assertNotIn("These are reference collections", html)
        copy = re.sub(r"<(script|style)\b[^>]*>[\s\S]*?</\1>", "", html)
        self.assertNotRegex(re.sub(r"<[^>]+>", "", copy), r"[-\u2010-\u2015\u2212]")
        for value in re.findall(r'(?:alt|title|aria-label)="([^"]*)"', copy):
            self.assertNotRegex(value, r"[-\u2010-\u2015\u2212]")

    def test_instagram_archive_covers_reviewed_profile_artwork(self):
        manifest = json.loads((ROOT / "img/instagram/manifest.json").read_text())
        images = [im for im in self.page.images if im["src"].startswith("img/instagram/")]
        self.assertEqual(len(images), 301)
        self.assertEqual(len(set(self.page.instagram_keys)), 301)
        self.assertEqual(len(set(self.page.instagram_posts)), 53)
        self.assertEqual(len({urlsplit(url)._replace(query="").geturl()
                              for url in self.page.instagram_posts}), 52)
        self.assertEqual(manifest["profile_post_count"], 52)
        self.assertEqual(manifest["profile_media_reviewed"], 316)
        self.assertEqual(manifest["current_profile_artwork_images"], 298)
        self.assertEqual(manifest["excluded_non_art_images"], 18)
        self.assertEqual(manifest["historical_retained_images"], 3)
        self.assertEqual(sum(im["retained_from_previous_gallery"] for im in manifest["images"]), 84)
        self.assertEqual({Path(im["src"]).name for im in images},
                         {im["filename"] for im in manifest["images"]})
        self.assertNotIn("01_CMWbWuDBngT_07_march-12-2021.jpg",
                         {Path(im["src"]).name for im in images})
        by_name = {im["filename"]: im for im in manifest["images"]}
        for im in images:
            path = ROOT / im["src"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             by_name[path.name]["sha256"])
            deployment_path = DEPLOYMENT_ROOT / im["src"]
            self.assertEqual(hashlib.sha256(deployment_path.read_bytes()).hexdigest(),
                             by_name[path.name]["sha256"])
            self.assertTrue(im.get("alt"))
            self.assertEqual(im.get("loading"), "lazy")
            self.assertGreater(int(im["width"]), 0)
            self.assertGreater(int(im["height"]), 0)
        html = (ROOT / "art.html").read_text()
        self.assertIn('id="instagram-drawings-heading">Drawings</h2>', html)
        self.assertIn('id="instagram-paintings-heading">Paintings</h2>', html)
        self.assertIn('aria-roledescription', html)
        self.assertNotIn("Bp8iSB7F6wJ-2", self.page.instagram_keys)
        self.assertNotIn("BmdMzLvA116-8", self.page.instagram_keys)
        self.assertFalse(any(key.startswith("BpoNvTKFNbD-") for key in self.page.instagram_keys))

    def test_instagram_is_undated_carousel_archive(self):
        html = (ROOT / "art.html").read_text()
        self.assertNotIn("\u2014", html)
        self.assertEqual(re.findall(
            r'<div class="instagram-carousel" data-carousel data-carousel-label="([^"]+)">',
            html), ["Drawings", "Paintings"])
        self.assertEqual(self.page.instagram_summaries, [])
        section = re.search(
            r'aria-labelledby="instagram-drawings-heading">([\s\S]*?)</section>', html).group(1)
        visible_copy = re.sub(r"<[^>]+>", "", section)
        self.assertNotRegex(visible_copy, r"\b(?:19|20)\d{2}\b")
        self.assertNotIn("<time", section)
        self.assertNotIn("<details", section)
        self.assertEqual(html.count('class="instagram-source"'), 301)
        deploy_html = (DEPLOYMENT_ROOT / "art.html").read_text()
        blocks = r'<figure data-instagram-key="[\s\S]*?</figure>'
        self.assertEqual(re.findall(blocks, html), re.findall(blocks, deploy_html))
        self.assertIn("carousel-controls", html)
        self.assertIn("ArrowLeft", html)
        self.assertIn("ArrowRight", html)
        self.assertIn("Image ${index + 1} of ${slides.length}", html)

    def test_painting_classification_drives_two_independent_carousels(self):
        html = (ROOT / "art.html").read_text()
        tagged = set(re.findall(
            r'<figure data-instagram-key="([^"]+)" data-instagram-category="painting">', html))
        self.assertEqual(tagged, PAINTING_KEYS)
        self.assertEqual(len(tagged), 17)
        painting_order = [key for key in self.page.instagram_keys if key in tagged]
        self.assertEqual(painting_order[:2], ["B0JleytJj_8-1", "B0JleytJj_8-2"])
        self.assertEqual(len(set(self.page.instagram_keys) - tagged), 284)
        self.assertTrue(UNCERTAIN_PAINTING_KEYS.isdisjoint(tagged))
        self.assertTrue(UNCERTAIN_PAINTING_KEYS <= set(self.page.instagram_keys) - tagged)
        for key in self.page.instagram_keys:
            self.assertEqual(html.count(f'data-instagram-key="{key}"'), 1)
        self.assertIn('data-instagram-gallery="drawings"', html)
        self.assertIn('data-instagram-gallery="paintings"', html)
        self.assertIn('data-instagram-paintings-section hidden', html)
        self.assertIn('paintings.forEach((painting) => paintingsGallery.append(painting));', html)
        self.assertIn('paintingsSection.hidden = paintings.length === 0;', html)
        self.assertIn('alt="Red and pink abstract painting."', html)
        first_view = re.search(r'<figure data-instagram-key="B0JleytJj_8-1"[\s\S]*?</figure>', html).group(0)
        self.assertIn('data-instagram-category="painting"', first_view)
        self.assertIn('alt="Close view of a red and pink abstract painting on a dark background."', first_view)
        self.assertRegex(first_view, r'<figcaption>Oil on blackboard <a class="instagram-source" href="https://www\.instagram\.com/p/B0JleytJj_8/\?img_index=1">View original</a></figcaption>')
        painting = re.search(r'<figure data-instagram-key="B0JleytJj_8-2"[\s\S]*?</figure>', html).group(0)
        self.assertNotIn('Red digital compositions', painting)
        self.assertIn('alt="Red and pink abstract painting."', painting)
        self.assertRegex(painting, r'<figcaption>Oil on blackboard <a class="instagram-source" href="https://www\.instagram\.com/p/B0JleytJj_8/\?img_index=2">View original</a></figcaption>')
        self.assertNotIn("Red and pink abstract painting", first_view[first_view.index("<figcaption>"):])
        selected_image = "img/instagram/06_B0JleytJj_8_01_july-20-2019.jpg"
        expected_hash = "2cb202309753d88138ffa35b7262219dab480c3e1650f7e639dec34dc93bc37f"
        for root in (ROOT, DEPLOYMENT_ROOT):
            self.assertEqual(hashlib.sha256((root / selected_image).read_bytes()).hexdigest(), expected_hash)
        self.assertIn('const carouselLabel = carousel.dataset.carouselLabel || "Artwork";', html)
        self.assertIn('`${carouselLabel} carousel`', html)
        self.assertIn('`Previous ${carouselLabel.toLowerCase()} image`', html)
        self.assertIn('`Next ${carouselLabel.toLowerCase()} image`', html)

    def test_ascii_categories_are_independent_and_cover_the_approved_set(self):
        expected = set().union(*ASCII_CATEGORY_KEYS.values())
        self.assertEqual(len(expected), 23)
        for root in (ROOT, DEPLOYMENT_ROOT):
            page = load_page(root)
            self.assertEqual({figure["key"] for figure in page.figures}, expected)
            actual = {}
            for figure in page.figures:
                actual.setdefault(figure["category"], set()).add(figure["key"])
            self.assertEqual(actual, ASCII_CATEGORY_KEYS)
            urls = {link for figure in page.figures for link in figure["links"]}
            self.assertEqual(len(urls), 25)
            html = (root / "art.html").read_text()
            self.assertEqual(re.findall(
                r'data-carousel data-carousel-label="(Vehicles|Statues and Studies|Fruits and Vegetables|Scenery)"',
                html), list(ASCII_CATEGORY_KEYS))
            self.assertEqual(html.count('class="ascii-carousel" data-carousel'), 4)
            self.assertIn('querySelector("[data-carousel-gallery]")', html)
            self.assertIn('gallery.setAttribute("aria-roledescription", "carousel")', html)
            self.assertIn('gallery.setAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight")', html)
            self.assertIn('status.setAttribute("aria-live", "polite")', html)

    def test_requested_first_drawing_and_first_statue_keep_remaining_order(self):
        # Riki 2026-10-26: live Drawings "Image 30 of 284" (B3u2M00pHCk-6) first; Winged Victory first in
        # Statues and Studies. Every other drawing and statue card keeps its previous relative order (sha256 of the
        # newline-joined keys taken from release 9f868c0 before the move).
        def joined(keys):
            return hashlib.sha256("\n".join(keys).encode()).hexdigest()
        for root in (ROOT, DEPLOYMENT_ROOT):
            page = load_page(root)
            drawings = [key for key in page.instagram_keys if key not in PAINTING_KEYS]
            self.assertEqual(len(drawings), 284)
            self.assertEqual(drawings[:4], ["B3u2M00pHCk-6", "CMWbWuDBngT-1", "CMWbWuDBngT-2", "CMWbWuDBngT-3"])
            self.assertEqual(drawings.count("B3u2M00pHCk-6"), 1)
            self.assertEqual(joined(drawings[1:]),
                             "4c69b8aa2150a0f3bfcdbb748d4190b98971c1d1083565973d08eb150623d5c0")
            paintings = [key for key in page.instagram_keys if key in PAINTING_KEYS]
            self.assertEqual(paintings[:2], ["B0JleytJj_8-1", "B0JleytJj_8-2"])
            statues = [figure["key"] for figure in page.figures if figure["category"] == "Statues and Studies"]
            self.assertEqual(statues, ["winged-victory-study", "david-study", "laocoon-study",
                                       "thinker-study", "eve-study", "hand"])
            self.assertEqual(joined(statues[1:]),
                             "247a74d888727f7e8dd84f89077ed9e7f68258754d5b4f9f0c11e0691041def0")

    def test_no_private_draft_or_local_file_links(self):
        html = (ROOT / "art.html").read_text()
        self.assertNotIn("/my-mlt/", html)
        self.assertNotIn("file://", html)
        self.assertNotIn("/Users/", html)
        for figure in self.page.figures:
            for link in figure["links"]:
                self.assertTrue(public_text_link(link))

    def test_release_gate_does_not_accept_pending_or_profile_links(self):
        self.assertFalse(public_text_link("https://aahub.org/profile/legumeboi"))
        self.assertFalse(public_text_link("https://aahub.org/my-mlt/example/edit"))
        self.assertTrue(public_text_link("https://aahub.org/mlts/example"))
        fixture = ArtPage()
        fixture.figures = [{"key": "david-study", "links": ["https://aahub.org/mlts/first"]}]
        self.assertTrue(release_blockers(fixture))
        fixture.figures[0]["links"].append("https://aahub.org/mlts/second")
        self.assertEqual(release_blockers(fixture), [])

    def test_five_approved_statue_cards_require_both_public_halves(self):
        statue_keys = [
            "david-study", "laocoon-study", "winged-victory-study", "thinker-study", "eve-study",
        ]
        fixture = ArtPage()
        fixture.figures = [{"key": key, "links": [f"https://aahub.org/mlts/{key}-first"]}
                           for key in statue_keys]
        self.assertEqual(release_blockers(fixture),
                         [f"{key}: needs 2 verified public AAHub text link(s)" for key in statue_keys])
        for figure in fixture.figures:
            figure["links"].append(f"https://aahub.org/mlts/{figure['key']}-second")
        self.assertEqual(release_blockers(fixture), [])

    def test_gallery_text_source_status_matches_confirmed_native_text(self):
        expected = {
            "ae86": ["7mfncb2dh74y"], "bluebird510": ["uryz5d39csus"],
            "cresta-gx71": ["0hxv4wfzr6bt"], "sambar": ["gveqvs5erv5d"],
            "porsche911": ["n7art7fwryaw"], "streamlined-car": ["zqnwhqyuhg9z"],
            "onion": ["tjcy1xz5t603"], "cloud": ["0izuaxfv3phw"],
            "tree": [], "rock-island": [], "hand": [],
            "church-walkthrough": ["o8m3xp7dz47t"],
            "onion-study-one": ["mri3oifrtiup"],
            "onion-study-two": ["0zarcgqpd46m"],
            "onion-study-three": ["0s5cmyub3a17"],
            "david-study": ["1tbub96qu8s0", "d5c5vdj98zqz"],
            "laocoon-study": ["fknq0p4x2myr", "a0dkm2e9nvau"],
            "winged-victory-study": ["i5mj1bvq4gpp", "niq0kldfgm1a"],
            "thinker-study": ["zn5q2qssvjva", "cnkfqw310dbm"],
            "eve-study": ["dhmzwfz1oq3j", "vb8d39c1pqi6"],
            "yuzu": ["md8lacyc2v52"], "ginger": ["1f3mhq7qugqq"],
            "cranberry": ["j2x92is6ejf8"],
        }
        self.assertEqual({figure["key"] for figure in self.page.figures}, set(expected))
        for figure in self.page.figures:
            if expected[figure["key"]]:
                self.assertEqual(figure["links"],
                                 [f"https://aahub.org/mlts/{item}"
                                  for item in expected[figure["key"]]])
                self.assertNotIn("pending", figure["caption"].lower())
            else:
                self.assertIn(figure["key"], {
                    "tree", "rock-island", "hand",
                    "david-study", "laocoon-study", "winged-victory-study",
                    "thinker-study", "eve-study",
                })
                self.assertEqual(figure["links"], [])
                self.assertIn("Text source pending", figure["caption"])
        self.assertEqual(release_blockers(self.page),
                         [
                             "hand: needs 1 verified public AAHub text link(s)",
                             "tree: needs 1 verified public AAHub text link(s)",
                             "rock-island: needs 1 verified public AAHub text link(s)",
                         ])


if __name__ == "__main__":
    if "--media-release" in sys.argv:
        result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ArtTests))
        print(f"GIF-only release: {len(release_blockers(load_page()))} gallery entries still await verified AAHub text links; none claimed published.")
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if "--release" in sys.argv:
        blockers = release_blockers(load_page())
        print("\n".join(blockers) if blockers else "Public link structure passes; verify matching native text and rights directly.")
        raise SystemExit(1 if blockers else 0)
    unittest.main()
