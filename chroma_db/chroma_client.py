from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
from pathlib import Path
from langchain.tools import tool
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def chunk_markdown(markdown_path):
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    md_docs = markdown_splitter.split_text(markdown_text)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        add_start_index=True,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )
    final_docs = text_splitter.split_documents(md_docs)
    return final_docs


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = Chroma(
    collection_name="knowledge_base",
    embedding_function=embeddings,
    persist_directory="./chroma_data",
)


def upload_chromadb():
    BASE_DIR = Path(__file__).parent.parent
    final_docs = chunk_markdown(BASE_DIR / "RAG_Document.md")
    ids = [f"rag_doc_{i}" for i in range(len(final_docs))]
    vector_store.add_documents(
        documents=final_docs,
        ids=ids,
    )


@tool
def search_knowledge_base(query: str) -> str:
    """Search the student knowledge base to query about student program knowledge."""
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )
    docs = retriever.invoke(query)
    return "\n\n".join(doc.page_content for doc in docs)


if __name__ == "__main__":
    upload_chromadb()
