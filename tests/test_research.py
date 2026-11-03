"""Research-page structure checks; --release rejects the unhosted devlog."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASCII_LINKS = {
    "https://rikiworld.com/xpedit",
    "https://github.com/rikiyanai/AsciickerY92-CP437-runtime",
    "https://github.com/rikiyanai/unicode-glyph-morphology-explorer",
    "https://github.com/rikiyanai/DylanEbert-texel-splatting-demo-godot-port",
    "https://github.com/rikiyanai/daily-neovim-ascii-art-tutor",
    "https://github.com/rikiyanai/3d-Space",
    "https://github.com/rikiyanai/rextuul",
    "https://github.com/rikiyanai/Xu-structured-ascii-art-algorithm-reproduction-experiments",
    "https://github.com/rikiyanai/screenshot-of-ascii-art-to-txt-converter",
}
OTHER_LINKS = {
    "papers/MAT401finaldraft.pdf", "papers/MAT331_ElGamal_Project.pdf",
    "https://github.com/rikiyanai/MAT200KARLLEVY",
    "https://varietym1.co.jp/pages/6/#block40-37", "https://drinkyuuz.com/",
    "https://rikiworld.com/lateletter/", "https://rikiworld.com/drawloom/",
    "https://rikiworld.com/refrog-app/", "https://github.com/rikiyanai/Terminotes",
}


class ResearchPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.section = None
        self.sections = []
        self.links = []
        self.latest = None
        self.in_latest = False
        self.position = 0
        self.titles = []
        self.title = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.position += 1
        if tag == "section":
            self.section = attrs.get("aria-labelledby")
            self.sections.append(self.section)
        if tag == "a" and "project-title" in attrs.get("class", "").split():
            self.title = ""
            self.links.append((self.section, attrs.get("href"), self.position))
        if tag == "article" and "latest-devlog" in attrs.get("class", "").split():
            self.latest = {"section": self.section, "position": self.position,
                           "status": attrs.get("data-publication-status"),
                           "links": [], "text": "", "date": None}
            self.in_latest = True
        if self.in_latest and tag == "a":
            self.latest["links"].append(attrs.get("href"))
        if self.in_latest and tag == "time":
            self.latest["date"] = attrs.get("datetime")

    def handle_data(self, data):
        if self.title is not None:
            self.title += data
        if self.in_latest:
            self.latest["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.title is not None:
            self.titles.append(self.title.strip())
            self.title = None
        if tag == "section":
            self.section = None
        if tag == "article":
            self.in_latest = False


def load_page():
    page = ResearchPage()
    page.feed((ROOT / "research.html").read_text())
    return page


def release_blockers(page):
    if not page.latest or page.latest["status"] == "pending" or not page.latest["links"]:
        return ["Latest devlog needs a verified hosted destination before release."]
    return []


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.page = load_page()

    def test_no_separator_dashes_in_project_titles(self):
        for title in self.page.titles:
            self.assertNotRegex(title, r"\s[—–-]\s")
        self.assertIn("Asciicker Y92 CP437 Runtime", self.page.titles)
        self.assertIn("Xu Structured ASCII Art Experiments", self.page.titles)
        self.assertIn("Screenshot of ASCII Art to TXT Converter", self.page.titles)

    def test_no_em_dashes_in_research_copy(self):
        self.assertNotIn("\u2014", (ROOT / "research.html").read_text())

    def test_no_dash_punctuation_in_visible_research_copy(self):
        html = (ROOT / "research.html").read_text()
        copy = re.sub(r"<(script|style)\b[^>]*>[\s\S]*?</\1>", "", html)
        self.assertNotRegex(re.sub(r"<[^>]+>", "", copy), r"[-\u2010-\u2015\u2212]")
        for value in re.findall(r'(?:alt|title|aria-label)="([^"]*)"', copy):
            self.assertNotRegex(value, r"[-\u2010-\u2015\u2212]")

    def test_requested_heading_hierarchy_and_devlog_label(self):
        html = (ROOT / "research.html").read_text()
        self.assertIn('<h2 id="social-links-heading">Devlog</h2>', html)
        self.assertNotIn('>Elsewhere</h2>', html)
        other = re.search(r"#other-projects-heading\s*\{([^}]+)\}", html).group(1)
        social = re.search(r"\.social-links h2\s*\{([^}]+)\}", html).group(1)
        other_size = float(re.search(r"font-size:\s*([\d.]+)rem", other).group(1))
        social_size = float(re.search(r"font-size:\s*([\d.]+)rem", social).group(1))
        self.assertGreater(other_size, 1)
        self.assertLess(social_size, 1)
        self.assertGreater(other_size, social_size)

    def test_ascii_section_precedes_other_research(self):
        self.assertEqual(self.page.sections, ["ascii-projects-heading", "other-projects-heading"])

    def test_all_ascii_projects_grouped_without_duplicates(self):
        ascii_links = [url for section, url, _ in self.page.links if section == "ascii-projects-heading"]
        self.assertEqual(set(ascii_links), ASCII_LINKS)
        self.assertEqual(len(ascii_links), len(ASCII_LINKS))

    def test_unrelated_existing_projects_preserved_separately(self):
        other = [url for section, url, _ in self.page.links if section == "other-projects-heading"]
        self.assertEqual(set(other), OTHER_LINKS)
        self.assertEqual(len(other), len(OTHER_LINKS))
        all_links = [url for _, url, _ in self.page.links]
        self.assertEqual(len(all_links), len(set(all_links)))

    def test_latest_devlog_first_with_actual_title_and_date(self):
        latest = self.page.latest
        self.assertEqual(latest["section"], "ascii-projects-heading")
        self.assertEqual(latest["date"], "2026-10-21")
        self.assertIn("Trying to Make a Structural ASCII Shader", latest["text"])
        self.assertLess(latest["position"], min(pos for section, _, pos in self.page.links
                                             if section == "ascii-projects-heading"))

    def test_no_local_filesystem_or_localhost_project_links(self):
        for _, url, _ in self.page.links:
            parsed = urlsplit(url)
            self.assertNotIn(parsed.hostname, {"localhost", "127.0.0.1"})
            self.assertNotIn("/Users/", url)
            self.assertNotEqual(parsed.scheme, "file")
            if not parsed.scheme:
                self.assertTrue((ROOT / parsed.path).is_file(), url)

    def test_unhosted_devlog_cannot_be_claimed_release_ready(self):
        fixture = ResearchPage()
        fixture.latest = {"status": "pending", "links": []}
        self.assertTrue(release_blockers(fixture))


if __name__ == "__main__":
    if "--release" in sys.argv:
        blockers = release_blockers(load_page())
        print("\n".join(blockers) if blockers else "Devlog link present; verify its deployment and runtime directly.")
        raise SystemExit(1 if blockers else 0)
    unittest.main()
