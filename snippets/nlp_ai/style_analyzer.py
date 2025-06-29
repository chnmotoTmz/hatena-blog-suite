import re
from collections import Counter
from typing import List, Dict, Any, Tuple

class BasicStyleAnalyzer:
    """
    Analyzes basic stylistic features of Japanese text.
    This analyzer provides a simplified approach and does not use advanced NLP models.
    """

    # Common Japanese sentence endings (examples)
    # More can be added or refined.
    SENTENCE_ENDINGS_PATTERNS = {
        "polite_formal": [r"です。", r"ます。", r"ました。", r"でしょう。", r"ございます。"],
        "plain_formal": [r"である。", r"であった。", r"だろう。", r"であるだろう。"],
        "polite_informal": [r"ですよ。", r"ますよ。", r"ですね。", r"ますね。", r"でしょうね。"],
        "plain_informal": [r"だ。", r"だった。", r"だろう。", r"じゃん。", r"かな。"],
        "question": [r"か。", r"ですか。", r"でしょうか。", r"の？", r"かい？"],
        "exclamation": [r"！", r"!!"] # Basic exclamation check
    }

    # Common Japanese conjunctive phrases (examples)
    CONJUNCTIVE_PHRASES = [
        "そして", "しかし", "だが", "また", "さらに", "ところで", "さて",
        "そのため", "したがって", "なので", "だから", "なぜなら",
        "例えば", "具体的には", "つまり", "要するに",
        "まず", "次に", "最後に",
        "ちなみに", "なお", "ただし"
    ]

    def __init__(self):
        pass

    def analyze_texts(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyzes a list of text strings and returns a dictionary of stylistic features.

        Args:
            texts: A list of Japanese text strings to analyze.

        Returns:
            A dictionary containing various stylistic metrics.
        """
        if not texts:
            return {"error": "No texts provided for analysis."}

        combined_text = "\n".join(texts)
        if not combined_text.strip():
            return {"error": "Provided texts are empty or whitespace only."}

        num_sentences, avg_sentence_length = self._analyze_sentence_structure(combined_text)
        num_paragraphs, avg_paragraph_length_chars, avg_paragraph_length_sents = self._analyze_paragraph_structure(combined_text, num_sentences)

        analysis_results = {
            "overall_metrics": {
                "total_characters": len(combined_text),
                "total_words_approx": len(re.findall(r'\S+', combined_text)), # Very rough word count
                "num_texts_analyzed": len(texts),
            },
            "sentence_metrics": {
                "num_sentences": num_sentences,
                "avg_sentence_length_chars": avg_sentence_length,
                "sentence_ending_patterns": self._analyze_sentence_endings(combined_text),
            },
            "paragraph_metrics": {
                "num_paragraphs": num_paragraphs,
                "avg_paragraph_length_chars": avg_paragraph_length_chars,
                "avg_paragraph_length_sentences": avg_paragraph_length_sents,
            },
            "vocabulary_metrics": {
                "char_type_ratios": self._analyze_character_types(combined_text),
                "common_conjunctive_phrases": self._analyze_conjunctive_phrases(combined_text),
            },
            "punctuation_metrics": {
                "punctuation_counts": self._analyze_punctuation(combined_text),
            }
        }
        return analysis_results

    def _analyze_sentence_structure(self, text: str) -> Tuple[int, float]:
        """Analyzes sentence count and average length."""
        # Split by common Japanese sentence enders: 。！？ and their full-width versions
        sentences = re.split(r'[。！？｡!?]', text)
        # Filter out empty strings that may result from splitting
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        num_sentences = len(valid_sentences)

        if num_sentences == 0:
            return 0, 0.0

        total_sentence_length_chars = sum(len(s) for s in valid_sentences)
        avg_sentence_length = total_sentence_length_chars / num_sentences if num_sentences > 0 else 0
        return num_sentences, avg_sentence_length

    def _analyze_paragraph_structure(self, text: str, total_sentences_in_text: int) -> Tuple[int, float, float]:
        """Analyzes paragraph count and average length (in chars and sentences)."""
        # Paragraphs are typically separated by one or more newlines
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        num_paragraphs = len(paragraphs)

        if num_paragraphs == 0:
            return 0, 0.0, 0.0

        total_paragraph_length_chars = sum(len(p) for p in paragraphs)
        avg_paragraph_length_chars = total_paragraph_length_chars / num_paragraphs if num_paragraphs > 0 else 0
        avg_paragraph_length_sents = total_sentences_in_text / num_paragraphs if num_paragraphs > 0 else 0

        return num_paragraphs, avg_paragraph_length_chars, avg_paragraph_length_sents


    def _analyze_sentence_endings(self, text: str) -> Dict[str, int]:
        """Counts occurrences of predefined sentence ending patterns."""
        ending_counts: Dict[str, int] = Counter()
        for category, patterns in self.SENTENCE_ENDINGS_PATTERNS.items():
            for pattern in patterns:
                # This is a simple count of regex matches, might not be perfectly accurate for true "endings"
                # as it doesn't ensure the pattern is at the very end of a sentence segment.
                # For more accuracy, one would need to analyze actual sentence segments.
                matches = re.findall(pattern, text)
                if matches:
                    ending_counts[category] += len(matches)
        return dict(ending_counts)

    def _analyze_character_types(self, text: str) -> Dict[str, float]:
        """Calculates ratios of Hiragana, Katakana, Kanji, AlphaNumeric, and Symbols."""
        counts = {
            "hiragana": 0, "katakana": 0, "kanji": 0,
            "alphanumeric": 0, "symbols_punctuation": 0, "whitespace": 0, "other":0
        }
        total_chars = len(text)
        if total_chars == 0:
            return {key: 0.0 for key in counts}

        for char_val in text:
            # Hiragana: U+3040 - U+309F
            if '\u3040' <= char_val <= '\u309F':
                counts["hiragana"] += 1
            # Katakana: U+30A0 - U+30FF
            elif '\u30A0' <= char_val <= '\u30FF':
                counts["katakana"] += 1
            # CJK Unified Ideographs (Common Kanji): U+4E00 - U+9FFF
            elif '\u4E00' <= char_val <= '\u9FFF':
                counts["kanji"] += 1
            # Alphanumeric
            elif char_val.isalnum(): # Covers English alphabet and numbers
                counts["alphanumeric"] += 1
            # Whitespace
            elif char_val.isspace():
                counts["whitespace"] +=1
            # Basic Punctuation (more can be added)
            # Japanese specific: 、。・「」『』（）？！％＃＆＊＠
            # General: , . ; : ' " ( ) ! ? % # & * @ - _ + = / \ | < > [ ] { } ~ ` ^
            elif char_val in "、。・「」『』（）？！％＃＆＊＠,.';:\"()!?%#&*@-_+=/\\|<>[]{}~`^":
                 counts["symbols_punctuation"] += 1
            else:
                counts["other"] += 1

        ratios = {key: (count / total_chars) if total_chars > 0 else 0.0 for key, count in counts.items()}
        return ratios

    def _analyze_conjunctive_phrases(self, text: str) -> Dict[str, int]:
        """Counts occurrences of common conjunctive phrases."""
        phrase_counts: Dict[str, int] = Counter()
        for phrase in self.CONJUNCTIVE_PHRASES:
            # Using word boundaries for more accurate phrase matching
            # For Japanese, \b might not work as expected. Using non-greedy match around phrase.
            # Simple string count is used here for broader matching.
            count = text.count(phrase)
            if count > 0:
                phrase_counts[phrase] = count
        return dict(phrase_counts)

    def _analyze_punctuation(self, text: str) -> Dict[str, int]:
        """Counts common punctuation marks."""
        punctuation_marks = {
            "comma_jp": "、", "period_jp": "。", "middle_dot_jp": "・",
            "open_quote_jp": "「", "close_quote_jp": "」",
            "open_bracket_jp": "（", "close_bracket_jp": "）",
            "question_mark_jp": "？", "exclamation_mark_jp": "！",
            "comma_en": ",", "period_en": ".", "question_mark_en": "?", "exclamation_mark_en": "!"
        }
        counts: Dict[str, int] = Counter()
        for name, mark in punctuation_marks.items():
            counts[name] = text.count(mark)
        return dict(counts)


if __name__ == '__main__':
    analyzer = BasicStyleAnalyzer()

    sample_texts_jp = [
        "こんにちは、皆さん！今日は良い天気ですね。お出かけしましょうか？",
        "昨日は雨でしたが、本日は晴天なり。だから、洗濯物がよく乾きます。",
        "このシステムは非常に複雑である。しかし、理解すれば便利だ。例えば、API連携も可能である。",
        "えーっと、つまり何が言いたいかというと、まあ、そういうことなんだよね。うんうん。"
    ]

    print("--- Analyzing Japanese Sample Texts ---")
    analysis1 = analyzer.analyze_texts(sample_texts_jp)

    if "error" not in analysis1:
        print(f"Overall Metrics: {analysis1['overall_metrics']}")
        print(f"Sentence Metrics: {analysis1['sentence_metrics']}")
        print(f"Paragraph Metrics: {analysis1['paragraph_metrics']}")
        print(f"Vocabulary Metrics (Char Types): {analysis1['vocabulary_metrics']['char_type_ratios']}")
        print(f"Vocabulary Metrics (Conjunctions): {analysis1['vocabulary_metrics']['common_conjunctive_phrases']}")
        print(f"Punctuation Metrics: {analysis1['punctuation_metrics']}")
    else:
        print(f"Analysis Error: {analysis1['error']}")

    sample_text_single = """
吾輩は猫である。名前はまだ無い。
どこで生れたかとんと見当がつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
吾輩はここで始めて人間というものを見た。
"""
    print("\\n--- Analyzing Single Japanese Text (Natsume Soseki snippet) ---")
    analysis2 = analyzer.analyze_texts([sample_text_single])
    if "error" not in analysis2:
        # print(json.dumps(analysis2, indent=2, ensure_ascii=False)) # Pretty print
        print(f"Overall: Chars={analysis2['overall_metrics']['total_characters']}, Sentences={analysis2['sentence_metrics']['num_sentences']}")
        print(f"Avg Sent Len: {analysis2['sentence_metrics']['avg_sentence_length_chars']:.2f} chars")
        print(f"Sentence Endings: {analysis2['sentence_metrics']['sentence_ending_patterns']}")
        print(f"Char Ratios (Kanji): {analysis2['vocabulary_metrics']['char_type_ratios'].get('kanji',0):.2%}")
        print(f"Punctuation (Period JP): {analysis2['punctuation_metrics'].get('period_jp',0)}")

    else:
        print(f"Analysis Error: {analysis2['error']}")

    print("\\n--- Test with empty input ---")
    empty_analysis = analyzer.analyze_texts([])
    print(f"Empty input analysis: {empty_analysis}")

    whitespace_analysis = analyzer.analyze_texts(["   \n   "])
    print(f"Whitespace input analysis: {whitespace_analysis}")

    print("\\nBasicStyleAnalyzer tests finished.")
