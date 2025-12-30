from lxml import etree, html
from lxml.html import HtmlElement
from pathlib import Path

__all__ = ["extract_sections"]


def serialize(fragment: HtmlElement, pretty_print: bool = False):
    return html.tostring(
        fragment,
        pretty_print=pretty_print,
        method="html",
        encoding="unicode",
    )


def heading_link(original_heading: HtmlElement, filename: str):
    href = str(Path(filename).parent)
    id = original_heading.attrib.get("id")
    if id:
        href = f"{href}#id"

    anchor = etree.Element("a", {"href": href})
    anchor.text = original_heading.text
    heading = etree.Element(original_heading.tag)
    heading.append(anchor)

    return heading


def get_heading_level(tag: str) -> int:
    heading_levels = {"h1": 0, "h2": 1, "h3": 2, "h4": 3, "h5": 4, "h6": 5}
    return heading_levels[tag]


def section_texts(section: HtmlElement, headings_path: list[str]):
    section_heading = " > ".join(headings_path) + ": "
    section_heading_length = len(section_heading)
    texts = []
    for element in section.iterchildren():
        if element.tag == "p":
            text = "".join(element.itertext())
            # remove unnecessary newline characters
            text = " ".join(text.splitlines())
            texts.append({"tag": "p", "text": text})
        elif element.attrib.get("class") == "highlight":
            code_element = element.find(".//code")
            if code_element is not None:
                lang = code_element.get("class")
                code = f"({lang}):\n"
                for line in code_element.iterchildren():
                    line_text = "".join(line.itertext())
                    code += line_text

                if len(texts) and texts[-1].get("tag") == "p":
                    last_paragraph = texts[-1]["text"]
                    code = f"{last_paragraph}\n{code}"
                    texts[-1] = {"tag": "code", "text": code}
                else:
                    texts.append({"tag": "code", "text": code})

    sections = []
    word_count = 0
    current_section = ""
    for entry in texts:
        word_count += len(entry["text"].split(" "))
        if (
            word_count < (256 - section_heading_length) and entry["tag"] != "code"
        ):  # 256
            if current_section:
                current_section += f"\n{entry['text']}"
            else:
                current_section = entry["text"]

        else:
            if current_section:
                sections.append(section_heading + current_section)
            current_section = entry["text"]
            word_count = 0

    sections.append(section_heading + current_section)

    return sections


def extract_sections(filename: str):
    tree = html.parse(filename)
    root = tree.find(".//article")
    heading_tags = ("h1", "h2", "h3", "h4", "h5", "h6")
    sections = []
    current_heading = None
    current_fragment = None
    embeddings_text = []
    headings_path = []

    for child in root.iterchildren():
        if child.tag in heading_tags:
            if current_fragment is not None:
                html_fragment = serialize(current_fragment, pretty_print=True)
                html_heading = serialize(current_heading, pretty_print=True)
                embeddings_text = section_texts(current_fragment, headings_path)
                sections.append(
                    {
                        "html_fragment": html_fragment,
                        "html_heading": html_heading,
                        "embeddings_text": embeddings_text,
                    }
                )

            current_heading = heading_link(child, filename)
            current_fragment = etree.Element("div", {"class": "article-fragment"})

            heading_level = get_heading_level(child.tag)
            headings_path = headings_path[:heading_level] + [child.text]

        elif current_fragment is not None:
            current_fragment.append(child)

    if current_fragment is not None:
        html_fragment = serialize(current_fragment, pretty_print=True)
        html_heading = serialize(current_heading, pretty_print=True)
        embeddings_text = section_texts(current_fragment, headings_path)
        sections.append(
            {
                "html_fragment": html_fragment,
                "html_heading": html_heading,
                "embeddings_text": embeddings_text,
            }
        )
    return sections
