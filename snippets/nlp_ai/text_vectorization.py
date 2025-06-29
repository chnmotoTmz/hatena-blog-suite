from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Optional, Any
import numpy as np
import scipy.sparse

class TextVectorizer:
    """
    Handles text vectorization using TF-IDF and computes cosine similarities.
    """
    def __init__(self, max_features: Optional[int] = 1000, ngram_range: Tuple[int, int] = (1, 2), **tfidf_kwargs):
        """
        Initializes the TextVectorizer with a TfidfVectorizer.

        Args:
            max_features: Maximum number of features (terms) to consider.
            ngram_range: The lower and upper boundary of the range of n-values for different
                         n-grams to be extracted. E.g., (1, 1) means only unigrams,
                         (1, 2) means unigrams and bigrams.
            **tfidf_kwargs: Additional keyword arguments to pass to TfidfVectorizer
                            (e.g., stop_words, min_df, max_df).
        """
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            **tfidf_kwargs
        )
        self.tfidf_matrix: Optional[scipy.sparse.csr_matrix] = None
        self.fitted_texts_count: int = 0

    def fit_transform_texts(self, texts: List[str]) -> Optional[scipy.sparse.csr_matrix]:
        """
        Fits the TF-IDF vectorizer to the given texts and transforms them into a TF-IDF matrix.

        Args:
            texts: A list of text documents.

        Returns:
            A sparse matrix of TF-IDF features, or None if input is empty or an error occurs.
        """
        if not texts:
            print("Warning: No texts provided for TF-IDF fitting and transformation.")
            return None
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.fitted_texts_count = len(texts)
            print(f"TF-IDF matrix created with shape: {self.tfidf_matrix.shape}")
            return self.tfidf_matrix
        except Exception as e:
            print(f"Error during TF-IDF fit_transform: {e}")
            self.tfidf_matrix = None
            self.fitted_texts_count = 0
            return None

    def transform_texts(self, texts: List[str]) -> Optional[scipy.sparse.csr_matrix]:
        """
        Transforms new texts into a TF-IDF matrix using the already fitted vectorizer.

        Args:
            texts: A list of new text documents.

        Returns:
            A sparse matrix of TF-IDF features, or None if vectorizer not fitted or error.
        """
        if not self.vectorizer.vocabulary_:
            print("Error: TF-IDF vectorizer has not been fitted yet. Call fit_transform_texts first.")
            return None
        if not texts:
            print("Warning: No texts provided for TF-IDF transformation.")
            return None
        try:
            return self.vectorizer.transform(texts)
        except Exception as e:
            print(f"Error during TF-IDF transform: {e}")
            return None

    def get_feature_names(self) -> Optional[List[str]]:
        """Returns the list of feature names (terms) learned by the vectorizer."""
        if not self.vectorizer.vocabulary_:
            print("Warning: Vectorizer not fitted. No feature names available.")
            return None
        try:
            return self.vectorizer.get_feature_names_out()
        except Exception as e:
            print(f"Error getting feature names: {e}")
            return None


    def calculate_cosine_similarity_matrix(
        self,
        matrix1: Optional[scipy.sparse.csr_matrix] = None,
        matrix2: Optional[scipy.sparse.csr_matrix] = None
    ) -> Optional[np.ndarray]:
        """
        Calculates the cosine similarity matrix.
        - If only matrix1 is provided, calculates similarity within matrix1 (e.g., document similarity).
        - If both matrix1 and matrix2 are provided, calculates similarity between rows of matrix1 and matrix2.
        - If no matrices are provided, uses the internally stored self.tfidf_matrix for self-similarity.

        Args:
            matrix1: A TF-IDF matrix. If None, uses self.tfidf_matrix.
            matrix2: An optional second TF-IDF matrix.

        Returns:
            A NumPy array representing the cosine similarity matrix, or None if an error occurs.
        """
        target_matrix1 = matrix1 if matrix1 is not None else self.tfidf_matrix

        if target_matrix1 is None:
            print("Error: No TF-IDF matrix available for similarity calculation. "
                  "Fit/transform texts or provide a matrix.")
            return None

        try:
            if matrix2 is None:
                # Calculate similarity within target_matrix1
                similarity_matrix = cosine_similarity(target_matrix1)
            else:
                # Calculate similarity between target_matrix1 and matrix2
                similarity_matrix = cosine_similarity(target_matrix1, matrix2)
            return similarity_matrix
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return None

    def get_similarity_for_text(self, new_text: str, top_n: Optional[int] = None) -> Optional[List[Tuple[int, float]]]:
        """
        Calculates cosine similarity of a new text against the fitted documents.

        Args:
            new_text: The new text string.
            top_n: If provided, returns the top N most similar document indices and their scores.

        Returns:
            A list of (document_index, similarity_score) tuples, sorted by similarity,
            or None if an error occurs.
        """
        if self.tfidf_matrix is None or not self.vectorizer.vocabulary_:
            print("Error: Vectorizer not fitted or no internal TF-IDF matrix. "
                  "Call fit_transform_texts first.")
            return None

        new_text_vector = self.transform_texts([new_text])
        if new_text_vector is None:
            return None

        similarities = self.calculate_cosine_similarity_matrix(new_text_vector, self.tfidf_matrix)
        if similarities is None:
            return None

        # similarities is a 1xN matrix, so get the first row
        scores = similarities[0]

        # Create (index, score) pairs
        indexed_scores = list(enumerate(scores))

        # Sort by score in descending order
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        if top_n is not None:
            return indexed_scores[:top_n]
        return indexed_scores


