#!.venv/bin/python
import os
import shutil
import subprocess
import sys
import traceback

from bs4 import BeautifulSoup as Soup

class StopGrading(Exception):
    pass

def children(element):
    return [e for e in element if not isinstance(e, str)]


def parents(soup):
    """find all the ancestors of an element"""
    s, p = [], soup
    while p:
        s.append(p)
        p = p.parent
    return s


def common_ancestor(a, b):
    """find a commo ancestor between two elements"""
    parents_a = parents(a)
    parents_b = parents(b)
    for item in parents_a:
        if item in parents_b:
            return item
    return None

class ProtoAssignment:
    def __init__(self, folder, max_grade):
        self.folder = folder
        self._max_grade = max_grade
        self._comments = []

    def add_comment(self, comment, points=0):
        self._comments.append((comment, points))

    def grade(self):
        steps = [getattr(self, name) for name in dir(self) if name.startswith("step")]
        for step in steps:
            try:
                step()
            except StopGrading:
                break
            except:
                print(traceback.format_exc())
                self.add_comment(step.__doc__ + " (Unable to grade)", 0)
        grade = 0
        for comment, points in self._comments:
            print("=" * 40)
            print(f"[{points:.2f} points]", comment)
            grade += points
        print("=" * 40)
        print(f"TOTAL GRADE {grade:.2f}")
        print("=" * 40)
        return grade


class Assignment(ProtoAssignment):

    def __init__(self, folder):
        super().__init__(folder, max_grade=3)

    def step01(self):
        "it should have a <head/> and a <bod/y>"
        self.filename = os.path.join(self.folder, "index.html")
        success = False
        if not os.path.exists(self.filename):
            self.add_comment("cannot find the file", 0)
        else:
            try:
                with open(self.filename) as content:
                    self.soup = Soup(content, "html.parser")
                    success = self.soup.find("head") and self.soup.find("body")
            except:
                self.add_comment("file cannot be read or parsed", 0)
        self.add_comment(self.step01.__doc__, 0.5 if success else 0)
        if not success:
            raise StopGrading

    def step02(self):
        "it should use the Bulma css library"
        link = self.soup.find("link")
        url = link["href"].lower()
        success = "bulma" in url and url.endswith(".css")
        self.add_comment(self.step02.__doc__, 0.5 if success else 0)
        if not success:
            raise StopGrading

    def step03(self):
        "it should contain a <header/> a <footer/> and two <section/>s in between"
        body = self.soup.find("body")
        self.children = children(body)
        names = [c.name for c in self.children]
        success = len(self.children) == 4 and names == [
            "header",
            "section",
            "section",
            "footer",
        ]
        self.add_comment(self.step03.__doc__, 1 if success else 0)
        if not success:
            raise StopGrading

    def step04(self):
        "One section with class top and one with class bottom"
        success = (
            "top" in self.children[1]["class"] and "bottom" in self.children[2]["class"]
        )
        self.add_comment(self.step04.__doc__, 1 if success else 0)

    def step05(self):
        "The top section should contain an <img/> that fills the page horizontally and show the image of a cat"
        image = self.children[1].find("img")
        success = image
        self.add_comment(self.step05.__doc__, 1 if success else 0)

    def step06(self):
        "The bottom section should contain 6 columns"
        columns = self.children[2].find("div", class_="columns")
        self.cols = columns and children(columns) or []
        success = len(self.cols) == 6 and all("column" in e["class"] for e in self.cols)
        self.add_comment(self.step06.__doc__, 1 if success else 0)
        if not success:
            raise StopGrading

    def step07(self):
        "Each column should contain a card"
        self.cards = [c.find("div", class_="card") for c in self.cols]
        success = all(self.cards)
        self.add_comment(self.step07.__doc__, 1 if success else 0)
        if not success:
            raise StopGrading

    def step08(self):
        "each card should have a header and content"
        success = all(
            card.find(class_="card-header") and card.find(class_="card-content")
            for card in self.cards
        )
        self.add_comment(self.step08.__doc__, 1 if success else 0)

    def step09(self):
        "each card content the cards be some text of your choice followed by a button. In total there should 6 buttons, one per column, one of each of the Bulma styles"
        expected = ["primary", "link", "info", "success", "warning", "danger"]
        styles = []
        for col in self.cols:
            card = col.find("div", class_="card")
            button = card.find("button")
            if button:
                classes = button["class"]
                if "button" in classes:
                    for style in expected:
                        if f"is-{style}" in classes:
                            styles.append(style)
                            break
        success = set(expected) == set(styles)
        self.add_comment(self.step09.__doc__, 1 if success else 0)

    def step10(self):
        "each card header should have title with the name of the style of the corrensponding button."
        expected = ["primary", "link", "info", "success", "warning", "danger"]
        match = 0
        for card in self.cards:
            title = card.find(class_="card-header-title")
            if title:
                name = title.text.strip().lower()
                if name in expected:
                    expected.remove(name)
                    button = card.find("button", class_=f"is-{name}")
                    if button:
                        match += 1
        success = match == 6
        self.add_comment(self.step10.__doc__, 1 if success else 0)

    def step11(self):
        "the footer contain a link that, on click, will open the user's default email app with To: file equalt to your email address. The text of the link should be youor name."
        self.footer_links = self.children[3].findAll("a")
        success = any(link["href"].startswith("mailto:") for link in self.footer_links)
        self.add_comment(self.step11.__doc__, 1 if success else 0)

if __name__ == "__main__":
    tests = Assignment(".")
    tests.grade()
