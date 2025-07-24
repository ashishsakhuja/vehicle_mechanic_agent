#!/usr/bin/env python3
# src/auto_mechanic_agent2/ingest_to_pinecone.py

import warnings
warnings.filterwarnings("ignore", message="Could not reliably determine page label")

import os
import sys
import time
import pickle
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings

# Filenames for persisted data
CHUNKS_FILE = "chunks.pkl"
PROGRESS_FILE = "progress.pkl"


def load_and_split(pdf_path: Path, splitter: RecursiveCharacterTextSplitter):
    pages = PyPDFLoader(str(pdf_path)).load()
    chunks = splitter.split_documents(pages)
    return pdf_path.name, chunks


def ingest_to_pinecone():
    # 1) Load credentials & init Pinecone
    load_dotenv()  # expects PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, OPENAI_API_KEY
    api_key    = os.getenv("PINECONE_API_KEY")
    env        = os.getenv("PINECONE_ENV")
    index_name = os.getenv("PINECONE_INDEX")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not (api_key and env and index_name and openai_key):
        raise ValueError(
            "Your .env must define PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, and OPENAI_API_KEY"
        )

    # Initialize Pinecone client and index object
    pc = Pinecone(api_key=api_key, environment=env)
    index = pc.Index(index_name)

    # Create index if it doesn't exist
    existing = pc.list_indexes().names()
    if index_name not in existing:
        print(f"▶️ Creating Pinecone index '{index_name}' …")
        pc.create_index(name=index_name, dimension=1536, metric="cosine")
        index = pc.Index(index_name)

    # 2) Set up paths
    base_dir      = Path(__file__).parent.resolve()
    pdf_dir       = base_dir / "knowledge" / "manuals"
    chunks_file   = base_dir / CHUNKS_FILE
    progress_file = base_dir / PROGRESS_FILE

    if not pdf_dir.exists():
        raise FileNotFoundError(f"Manuals folder not found at {pdf_dir!r}")

    # 3) Chunking phase: run once
    if not chunks_file.exists():
        pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
        print(f"Found {len(pdf_paths)} PDFs under {pdf_dir}")

        splitter    = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)
        all_chunks  = []
        start_time  = time.time()
        with ThreadPoolExecutor(max_workers=4) as exe:
            futures = {exe.submit(load_and_split, p, splitter): p for p in pdf_paths}
            for fut in as_completed(futures):
                name, chunks = fut.result()
                all_chunks.extend(chunks)
                print(f"  • {name}: {len(chunks)} chunks")
        elapsed = time.time() - start_time
        print(f"✅ Chunked {len(all_chunks)} total chunks in {elapsed:.1f}s")

        with open(chunks_file, "wb") as f:
            pickle.dump(all_chunks, f)
        print(f"🔖 Saved chunks to {CHUNKS_FILE}. Run again to embed/upsert.")
        sys.exit(0)

    # 4) Load persisted chunks
    with open(chunks_file, "rb") as f:
        all_chunks = pickle.load(f)
    print(f"🔄 Loaded {len(all_chunks)} chunks from {CHUNKS_FILE}")

    # 5) Load or initialize progress set
    if progress_file.exists():
        with open(progress_file, "rb") as f:
            processed_ids = pickle.load(f)
    else:
        processed_ids = set()

    # 6) Embed & upsert, resuming
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    batch_size = 200
    total      = len(all_chunks)

    for i in range(0, total, batch_size):
        batch = all_chunks[i : i + batch_size]
        # Generate unique IDs using source path
        proc_items = []
        for j, d in enumerate(batch):
            src = d.metadata.get('source') or d.metadata.get('path') or str(i+j)
            vid = f"{Path(src).stem}-{i+j}"
            if vid not in processed_ids:
                proc_items.append((vid, d))

        if not proc_items:
            print(f"🔄 Skipping batch {i+1}-{i+len(batch)} (already processed)")
            continue

        texts = [d.page_content for _, d in proc_items]
        metas = [d.metadata for _, d in proc_items]
        vids  = [vid for vid, _ in proc_items]

        t0 = time.time()
        vectors = embeddings.embed_documents(texts)
        print(f"    ↳ Embedded {len(vectors)} vectors in {time.time()-t0:.1f}s")

        # Upsert to Pinecone via index object
        index.upsert(vectors=list(zip(vids, vectors, metas)))
        print(f"    ↑ Upserted {len(vectors)}/{total} chunks")

        # Save progress
        processed_ids.update(vids)
        with open(progress_file, "wb") as f:
            pickle.dump(processed_ids, f)

    print(f"🎉 All done! Upserted {len(processed_ids)} unique chunks to '{index_name}'")

if __name__ == "__main__":
    ingest_to_pinecone()
