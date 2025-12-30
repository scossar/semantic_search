from lxml import etree, html
from lxml.html import HtmlElement
import copy
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


def extract_text_sections(section: HtmlElement):
    print(serialize(section, pretty_print=True))
    text = ""
    for element in section.iter():
        if element.tag == "code":
            lang = element.get("class")
            code = f"({lang}):\n"
            for line in element.iterchildren():
                print("in line")
                line_text = "".join(line.itertext())
                code += line_text
            text += code

    return text


def extract_sections(filename: str):
    tree = html.parse(filename)
    root = tree.find(".//article")
    heading_tags = ("h1", "h2", "h3", "h4", "h5", "h6")
    sections = []
    current_heading = None
    current_fragment = None
    headings_path = []

    for child in root.iterchildren():
        if child.tag in heading_tags:
            if current_fragment is not None:
                html_fragment = serialize(current_fragment, pretty_print=True)
                html_heading = serialize(current_heading, pretty_print=True)
                sections.append(
                    {
                        "html_fragment": html_fragment,
                        "html_heading": html_heading,
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
        sections.append(
            {
                "html_fragment": html_fragment,
                "html_heading": html_heading,
            }
        )
    return sections


def extract_sections_bak(filename: str):
    tree = html.parse(filename)
    # using article as root and iterchildren is making assumptions about the HTML structure
    # it works for my case though
    root = tree.find(".//main")
    heading_tags = ("h1", "h2", "h3", "h4", "h5", "h6")
    sections = []
    current_fragment = None
    current_heading = None
    # current_embedding_texts = []
    current_heading_path = []
    file_href = str(Path(filename).parent)

    for child in root.iterdescendants():
        print("child.tag", child.tag)
        for element in child.iter():
            if element.tag in heading_tags:
                if current_fragment is not None:
                    serialized_fragment = serialize(current_fragment, pretty_print=True)
                    print("serialized fragment:\n", serialized_fragment)
                    serialized_heading = serialize(current_heading, pretty_print=True)
                    # embedding_texts = extract_text_sections(current_fragment)
                    sections.append(
                        {
                            "html_fragment": serialized_fragment,
                            "html_heading": serialized_heading,
                            # "embedding_texts": embedding_texts,
                        }
                    )

                heading_level = get_heading_level(element.tag)

                heading_id = element.attrib.get("id")
                if heading_id:
                    heading_href = f"{file_href}#{heading_id}"
                else:
                    heading_href = file_href
                heading_link = etree.Element("a", {"href": heading_href})
                heading_link.text = element.text
                current_heading = etree.Element(element.tag)
                current_heading.append(heading_link)
                current_heading_path = current_heading_path[:heading_level] + [
                    element.text
                ]
                current_fragment = etree.Element("div", {"class": "article-fragment"})

            elif current_fragment is not None:
                # deal with HTML comment elements
                if not isinstance(element, HtmlElement):
                    new_element = copy.deepcopy(element)
                else:
                    # create new element instead of copying element
                    # new_element = etree.Element(element.tag, element.attrib)
                    # new_element.text = element.text
                    # new_element.tail = element.tail
                    new_element = copy.deepcopy(element)

                current_fragment.append(new_element)
                for child in element.iterchildren():
                    print("remove tag:", child.tag)
                    element.remove(child)

    if current_fragment is not None:
        serialized_fragment = serialize(current_fragment, pretty_print=True)
        print("serialized fragment:\n", serialized_fragment)
        serialized_heading = serialize(current_heading, pretty_print=True)
        # embedding_texts = extract_text_sections(current_fragment)
        sections.append(
            {
                "html_fragment": serialized_fragment,
                "html_heading": serialized_heading,
                # "embedding_texts": embedding_texts,
            }
        )

    return sections
