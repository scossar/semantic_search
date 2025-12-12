import frontmatter

# import toml
from frontmatter import Post
from postchunker import extract_sections
from pathlib import Path
from typing import cast, Any
import mistune

postspath = "/home/scossar/zalgorithm/content"
# To generate an AST, call with `markdown(post.content)`
# See https://github.com/lepture/mistune/blob/4adac1c6e7e14e7deeb1bf6c6cd8c6816f537691/docs/renderers.rst#L56
# for the list of available methods (list of nodes that will be generated)
markdown = mistune.create_markdown(
    renderer=None, plugins=["footnotes"]
)  # Creates an AST renderer


def should_process_file(filepath: Path) -> bool:
    if any(part.startswith(".") for part in filepath.parts):
        print("starts with .")
        return False
    if filepath.suffix.lower() not in (".md", ".markdown"):
        return False
    return True


def load_file(filepath: str) -> Post:
    # print("filepath", filepath)
    # path = str(filepath)
    post = frontmatter.load(filepath)
    return post


for path in Path(postspath).rglob("*"):
    if not should_process_file(path):
        continue
    stem = path.stem
    # I'm just checking a single file for testing
    # stem_name = "chunking_hugo_post_content_for_semantic_search"
    stem_name = "roger-bacon-as-magician"
    if stem == stem_name:
        pathstr = str(path)
        post = load_file(pathstr)
        title = str(post["title"])  # it's a string
        nodes = markdown(post.content)
        # From `markdown.py`, the __call__(self, s: str) method calls `self.parse(s)[0]`
        # The return type is `Union[str, List[Dict[str, Any]]]`, but for the "None" renderer
        # the returned type will be `List[Dict[str, Any]]`
        nodes = cast(list[dict[str, Any]], nodes)
        # for node in nodes[:25]:
        #     print(node)
        #     print("\n")
        sections = extract_sections(nodes, headings=[title])
        for section in sections:
            print(section)
            print("")