if __name__ == '__main__':
    print("--- Testing TextVectorizer ---")

    documents = [
        "This is the first document about Python programming.",
        "Python is a versatile and popular programming language.",
        "The second document discusses data science with Python.",
        "Java is another programming language, different from Python.",
        "Natural Language Processing (NLP) can be done using Python libraries."
    ]

    # Initialize vectorizer
    # Using English stop words for this example
    vectorizer_eng = TextVectorizer(stop_words='english', max_features=50)

    # Test 1: Fit and transform
    print("\\n--- Test 1: Fit and Transform ---")
    tfidf_matrix = vectorizer_eng.fit_transform_texts(documents)
    if tfidf_matrix is not None:
        print(f"TF-IDF Matrix shape: {tfidf_matrix.shape}")
        # print(f"Matrix content (first 2 docs):\n{tfidf_matrix[:2].toarray()}")

        features = vectorizer_eng.get_feature_names()
        if features:
            print(f"First 10 Features: {features[:10]}")

    # Test 2: Calculate self-similarity matrix
    print("\\n--- Test 2: Calculate Self-Similarity Matrix ---")
    if tfidf_matrix is not None:
        similarity_matrix = vectorizer_eng.calculate_cosine_similarity_matrix()
        if similarity_matrix is not None:
            print(f"Similarity Matrix shape: {similarity_matrix.shape}")
            print("Pairwise similarities (rounded):")
            for i in range(len(documents)):
                row_sim = [f"{s:.2f}" for s in similarity_matrix[i]]
                print(f"  Doc {i+1} vs all: {row_sim}")
            # Document 0 and 1 should be similar, 0 and 3 less so.
            assert similarity_matrix[0, 1] > similarity_matrix[0, 3]

    # Test 3: Transform new text and get similarity
    print("\\n--- Test 3: Similarity for a New Text ---")
    new_doc = "Exploring Python for advanced data analysis and machine learning."
    if tfidf_matrix is not None: # Ensures vectorizer is fitted
        similar_docs = vectorizer_eng.get_similarity_for_text(new_doc, top_n=3)
        if similar_docs:
            print(f"Top 3 documents similar to '{new_doc}':")
            for idx, score in similar_docs:
                print(f"  - Doc {idx+1} ('{documents[idx][:30]}...'): Score {score:.4f}")

    # Test 4: Japanese text (requires appropriate tokenizer/stop words if MeCab isn't integrated here)
    print("\\n--- Test 4: Japanese Text (simple, no specific JP stop words) ---")
    jp_documents = [
        "これは最初の日本語ドキュメントです。プログラミングについてです。",
        "Pythonは多目的で人気のあるプログラミング言語です。",
        "二番目のドキュメントは、Pythonを使ったデータサイエンスについて議論します。",
        "自然言語処理（NLP）はPythonライブラリを使用して行うことができます。"
    ]
    # For Japanese, it's better to not use English stop words and potentially use a Japanese tokenizer
    # or set ngram_range appropriately if using character n-grams.
    # Here, we'll just run it without stop_words.
    vectorizer_jp = TextVectorizer(ngram_range=(1,3)) # Try char n-grams for Japanese without MeCab

    tfidf_matrix_jp = vectorizer_jp.fit_transform_texts(jp_documents)
    if tfidf_matrix_jp is not None:
        print(f"JP TF-IDF Matrix shape: {tfidf_matrix_jp.shape}")
        jp_features = vectorizer_jp.get_feature_names()
        if jp_features:
             print(f"First 10 JP Features (may be char n-grams): {jp_features[:10]}")

        new_jp_doc = "Pythonでの自然言語処理は非常に便利です。"
        similar_jp_docs = vectorizer_jp.get_similarity_for_text(new_jp_doc, top_n=2)
        if similar_jp_docs:
            print(f"Top 2 JP documents similar to '{new_jp_doc}':")
            for idx, score in similar_jp_docs:
                print(f"  - Doc {idx+1} ('{jp_documents[idx][:20]}...'): Score {score:.4f}")

    print("\\n--- Test 5: Error handling ---")
    empty_vectorizer = TextVectorizer()
    print(f"Transform without fit: {empty_vectorizer.transform_texts(['test'])}")
    print(f"Similarity without fit: {empty_vectorizer.calculate_cosine_similarity_matrix()}")
    print(f"Similarity for text without fit: {empty_vectorizer.get_similarity_for_text('new text')}")
    print(f"Fit with empty list: {empty_vectorizer.fit_transform_texts([])}")


    print("\\nTextVectorizer tests finished.")
