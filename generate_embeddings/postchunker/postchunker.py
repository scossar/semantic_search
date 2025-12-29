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


def get_heading_level(tag: str) -> int:
    heading_levels = {"h1": 0, "h2": 1, "h3": 2, "h4": 3, "h5": 4, "h6": 5}
    return heading_levels[tag]


def extract_sections(filename: str):
    tree = html.parse(filename)
    # using article as root and iterchildren is making assumptions about the HTML structure
    # it works for my case though
    root = tree.find(".//main")
    heading_tags = ("h1", "h2", "h3", "h4", "h5", "h6")
    sections = []
    current_fragment = None
    current_heading = None
    current_embedding_texts = []
    current_heading_path = []
    file_href = str(Path(filename).parent)

    for element in root.iter():
        if element.tag in heading_tags:
            if current_fragment is not None:
                serialized_fragment = serialize(current_fragment, pretty_print=True)
                serialized_heading = serialize(current_heading, pretty_print=True)
                sections.append(
                    {
                        "html_fragment": serialized_fragment,
                        "html_heading": serialized_heading,
                        "embedding_texts": current_embedding_texts,
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
            current_heading_path = current_heading_path[:heading_level] + [element.text]
            current_fragment = etree.Element("div", {"class": "article-fragment"})
            current_embedding_texts = []

        elif current_fragment is not None:
            # deal with HTML comment elements
            if not isinstance(element, HtmlElement):
                new_element = copy.deepcopy(element)
            else:
                # create new element instead of copying element
                new_element = etree.Element(element.tag, element.attrib)
                new_element.text = element.text
                new_element.tail = element.tail

            current_fragment.append(new_element)
            # sort of, but the code element's children still exist in the tree
            # so will be re-iterated over in the `else:` block
            if element.tag == "code":
                lang = element.get("class")
                code = f"({lang}):\n"
                for line in element.iterchildren():
                    line_text = "".join(line.itertext())
                    code += line_text

                current_embedding_texts.append(code)
            else:
                text = ""
                for child in element.iterchildren():
                    # getting there..., but so far away
                    if not isinstance(child, HtmlElement):
                        continue
                    child_text = "".join(child.itertext())
                    print("child_text:", child_text)
                    text += child_text
                current_embedding_texts.append(text)

    if current_fragment is not None:
        print("made it into the last part")
        serialized_fragment = serialize(current_fragment, pretty_print=True)
        serialized_heading = serialize(current_heading, pretty_print=True)
        sections.append(
            {
                "html_fragment": serialized_fragment,
                "html_heading": serialized_heading,
                "embedding_texts": current_embedding_texts,
            }
        )

    return sections
