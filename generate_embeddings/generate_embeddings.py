import frontmatter

# from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import Collection

# from chromadb.utils import embedding_functions
import re
import unidecode

# import toml
# from frontmatter import Post
# from sentence_transformers.util import semantic_search
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


# NOTES ##########################################################################################################
# see https://docs.trychroma.com/docs/embeddings/embedding-functions for details about custom embedding functions,
# i.e, creating one for for "all-mpnet-base-v2"
# ################################################################################################################


class EmbeddingGenerator:
    def __init__(
        self,
        content_directory: str = "/home/scossar/zalgorithm/content",
        collection_name: str = "zalgorithm",
    ):
        self.skip_dirs: set[str] = {
            "node_modules",
            ".git",
            ".obsidian",
            "__pycache__",
            "venv",
            ".venv",
        }
        self.collection_name = collection_name
        self.chroma_client = chromadb.PersistentClient()  # chroma will use the default `chroma` directory in the base of the project for persistence
        self.collection = self.get_or_create_collection()
        self.content_directory = content_directory

    def get_or_create_collection(self) -> Collection:
        return self.chroma_client.get_or_create_collection(name=self.collection_name)

    # todo: either respect 'draft' frontmatter boolean, or a 'private' boolean;
    # also, this function needs access to frontmatter
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

    # TODO: check file_mtime to see if new embedding should be created
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

            # quick hack (you don't want to use the parsed content here...)
            html = mistune.html(content)

            metadatas = {
                "title": title,
                "html": html,
                "anchor_link": anchor_link,
                "updated_at": file_mtime,
            }
            ids = section_id
            embedding_content = f"{headings}: {content}"

            self.collection.upsert(
                ids=ids, metadatas=metadatas, documents=embedding_content
            )

    def query_collection(self, query: str):
        results = self.collection.query(
            query_texts=[query],
            n_results=7,
            include=["metadatas", "documents", "distances"],
        )

        if not (results["metadatas"] and results["documents"] and results["distances"]):
            return

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        zipped = zip(ids, documents, metadatas, distances)

        for _, document, metadata, distance in zipped:
            print("\n", metadata)
            print(distance, "\n")


embeddings_generator = EmbeddingGenerator()
embeddings_generator.generate_embeddings()
embeddings_generator.query_collection("How do I stop tracking a file with git?")
