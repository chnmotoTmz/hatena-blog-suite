import re
from typing import Dict, Any, List, Optional

# This module would typically interact with style analysis results (e.g., from BasicStyleAnalyzer)
# For simplicity, this example will be self-contained but designed to accept style profiles.

class ContentPersonalizer:
    """
    Personalizes text content based on a given style profile.
    This is a basic implementation focusing on rule-based transformations.
    """

    def __init__(self, style_profile: Optional[Dict[str, Any]] = None):
        """
        Initializes the ContentPersonalizer.

        Args:
            style_profile: A dictionary representing the target writing style.
                           This profile might include preferences for:
                           - formality: "formal", "informal", "neutral"
                           - sentence_endings: Preferred endings for specific styles.
                           - vocabulary_map: A dict for word replacements (e.g., {"硬い言葉": "柔らかい言葉"}).
                           - preferred_phrases: Phrases to try and incorporate.
                           - emoji_usage: bool (not implemented in this basic version)
        """
        self.style_profile = style_profile if style_profile else self._get_default_profile()
        # Pre-compile regexes if they are complex and used often
        self._compile_regexes()

    def _get_default_profile(self) -> Dict[str, Any]:
        return {
            "formality": "neutral", # formal, informal, neutral
            "sentence_endings_map": { # Target endings based on formality
                "formal": {
                    "だ。": "である。", "だった。": "であった。",
                    "だろう。": "であろう。", "る。": "ます。", # Simple verb to polite form
                },
                "informal": {
                    "です。": "だよ。", "ます。": "るよ。", "ました。": "たよ。",
                    "である。": "だ。", "であった。": "だった。",
                }
            },
            "vocabulary_map": {
                # Example: "formal_to_informal" or "technical_to_simple"
                # "formal_to_informal": { "致します": "します", "御社": "そちらの会社" }
            },
            "preferred_phrases": {
                # "informal": ["ちなみに、", "なんか、"]
            }
        }

    def _compile_regexes(self):
        """Pre-compile regex patterns from the style profile for efficiency."""
        self.compiled_endings = {}
        endings_map = self.style_profile.get("sentence_endings_map", {})
        target_formality = self.style_profile.get("formality", "neutral")

        if target_formality in endings_map:
            self.compiled_endings[target_formality] = {
                re.compile(re.escape(src) + r'\s*$'): (dest + ' ') # Add space to ensure separation
                for src, dest in endings_map[target_formality].items()
            }
            # Add regex for general sentence splitting
            self.sentence_split_re = re.compile(r'([。！？｡!?])')


    def update_style_profile(self, new_profile: Dict[str, Any]):
        """Updates the current style profile and recompiles regexes."""
        self.style_profile.update(new_profile)
        self._compile_regexes()
        print(f"Style profile updated. Current formality: {self.style_profile.get('formality')}")


    def personalize_text(self, text: str, target_formality_override: Optional[str] = None) -> str:
        """
        Personalizes the given text according to the loaded or overridden style profile.

        Args:
            text: The input text string.
            target_formality_override: Optionally override the formality defined in the profile.

        Returns:
            The personalized text string.
        """
        if not text:
            return ""

        current_formality = target_formality_override or self.style_profile.get("formality", "neutral")

        # 1. Adjust sentence endings
        text = self._apply_sentence_ending_rules(text, current_formality)

        # 2. Adjust vocabulary
        text = self._apply_vocabulary_rules(text, current_formality)

        # 3. Incorporate preferred phrases (simplistic insertion)
        # text = self._incorporate_preferred_phrases(text, current_formality)

        return text.strip() # Remove any trailing spaces from regex replacements

    def _apply_sentence_ending_rules(self, text: str, formality: str) -> str:
        """Applies regex-based sentence ending transformations."""
        if formality not in self.compiled_endings or not hasattr(self, 'sentence_split_re'):
            return text

        # Split text into sentences and delimiters
        parts = self.sentence_split_re.split(text)
        processed_parts = []

        ending_rules = self.compiled_endings[formality]

        for i in range(0, len(parts) -1, 2): # Iterate over sentence + delimiter pairs
            sentence_segment = parts[i]
            delimiter = parts[i+1] if (i+1) < len(parts) else "" # delimiter for this segment

            # Attempt to match and replace endings *before* the delimiter
            # This is a simplified approach. True grammatical transformation is much harder.
            # We are essentially replacing the delimiter if the preceding text matches a pattern.

            # Check if the sentence segment (without its own final punctuation) + delimiter matches a rule
            # Example: "です" + "。" -> "だ" + "。"
            # We are replacing the source ending *and its punctuation* with the target ending *and its punctuation*.

            modified_segment = sentence_segment # Start with original segment

            # Try to match endings by temporarily appending the delimiter to the rule keys
            # This is tricky because rules are `src_ending_punct : dest_ending_punct`
            # We need to match `text_before_punct + src_punct` and replace with `text_before_punct + dest_punct`
            # This current regex approach might not be robust enough for this.

            # A simpler approach: replace known full endings (like "です。")
            full_segment_for_replacement = sentence_segment + delimiter
            temp_replaced_segment = full_segment_for_replacement

            for pattern_re, replacement_text in ending_rules.items():
                 # The regex `pattern_re` expects `src_ending` + `\s*$`
                 # This means it will match if `sentence_segment` ends with `src_ending`.
                 # We need to be careful about how replacement_text (dest_ending + ' ') interacts.

                 # Let's make this simpler: if "です。" is a key, replace it with "だ。"
                 # The compiled regex already has `re.escape(src) + r'\s*$'`
                 # `src` would be "です。"
                 # `dest` would be "だ。"

                 # If a rule is defined as "です。" -> "だ。", the regex is for "です。\s*$"
                 # The replacement is "だ。 "
                 # This should correctly replace "です。" at the end of `full_segment_for_replacement`

                 temp_replaced_segment = pattern_re.sub(replacement_text, temp_replaced_segment)

            if temp_replaced_segment != full_segment_for_replacement:
                 # If a replacement occurred, use the result (which includes the new punctuation)
                 processed_parts.append(temp_replaced_segment.strip()) # Strip the trailing space from replacement
            else:
                 # No rule matched, keep original segment and delimiter
                 processed_parts.append(sentence_segment)
                 processed_parts.append(delimiter)

        # If there's an odd part left (text after the last delimiter)
        if len(parts) % 2 == 1:
            processed_parts.append(parts[-1])

        return "".join(processed_parts)


    def _apply_vocabulary_rules(self, text: str, formality: str) -> str:
        """Applies vocabulary replacements based on the profile."""
        # Vocab map could be structured like: {"general": {"old": "new"}, "formal_to_informal": {...}}
        vocab_map_for_style = self.style_profile.get("vocabulary_map", {}).get(formality, {})
        general_vocab_map = self.style_profile.get("vocabulary_map", {}).get("general", {})

        combined_vocab_map = {**general_vocab_map, **vocab_map_for_style} # Style-specific overrides general

        for old_word, new_word in combined_vocab_map.items():
            # Use regex to replace whole words only to avoid partial matches in larger words.
            # For Japanese, word boundaries (\b) are complex. A simpler space-boundary or careful non-greedy match might be needed.
            # This simple replace is a placeholder for more advanced token-based replacement.
            text = text.replace(old_word, new_word) # Basic replacement
            # text = re.sub(r'\b' + re.escape(old_word) + r'\b', new_word, text) # For space-separated languages
        return text

    # Incorporating preferred phrases is more complex and context-dependent.
    # A simple version might randomly insert them or prepend/append to sentences/paragraphs.
    # This is omitted for this basic version due to its complexity for good results.

