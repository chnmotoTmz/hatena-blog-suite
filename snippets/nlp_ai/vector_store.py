import os
from typing import List, Dict, Optional, Tuple, Any
from langchain.embeddings.openai import OpenAIEmbeddings # Using OpenAI for embeddings by default
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Try to import chromadb client, not strictly necessary if only using Langchain's Chroma wrapper
try:
    import chromadb
    CHROMADB_CLIENT_AVAILABLE = True
except ImportError:
    CHROMADB_CLIENT_AVAILABLE = False
    logger.info("chromadb client library not found. Langchain's Chroma wrapper will be used.")


class ChromaVectorStoreManager:
    """
    Manages a Chroma vector store for embedding and retrieving documents.
    Uses Langchain's Chroma wrapper and OpenAI embeddings by default.
    """
    DEFAULT_CHROMA_PERSIST_DIR = "./chroma_db_store"
    DEFAULT_COLLECTION_NAME = "langchain" # Default collection name used by Langchain's Chroma

    def __init__(
        self,
        openai_api_key: str,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_function: Optional[Any] = None, # Allow custom embedding functions
        text_splitter_chunk_size: int = 1000,
        text_splitter_chunk_overlap: int = 200,
    ):
        """
        Initializes the ChromaVectorStoreManager.

        Args:
            openai_api_key: OpenAI API key, required for default OpenAIEmbeddings.
            persist_directory: Directory to persist the Chroma database.
                               Defaults to DEFAULT_CHROMA_PERSIST_DIR.
            collection_name: Name of the collection within Chroma.
                             Defaults to DEFAULT_COLLECTION_NAME.
            embedding_function: Optional Langchain-compatible embedding function.
                                If None, OpenAIEmbeddings will be used.
            text_splitter_chunk_size: Chunk size for the text splitter.
            text_splitter_chunk_overlap: Chunk overlap for the text splitter.
        """
        if not openai_api_key and not embedding_function:
            raise ValueError("Either openai_api_key (for default embeddings) or a custom embedding_function must be provided.")

        self.persist_directory = persist_directory or self.DEFAULT_CHROMA_PERSIST_DIR
        self.collection_name = collection_name or self.DEFAULT_COLLECTION_NAME

        if embedding_function:
            self.embedding_function = embedding_function
        else:
            self.embedding_function = OpenAIEmbeddings(openai_api_key=openai_api_key)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=text_splitter_chunk_size,
            chunk_overlap=text_splitter_chunk_overlap,
            length_function=len
        )
        self.vector_store: Optional[Chroma] = None
        self._ensure_persist_directory()

    def _ensure_persist_directory(self):
        if not os.path.exists(self.persist_directory):
            try:
                os.makedirs(self.persist_directory)
                logger.info(f"Created Chroma persist directory: {self.persist_directory}")
            except OSError as e:
                logger.error(f"Failed to create persist directory {self.persist_directory}: {e}")
                # Decide on error handling: raise error or log and continue?
                # For now, log and continue, operations will likely fail later.

    def _articles_to_langchain_documents(self, articles: List[Dict[str, Any]]) -> List[LangchainDocument]:
        """Converts a list of article dictionaries to Langchain Document objects."""
        langchain_docs = []
        for i, article in enumerate(articles):
            content = article.get('content', '') or article.get('text', '') # Prefer 'content'
            if not content:
                logger.warning(f"Article {article.get('id', i)} has no content, skipping.")
                continue

            metadata = article.get('metadata', {})
            # Ensure some common fields are in metadata if present at top level of article dict
            for key in ['title', 'url', 'date', 'source', 'id', 'article_id', 'categories']:
                if key in article and key not in metadata:
                    metadata[key] = article[key]

            doc = LangchainDocument(page_content=content, metadata=metadata)
            langchain_docs.append(doc)
        return langchain_docs

    def add_articles(self, articles: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """
        Adds articles to the Chroma vector store. Articles are converted to
        Langchain Documents, split into chunks, and then embedded.

        Args:
            articles: A list of dictionaries, where each dictionary represents an article.
                      Each article dict should have a 'content' or 'text' field,
                      and optionally a 'metadata' field. Other top-level keys will be
                      added to metadata if not already present.
            batch_size: Number of documents to add in a single batch (if applicable to underlying client).

        Returns:
            True if articles were added successfully, False otherwise.
        """
        if not articles:
            logger.warning("No articles provided to add to vector store.")
            return False

        langchain_documents = self._articles_to_langchain_documents(articles)
        if not langchain_documents:
            logger.warning("No valid Langchain documents could be created from the articles.")
            return False

        split_documents = self.text_splitter.split_documents(langchain_documents)
        if not split_documents:
            logger.warning("Text splitting resulted in no documents.")
            return False

        logger.info(f"Adding {len(split_documents)} document chunks from {len(articles)} articles to Chroma.")

        try:
            if self.vector_store is None: # Initialize if not already loaded/created
                 # This will create or load the store.
                logger.info(f"Initializing Chroma vector store at {self.persist_directory} with collection {self.collection_name}")
                self.vector_store = Chroma.from_documents(
                    documents=split_documents,
                    embedding=self.embedding_function,
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name
                    # ids=[doc.metadata.get("id", f"chunk_{i}") for i, doc in enumerate(split_documents)] # Optional: provide custom IDs
                )
                self.vector_store.persist() # Ensure persistence after initial creation
            else: # Add to existing store
                # Langchain's Chroma `add_documents` handles batching internally to some extent.
                # The `batch_size` arg here is more for conceptual chunking if we were to loop.
                self.vector_store.add_documents(split_documents)
                self.vector_store.persist() # Persist after adding new documents

            logger.info(f"Successfully added {len(split_documents)} chunks to Chroma. Collection size: {self.get_collection_count()}")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to Chroma: {e}", exc_info=True)
            return False

    def load_store(self) -> bool:
        """
        Loads an existing Chroma vector store from the persist_directory.

        Returns:
            True if the store was loaded successfully, False otherwise.
        """
        if not os.path.exists(self.persist_directory) or not os.listdir(self.persist_directory): # Check if dir is empty
            logger.warning(f"Persist directory {self.persist_directory} does not exist or is empty. Cannot load store.")
            return False
        try:
            logger.info(f"Loading Chroma vector store from {self.persist_directory}, collection: {self.collection_name}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
                collection_name=self.collection_name
            )
            logger.info(f"Successfully loaded Chroma. Collection items: {self.get_collection_count()}")
            return True
        except Exception as e: # Chroma can raise various errors if DB is corrupt or misconfigured
            logger.error(f"Error loading Chroma vector store: {e}", exc_info=True)
            self.vector_store = None
            return False

    def similarity_search(self, query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[LangchainDocument, float]]:
        """
        Performs a similarity search in the vector store.

        Args:
            query: The query string.
            k: The number of top similar documents to retrieve.
            filter_metadata: Optional dictionary to filter results based on metadata.
                             Example: {"source": "blog_A"}

        Returns:
            A list of tuples, each containing a LangchainDocument and its similarity score.
            Returns empty list if store not loaded or search fails.
        """
        if self.vector_store is None:
            logger.warning("Vector store not loaded. Cannot perform similarity search.")
            if not self.load_store(): # Attempt to load if not already
                 return []


        if not query:
            logger.warning("Similarity search query is empty.")
            return []

        try:
            # Langchain's Chroma retriever uses `similarity_search_with_score`
            # The filter argument in Chroma's similarity_search is `where`
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                where=filter_metadata # Langchain Chroma uses 'where' for filtering
            )
            logger.info(f"Similarity search for '{query[:50]}...' returned {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {e}", exc_info=True)
            return []

    def get_collection_count(self) -> Optional[int]:
        """Returns the number of items in the collection, if the store is loaded."""
        if self.vector_store and self.vector_store._collection:
            try:
                return self.vector_store._collection.count()
            except Exception as e:
                logger.error(f"Error getting collection count: {e}")
                return None
        # Try to load if not available
        elif not self.vector_store and self.load_store() and self.vector_store and self.vector_store._collection:
             try:
                return self.vector_store._collection.count()
             except Exception as e:
                logger.error(f"Error getting collection count after loading: {e}")
                return None
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # IMPORTANT: Requires OPENAI_API_KEY environment variable to be set for default embeddings.
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("OPENAI_API_KEY environment variable not set. Tests requiring embeddings will be skipped.")
    else:
        print("--- Testing ChromaVectorStoreManager ---")

        # Define a temporary persist directory for testing
        test_persist_dir = "./test_chroma_store"
        test_collection_name = "test_collection"

        # Clean up previous test directory if it exists
        import shutil
        if os.path.exists(test_persist_dir):
            shutil.rmtree(test_persist_dir)

        manager = ChromaVectorStoreManager(
            openai_api_key=openai_key,
            persist_directory=test_persist_dir,
            collection_name=test_collection_name
        )

        sample_articles_data = [
            {'id': 'doc1', 'content': "Python is a great language for data science.", 'metadata': {'source': 'blog_A', 'year': 2023}},
            {'id': 'doc2', 'content': "Langchain helps build LLM-powered applications.", 'metadata': {'source': 'blog_B', 'year': 2023}},
            {'id': 'doc3', 'content': "Vector stores like Chroma are useful for semantic search.", 'metadata': {'source': 'blog_A', 'year': 2024}},
            {'id': 'doc4', 'content': "Understanding Python data structures is key for efficiency.", 'metadata': {'source': 'blog_C', 'year': 2024}},
        ]

        print("\\n--- Test 1: Add Articles ---")
        success_add = manager.add_articles(sample_articles_data)
        print(f"Adding articles successful: {success_add}")
        assert success_add
        assert manager.get_collection_count() is not None and manager.get_collection_count() > 0

        current_count = manager.get_collection_count()
        print(f"Items in collection after adding: {current_count}")


        print("\\n--- Test 2: Similarity Search ---")
        query1 = "data science with Python"
        results1 = manager.similarity_search(query1, k=2)
        print(f"Search results for '{query1}':")
        for doc, score in results1:
            print(f"  - Score: {score:.4f}, Content: '{doc.page_content[:50]}...', Metadata: {doc.metadata}")
        assert len(results1) > 0
        if results1:
             assert "Python" in results1[0][0].page_content or "data science" in results1[0][0].page_content


        print("\\n--- Test 3: Similarity Search with Metadata Filter ---")
        query2 = "Python applications"
        results2 = manager.similarity_search(query2, k=2, filter_metadata={'source': 'blog_A'})
        print(f"Search results for '{query2}' (source=blog_A):")
        for doc, score in results2:
            print(f"  - Score: {score:.4f}, Content: '{doc.page_content[:50]}...', Metadata: {doc.metadata}")
            assert doc.metadata.get('source') == 'blog_A'
        # Depending on chunking, doc1 and doc3 (both from blog_A) might be relevant.

        # Test loading from persisted directory
        print("\\n--- Test 4: Load Store from Disk ---")
        manager_loaded = ChromaVectorStoreManager(
            openai_api_key=openai_key,
            persist_directory=test_persist_dir,
            collection_name=test_collection_name
        )
        load_success = manager_loaded.load_store()
        print(f"Loading from disk successful: {load_success}")
        assert load_success
        assert manager_loaded.get_collection_count() == current_count # Should be same as before

        query3 = "Chroma vector database"
        results3 = manager_loaded.similarity_search(query3, k=1)
        print(f"Search results for '{query3}' after loading:")
        for doc, score in results3:
            print(f"  - Score: {score:.4f}, Content: '{doc.page_content[:50]}...', Metadata: {doc.metadata}")
        assert len(results3) > 0
        if results3:
            assert "Chroma" in results3[0][0].page_content

        # Clean up test directory
        if os.path.exists(test_persist_dir):
            shutil.rmtree(test_persist_dir)
        print(f"Cleaned up test directory: {test_persist_dir}")

        print("\\nChromaVectorStoreManager tests finished.")
