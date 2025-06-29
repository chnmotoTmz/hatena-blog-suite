import re
from typing import List, Optional

# Attempt to import MeCab
try:
    import MeCab
    MECAB_AVAILABLE = True
except ImportError:
    MECAB_AVAILABLE = False
    print("Warning: MeCab is not installed or not found. Keyword extraction will use a simple fallback.")

class KeywordExtractor:
    """
    Extracts keywords from text, preferring MeCab if available,
    otherwise using a simple regex-based fallback.
    """
    def __init__(self, mecab_tagger_args: str = ""):
        """
        Initializes the KeywordExtractor.

        Args:
            mecab_tagger_args: Arguments to pass to the MeCab.Tagger constructor
                               (e.g., "-Ochasen", "-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd").
                               Only used if MeCab is available.
        """
        self.mecab_tagger = None
        if MECAB_AVAILABLE:
            try:
                self.mecab_tagger = MeCab.Tagger(mecab_tagger_args)
            except RuntimeError as e:
                print(f"Error initializing MeCab.Tagger with args '{mecab_tagger_args}': {e}")
                print("Falling back to default MeCab Tagger or simple extraction if that also fails.")
                try:
                    self.mecab_tagger = MeCab.Tagger() # Try with default args
                except RuntimeError as e_default:
                    print(f"Error initializing default MeCab.Tagger: {e_default}. MeCab will not be used.")
                    self.mecab_tagger = None # Ensure it's None if initialization fails

        if not self.mecab_tagger and MECAB_AVAILABLE: # If MeCab was imported but Tagger failed
            print("MeCab was imported, but Tagger could not be initialized. Using fallback.")


    def extract_keywords(self, text: str, min_word_length: int = 2, use_mecab_if_available: bool = True) -> List[str]:
        """
        Extracts keywords from the given text.

        Uses MeCab if available and `use_mecab_if_available` is True.
        Otherwise, uses a simple regex-based extraction.

        Args:
            text: The input text string.
            min_word_length: Minimum length for a word to be considered a keyword (for fallback).
            use_mecab_if_available: If True, tries to use MeCab. If False, forces fallback.

        Returns:
            A list of unique keywords.
        """
        if not text:
            return []

        if use_mecab_if_available and self.mecab_tagger:
            return self._extract_keywords_mecab(text)
        else:
            return self._extract_keywords_fallback(text, min_word_length)

    def _extract_keywords_mecab(self, text: str) -> List[str]:
        """
        Extracts keywords using MeCab (nouns, adjectives, verbs - base form).
        """
        keywords = set()
        if not self.mecab_tagger: # Should not happen if called from extract_keywords logic
             return self._extract_keywords_fallback(text, 2)

        try:
            # Ensure text is valid for MeCab (e.g. not None, not bytes)
            if not isinstance(text, str):
                 text = str(text)

            node = self.mecab_tagger.parseToNode(text)
            while node:
                # feature is a CSV string: 品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用形,活用型,原形,読み,発音
                features = node.feature.split(',')
                word_surface = node.surface

                if not word_surface: # Skip empty surface tokens
                    node = node.next
                    continue

                # Extract Nouns (名詞), Adjectives (形容詞), Verbs (動詞 - base form)
                # Consider also Proper Nouns (名詞-固有名詞)
                pos = features[0] # 品詞 (Part of Speech)

                if pos in ['名詞', '形容詞', '動詞']:
                    base_form = features[6] if len(features) > 6 and features[6] != '*' else word_surface

                    # Filter criteria
                    # - Not a number (MeCab might classify numbers as nouns)
                    # - Not a single character (unless it's a relevant Kanji/symbol, harder to define generally)
                    # - Not a stop word (more advanced, requires a stop word list)
                    if not base_form.isnumeric() and len(base_form) > 1 :
                         # For verbs and adjectives, prefer base form. For nouns, surface form might be better.
                         # Here, we'll use base_form for all selected POS for simplicity.
                        keywords.add(base_form)

                node = node.next
            return list(keywords)
        except Exception as e:
            print(f"Error during MeCab parsing: {e}. Falling back to simple extraction.")
            return self._extract_keywords_fallback(text, 2)


    def _extract_keywords_fallback(self, text: str, min_word_length: int = 2) -> List[str]:
        """
        A simple regex-based keyword extraction fallback.
        Extracts sequences of Japanese characters (Hiragana, Katakana, Kanji) and alphanumeric words.
        """
        # Regex for Japanese words (Kanji, Hiragana, Katakana) and English words
        # Japanese part: [\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+
        # English/Alphanumeric part: [a-zA-Z0-9]+
        pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+|[a-zA-Z0-9]+')
        words = pattern.findall(text)

        # Filter by length and uniqueness
        keywords = list(set(word.lower() for word in words if len(word) >= min_word_length))
        return keywords

