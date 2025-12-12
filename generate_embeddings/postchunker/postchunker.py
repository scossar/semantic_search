from typing import Any, Dict, List
import re

__all__ = ["extract_sections"]


def extract_text_from_node(node: Dict[str, Any]) -> str:
    if node["type"] == "text":
        return node["raw"]

    # this will remove the footnotes section, as long as it's properly structured
    # TODO: check how brittle this is
    if node["type"] == "footnote_item":
        return ""

    if node["type"] == "block_code":
        lang = node["attrs"].get("info", "")
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


def clean_text(text: str) -> str:
    # remove footnote references:
    text = re.sub(r"\[\^\d+\]", "", text)
    return text


# Possible improvements:
# - add sliding window
# - check content length and handle short/long content
def extract_sections(
    ast: List[Dict[str, Any]], headings: List[str] = []
) -> List[Dict[str, str]]:
    sections = []
    current_section = {"headings": headings, "content": []}

    for node in ast:
        if node["type"] == "heading":
            #  append previouw section to sections
            if current_section["content"]:
                sections.append(current_section)

            # start a new section
            heading_text = extract_text(node["children"])
            level = node["attrs"]["level"]

            headings = headings[: level - 1] + [heading_text]
            current_section = {"headings": headings, "content": []}

        else:
            text = extract_text_from_node(node)
            text = clean_text(text)
            if text.strip():
                current_section["content"].append(text)

    # append the last section
    if current_section["content"]:
        sections.append(current_section)

    return sections
