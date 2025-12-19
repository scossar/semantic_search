import frontmatter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import Collection
import re
import unidecode

# import toml
from frontmatter import Post
from sentence_transformers.util import semantic_search
from postchunker import extract_sections
from pathlib import Path
from typing import cast, Any
import mistune

postspath = "/home/scossar/zalgorithm/content"
# To generate an AST, call with `markdown(post.content)`
# See https://github.com/lepture/mistune/blob/4adac1c6e7e14e7deeb1bf6c6cd8c6816f537691/docs/renderers.rst#L56
# for the list of available methods (list of nodes that will be generated)
# list of available plugins: https://mistune.lepture.com/en/latest/plugins.html
markdown = mistune.create_markdown(
    renderer=None, plugins=["footnotes", "math"]
)  # Creates an AST renderer


class EmbeddingGenerator:
    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        persist_directory: str = "../chroma-data",
        content_directory: str = "/home/scossar/zalgorithm/content",
        collection_name: str = "zalgorithm",
        development_mode: bool = False,
        delete_collection: bool = False,
    ):
        self.skip_dirs: set[str] = {
            "node_modules",
            ".git",
            ".obsidian",
            "__pycache__",
            "venv",
            ".venv",
        }
        self.model = SentenceTransformer(model_name)
        self.development_mode = development_mode
        self.collection_name = collection_name
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        # self.collection = self.chroma_client.get_or_create_collection(name="zalgorithm")
        self.collection = self.get_or_create_collection(
            development_mode=development_mode, delete_collection=delete_collection
        )
        self.content_directory = content_directory

    def get_or_create_collection(
        self, development_mode: bool, delete_collection: bool = False
    ) -> Collection:
        if development_mode and delete_collection:
            try:
                self.chroma_client.delete_collection(self.collection_name)
            except ValueError:
                pass

        return self.chroma_client.get_or_create_collection(name=self.collection_name)

    def _should_process_file(self, filepath: Path) -> bool:
        if any(part.startswith(".") for part in filepath.parts):
            return False
        if any(skip_dir in filepath.parts for skip_dir in self.skip_dirs):
            return False
        if filepath.suffix.lower() not in (".md", ".markdown"):
            return False
        return True

    # Hoping this matches Hugo's implementation
    def _slugify(self, title: str) -> str:
        title = unidecode.unidecode(title).lower()
        title = re.sub(r"[^a-z0-9\s-]", "", title)
        title = re.sub(r"[\s_]+", "-", title)
        title = title.strip("-")  # strip leading/trailing hyphens
        return title

    def generate_embeddings(self):
        """
        Generate embeddings for blog content
        """
        for path in Path(self.content_directory).rglob("*"):
            if not self._should_process_file(path):
                continue
            self.generate_embedding(path)

    def generate_embedding(self, filepath: Path):
        """
        Generate embedding for a single file
        """
        post = frontmatter.load(str(filepath))
        file_mtime = filepath.stat().st_mtime
        title = str(post.get("title"))
        stem = filepath.stem
        post_id = post.get("id", None)
        if not post_id:
            print(
                f"The post '{stem}' is missing an 'id' field. Skipping generating an embedding."
            )
        nodes = markdown(post.content)
        nodes = cast(list[dict[str, Any]], nodes)
        sections = extract_sections(nodes, headings=[title])
        for section in sections:
            heading_slug = self._slugify(section["headings"][-1])
            section_id = f"{post_id}-{heading_slug}"
            relative_path = filepath.relative_to(self.content_directory).with_suffix("")
            anchor_link = f"/{relative_path}#{heading_slug}"

            headings = " > ".join(section["headings"])
            content = " ".join(section["content"])

            metadatas = {
                "title": title,
                "anchor_link": anchor_link,
                "updated_at": file_mtime,
            }
            documents = content
            ids = section_id

            embedding_content = f"{headings}: {content}"
            embeddings = self.model.encode(
                embedding_content, convert_to_numpy=True, normalize_embeddings=True
            )

            self.collection.upsert(
                embeddings=embeddings, ids=ids, metadatas=metadatas, documents=documents
            )

    def query_collection(self, query: str):
        query_embedding = self.model.encode(
            query, convert_to_numpy=True, normalize_embeddings=True
        )
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=7,
            include=["metadatas", "documents", "distances"],
        )

        if not (results["metadatas"] and results["documents"] and results["distances"]):
            return

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            print(
                f"{meta['title']}: {meta['anchor_link']} (distance: {dist:.3f})\ndocument: {doc}\n"
            )


embeddings_generator = EmbeddingGenerator(
    development_mode=True, delete_collection=False
)
# embeddings_generator.generate_embeddings()
embeddings_generator.query_collection("How do I stop tracking a file with git?")


# def should_process_file(filepath: Path) -> bool:
#     if any(part.startswith(".") for part in filepath.parts):
#         print("starts with .")
#         return False
#     if filepath.suffix.lower() not in (".md", ".markdown"):
#         return False
#     return True
#
#
# def load_file(filepath: str) -> Post:
#     # print("filepath", filepath)
#     # path = str(filepath)
#     post = frontmatter.load(filepath)
#     return post
#
#
# # for path in Path(postspath).rglob("*"):
# #     if not should_process_file(path):
# #         continue
# #     stem = path.stem
# #     # I'm just checking a single file for testing
# #     stem_name = "polynomial-functions"
# #     # stem_name = "notes-on-cognitive-and-morphological-patterns"
# #     if stem == stem_name:
# #         pathstr = str(path)
# #         post = load_file(pathstr)
# #         title = str(post["title"])  # it's a string
# #         nodes = markdown(post.content)
# #         # From `markdown.py`, the __call__(self, s: str) method calls `self.parse(s)[0]`
# #         # The return type is `Union[str, List[Dict[str, Any]]]`, but for the "None" renderer
# #         # the returned type will be `List[Dict[str, Any]]`
# #         nodes = cast(list[dict[str, Any]], nodes)
# #         # for node in nodes[:25]:
# #         #     print(node)
# #         #     print("\n")
# #         sections = extract_sections(nodes, headings=[title])
# #         chunks = generate_chunks(sections)
#
# for path in Path(postspath).rglob("*"):
#     if not should_process_file(path):
#         continue
#     pathstr = str(path)
#     post = load_file(pathstr)
#     title = str(post["title"])
#     nodes = markdown(post.content)
#     nodes = cast(list[dict[str, Any]], nodes)
#     sections = extract_sections(nodes, headings=[title])
#
#     for section in sections:
#         print("\n\n", section)