if __name__ == '__main__':
    print(f"--- Testing KeywordExtractor (MeCab available: {MECAB_AVAILABLE}) ---")

    extractor_default = KeywordExtractor() # Default MeCab args
    # extractor_neologd = KeywordExtractor(mecab_tagger_args="-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd") # Example for NEologd

    sample_text_jp = "これはMeCabとPythonを使った日本語のキーワード抽出テストです。東京タワーや京都の観光地、美味しいラーメンについても話しています。"
    sample_text_en = "This is a test for keyword extraction using Python, with some technical terms like API and SDK."
    sample_text_mixed = "Pythonistaなら知っておきたい、機械学習（Machine Learning）と深層学習（Deep Learning）の基礎。API連携も重要。"

    print(f"\\n--- Extracting from Japanese text ---")
    keywords_jp = extractor_default.extract_keywords(sample_text_jp)
    print(f"Keywords (MeCab or fallback): {keywords_jp}")

    print(f"\\n--- Extracting from English text (MeCab might not be ideal, fallback is better) ---")
    keywords_en_mecab_preferred = extractor_default.extract_keywords(sample_text_en, use_mecab_if_available=True)
    print(f"Keywords (MeCab preferred): {keywords_en_mecab_preferred}")
    keywords_en_fallback = extractor_default.extract_keywords(sample_text_en, use_mecab_if_available=False)
    print(f"Keywords (Fallback forced): {keywords_en_fallback}")


    print(f"\\n--- Extracting from mixed Japanese/English text ---")
    keywords_mixed = extractor_default.extract_keywords(sample_text_mixed)
    print(f"Keywords (MeCab or fallback): {keywords_mixed}")

    print(f"\\n--- Forcing fallback for Japanese text ---")
    keywords_jp_fallback = extractor_default.extract_keywords(sample_text_jp, use_mecab_if_available=False, min_word_length=3)
    print(f"Keywords (Fallback forced, min_length=3): {keywords_jp_fallback}")

    print(f"\\n--- Test with empty string ---")
    keywords_empty = extractor_default.extract_keywords("")
    print(f"Keywords from empty string: {keywords_empty}")

    if MECAB_AVAILABLE and extractor_default.mecab_tagger:
        print("\\nMeCab specific tests:")
        print("POS extracted by MeCab (nouns, adjectives, verbs - base form):")
        # Example of how _extract_keywords_mecab processes
        test_sentence_for_mecab = "美しい花が咲いた。速く走る。"
        mecab_extracted = extractor_default._extract_keywords_mecab(test_sentence_for_mecab)
        print(f"MeCab extracted from '{test_sentence_for_mecab}': {mecab_extracted}")
    elif MECAB_AVAILABLE and not extractor_default.mecab_tagger:
        print("\\nMeCab was imported, but Tagger could not be initialized. All tests used fallback.")
    else:
        print("\\nMeCab not available. All tests used fallback method.")

    print("\\nKeywordExtractor tests finished.")