if __name__ == '__main__':
    print("--- Testing ContentPersonalizer ---")

    # Profile for informal style
    informal_profile = {
        "formality": "informal",
        "sentence_endings_map": {
            "informal": { # Target this formality
                "です。": "だよ。",
                "ます。": "るんだ。", # Example: 行きます -> 行くんだ
                "ました。": "たんだ。", # Example: 行きました -> 行ったんだ
                "でしょう。": "だろうね。",
                "である。": "なんだ。", # More emphatic than just "だ。"
            }
        },
        "vocabulary_map": {
            "general": {"非常に": "すごく", "しかし": "でも"},
            "informal": {"致します": "するね", "御社": "キミの会社"} # Specific to informal
        }
    }

    # Profile for formal style
    formal_profile = {
        "formality": "formal",
        "sentence_endings_map": {
            "formal": {
                "だ。": "である。",
                "だった。": "であった。",
                "だろう。": "であろう。",
                "だよ。": "です。",
                "るんだ。": "ます。", # Example: 行くんだ -> 行きます
                "たんだ。": "ました。", # Example: 行ったんだ -> 行きました
            }
        },
        "vocabulary_map": {
            "general": {"非常に": "大変", "しかし": "然しながら"}, # Keep "非常に" or change to another formal
            "formal": {"すごい": "素晴らしい", "キミの会社": "貴社"}
        }
    }

    text_sample1 = "これはテストです。明日晴れます。しかし非常に難しい問題だった。我々は進む。"
    text_sample2 = "吾輩は猫である。名前はまだ無いのだ。すごいだろう。" # Uses だ。

    print("\\n--- Test 1: Informal Personalization ---")
    personalizer_informal = ContentPersonalizer(style_profile=informal_profile)
    informal_text1 = personalizer_informal.personalize_text(text_sample1)
    print(f"Original: {text_sample1}")
    print(f"Informal: {informal_text1}")
    # Expected: "これはテストだよ。 明日晴れるんだ。 でもすごく難しい問題だったんだ。 我々は進むんだ。" (approx)

    informal_text2 = personalizer_informal.personalize_text(text_sample2)
    print(f"Original: {text_sample2}")
    print(f"Informal: {informal_text2}")
    # Expected: "吾輩は猫なんだ。 名前はまだ無いんだ。 すごいだろうね。" (approx, "すごい" might not change if not in vocab map)


    print("\\n--- Test 2: Formal Personalization ---")
    personalizer_formal = ContentPersonalizer(style_profile=formal_profile)
    formal_text1 = personalizer_formal.personalize_text(text_sample1) # Original has です/ます
    print(f"Original: {text_sample1}")
    print(f"Formal: {formal_text1}")
    # Expected: "これはテストです。明日晴れます。然しながら大変難しい問題であった。我々は進みます。" (approx, some endings might not change if not in map)
                                                         # "だった" -> "であった"

    formal_text2 = personalizer_formal.personalize_text(text_sample2) # Original has だ
    print(f"Original: {text_sample2}")
    print(f"Formal: {formal_text2}")
    # Expected: "吾輩は猫である。名前はまだ無いのである。素晴らしいであろう。" (approx)


    print("\\n--- Test 3: Override formality at runtime ---")
    # Using informal personalizer, but overriding to formal for one call
    override_formal_text = personalizer_informal.personalize_text(text_sample2, target_formality_override="formal")
    print(f"Original: {text_sample2}")
    print(f"Overridden to Formal (using informal_profile base but formal endings): {override_formal_text}")
    # This will use 'informal_profile's vocab but 'formal' endings if 'formal' is in its map.
    # This highlights the need for comprehensive maps or a more dynamic selection.
    # The current `_apply_sentence_ending_rules` uses `self.compiled_endings[formality]`.
    # So, if `informal_profile` doesn't have a key for "formal" in its `sentence_endings_map`,
    # no ending changes for "formal" will occur.

    # Let's test with a personalizer that has both formal and informal maps, then override
    comprehensive_profile = {
        "formality": "neutral", # Default
         "sentence_endings_map": {
            "informal": informal_profile["sentence_endings_map"]["informal"],
            "formal": formal_profile["sentence_endings_map"]["formal"],
        },
        "vocabulary_map": { "general": {"非常に": "とても"} }
    }
    comp_personalizer = ContentPersonalizer(comprehensive_profile)

    print("Using comprehensive personalizer:")
    comp_formal_override = comp_personalizer.personalize_text(text_sample2, target_formality_override="formal")
    print(f"Original: {text_sample2}")
    print(f"Comp. Overridden to Formal: {comp_formal_override}")
    # Expected: "吾輩は猫である。名前はまだ無いのである。すごいであろう。"

    comp_informal_override = comp_personalizer.personalize_text(text_sample1, target_formality_override="informal")
    print(f"Original: {text_sample1}")
    print(f"Comp. Overridden to Informal: {comp_informal_override}")
    # Expected: "これはテストだよ。明日晴れるんだ。しかしとても難しい問題だったんだ。我々は進むんだ。"

    print("\\nContentPersonalizer tests finished.")
