from typing import cast, Any, Dict, List


__all__ = ["extract_sections"]


def extract_text_from_node(node: Dict[str, Any]) -> str:
    if node["type"] == "text":
        return node["raw"]

    if node["type"] == "image":
        # TODO: look into this
        return extract_text(node["children"])

    if node["type"] == "block_math" or node["type"] == "inline_math":
        return node.get("raw", "")

    # this will remove the footnotes section, as long as it's properly structured
    # TODO: check how brittle this is
    if node["type"] == "footnote_item":
        return ""

    if node["type"] == "block_code":
        # note that "attrs" is not set for "style": "indent" code blocks
        lang = node.get("attrs", {}).get("info", "")
        code = node["raw"]
        if lang:
            return f"\n\nCode ({lang}):\n{code}\n\n"
        return f"\n\nCode:\n{code}\n\n"

    if (
        node["type"] == "softbreak"
        or node["type"] == "linebreak"
        or node["type"] == "blank_line"
    ):
        return " "

    # a list is made up of list_items that contain block_text nodes
    if node["type"] == "list":
        items_text = extract_text(node["children"])
        return f"\n{items_text}\n"

    # list items
    if node["type"] == "list_item":
        item_text = extract_text(node["children"])
        return f"- {item_text}\n"

    # list_item text
    if node["type"] == "block_text":
        return extract_text(node["children"])

    if node["type"] == "paragraph":
        text = extract_text(node["children"])
        return text + "\n\n"

    if "children" in node:
        return extract_text(node["children"])

    return ""


def extract_text(nodes: List[Dict[str, Any]]) -> str:
    return "".join(extract_text_from_node(node) for node in nodes)


def extract_sections(
    ast: List[Dict[str, Any]], headings: List[str] = []
) -> List[Dict[str, str]]:
    sections = []
    current_section = {"headings": headings, "content": []}

    for node in ast:
        if node["type"] == "heading":
            #  append previous section to sections
            if current_section["content"]:
                sections.append(current_section)

            # start a new section
            heading_text = extract_text(node["children"])
            level = node["attrs"]["level"]

            headings = headings[: level - 1] + [heading_text]
            current_section = {"headings": headings, "content": []}

        else:
            text = extract_text_from_node(node)
            if text.strip():
                current_section["content"].append(text)

    # append the last section
    if current_section["content"]:
        sections.append(current_section)

    return sections


def extract_sections_with_html(
    ast: List[Dict[str, Any]], headings: List[str] = []
) -> List[Dict[str, str]]:
    sections = []
    current_section = {
        "headings": headings,
        "heading_text": "",
        "heading_level": None,
        "content": [],
        "tokens": [],
    }

    for token in ast:
        if token["type"] == "heading":
            #  append previous section to sections
            if current_section["content"]:
                sections.append(current_section)

            # start a new section
            heading_text = extract_text(token["children"])
            heading_level = token["attrs"]["level"]

            headings = headings[: heading_level - 1] + [heading_text]
            current_section = {
                "headings": headings,
                "heading_text": heading_text,
                "heading_level": heading_level,
                "content": [],
                "tokens": [],
            }

        else:
            current_section["tokens"].append(token)
            text = extract_text_from_node(token)
            if text.strip():
                current_section["content"].append(text)

    # append the last section
    if current_section["content"]:
        sections.append(current_section)

    return sections


## tests
import mistune

# note: the solution for markdown -> ast -> html is here: https://github.com/lepture/mistune/issues/217
from mistune.renderers.html import HTMLRenderer
from mistune.core import BlockState

# load a single file for testing
file_content = ""
with open(
    "/home/scossar/zalgorithm/content/notes/logistic-map.md",
    "r",
) as file:
    file_content = file.readlines()
file_content = "".join(file_content)
renderer = HTMLRenderer()

markdown = mistune.create_markdown(renderer=None)  # Creates an AST renderer
tokens = markdown(file_content)

tokens = cast(list[dict[str, Any]], tokens)

# Extracts and cleans text from each heading section for generating embeddings;
# Now also returns the nodes for each section. The second argument is the file's title, as it's not included in the markdown
sections = extract_sections_with_html(tokens, ["Logistic Map"])

for section in sections:
    section_tokens = section["tokens"]
    section_tokens = cast(list[dict[str, Any]], section_tokens)
    print(
        "SECTION HEADING:",
        section["heading_text"],
        "HEADING LEVEL:",
        section["heading_level"],
    )
    print(renderer(section_tokens, state=BlockState()))
