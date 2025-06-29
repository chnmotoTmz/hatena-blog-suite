import os
import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pickle


class PersonalizationAgent:
    def __init__(self, user_profile_path: str = None):
        self.user_profile_path = user_profile_path or "./user_profile.json"
        self.user_profile = self._load_user_profile()
        self.writing_patterns = {
            'sentence_endings': {},
            'common_phrases': {},
            'vocabulary_preferences': {},
            'paragraph_structure': {},
            'tone_indicators': {}
        }
    
    def _load_user_profile(self) -> Dict:
        """ユーザープロファイルを読み込み"""
        try:
            with open(self.user_profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'writing_style': {
                    'formality_level': 'casual',  # casual, semi-formal, formal
                    'tone': 'friendly',  # friendly, professional, enthusiastic
                    'sentence_length': 'medium',  # short, medium, long
                    'use_emojis': False,
                    'first_person': True
                },
                'vocabulary_preferences': {
                    'technical_terms': 'moderate',  # minimal, moderate, extensive
                    'foreign_words': 'minimal',
                    'colloquialisms': 'some'
                },
                'content_preferences': {
                    'introduction_style': 'direct',  # direct, story, question
                    'conclusion_style': 'summary',  # summary, call-to-action, open-ended
                    'use_examples': True,
                    'include_personal_anecdotes': True
                },
                'learned_patterns': {}
            }
    
    def save_user_profile(self):
        """ユーザープロファイルを保存"""
        with open(self.user_profile_path, 'w', encoding='utf-8') as f:
            json.dump(self.user_profile, f, ensure_ascii=False, indent=2)
    
    def analyze_writing_samples(self, articles: List[Dict]):
        """執筆サンプルを分析してユーザーの文体パターンを学習"""
        all_content = []
        
        for article in articles:
            content = article.get('full_content', '') or article.get('content', '')
            if content:
                all_content.append(content)
        
        if not all_content:
            return
        
        # 文末表現の分析
        self._analyze_sentence_endings(all_content)
        
        # 常用フレーズの分析
        self._analyze_common_phrases(all_content)
        
        # 語彙選択の分析
        self._analyze_vocabulary_patterns(all_content)
        
        # 段落構造の分析
        self._analyze_paragraph_structure(all_content)
        
        # トーンの分析
        self._analyze_tone_indicators(all_content)
        
        # プロファイルを更新
        self._update_user_profile()
    
    def _analyze_sentence_endings(self, contents: List[str]):
        """文末表現の分析"""
        endings = {}
        
        for content in contents:
            sentences = re.split(r'[。！？]', content)
            for sentence in sentences:
                if sentence.strip():
                    # 文末の2-3文字を抽出
                    ending = sentence.strip()[-3:]
                    endings[ending] = endings.get(ending, 0) + 1
        
        # 頻度順にソート
        sorted_endings = sorted(endings.items(), key=lambda x: x[1], reverse=True)
        self.writing_patterns['sentence_endings'] = dict(sorted_endings[:20])
    
    def _analyze_common_phrases(self, contents: List[str]):
        """常用フレーズの分析"""
        phrases = {}
        
        # よく使われるフレーズパターン
        phrase_patterns = [
            r'ということで',
            r'ちなみに',
            r'そもそも',
            r'要するに',
            r'つまり',
            r'実際に',
            r'とりあえず',
            r'いわゆる',
            r'一方で',
            r'しかし',
            r'また',
            r'さらに',
            r'例えば'
        ]
        
        for content in contents:
            for pattern in phrase_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    phrases[pattern] = phrases.get(pattern, 0) + len(matches)
        
        self.writing_patterns['common_phrases'] = phrases
    
    def _analyze_vocabulary_patterns(self, contents: List[str]):
        """語彙選択パターンの分析"""
        vocabulary = {
            'katakana_ratio': 0,
            'technical_terms': [],
            'informal_expressions': [],
            'formal_expressions': []
        }
        
        total_chars = 0
        katakana_chars = 0
        
        # カタカナ比率の計算
        for content in contents:
            total_chars += len(content)
            katakana_chars += len(re.findall(r'[ァ-ヴー]', content))
        
        if total_chars > 0:
            vocabulary['katakana_ratio'] = katakana_chars / total_chars
        
        # 技術用語の抽出
        tech_terms = [
            'API', 'JSON', 'HTML', 'CSS', 'JavaScript', 'Python', 'SQL',
            'アルゴリズム', 'データベース', 'フレームワーク', 'ライブラリ'
        ]
        
        for content in contents:
            for term in tech_terms:
                if term in content:
                    vocabulary['technical_terms'].append(term)
        
        self.writing_patterns['vocabulary_preferences'] = vocabulary
    
    def _analyze_paragraph_structure(self, contents: List[str]):
        """段落構造の分析"""
        structure_data = {
            'avg_paragraph_length': 0,
            'avg_sentences_per_paragraph': 0,
            'uses_bullet_points': False,
            'uses_numbered_lists': False
        }
        
        total_paragraphs = 0
        total_sentences = 0
        total_chars = 0
        
        for content in contents:
            paragraphs = content.split('\n\n')
            total_paragraphs += len(paragraphs)
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    total_chars += len(paragraph)
                    sentences = re.split(r'[。！？]', paragraph)
                    total_sentences += len([s for s in sentences if s.strip()])
            
            # リストの使用チェック
            if re.search(r'[・•]', content):
                structure_data['uses_bullet_points'] = True
            if re.search(r'\d+[.)]', content):
                structure_data['uses_numbered_lists'] = True
        
        if total_paragraphs > 0:
            structure_data['avg_paragraph_length'] = total_chars / total_paragraphs
            structure_data['avg_sentences_per_paragraph'] = total_sentences / total_paragraphs
        
        self.writing_patterns['paragraph_structure'] = structure_data
    
    def _analyze_tone_indicators(self, contents: List[str]):
        """文章のトーンを示す指標を分析"""
        tone_indicators = {
            'exclamation_ratio': 0,
            'question_ratio': 0,
            'personal_pronouns': {},
            'emotional_expressions': []
        }
        
        total_sentences = 0
        exclamations = 0
        questions = 0
        
        personal_pronouns = ['私', '僕', '俺', 'わたし', 'ぼく']
        emotional_expressions = ['すごい', 'とても', 'めちゃくちゃ', '本当に', 'かなり']
        
        for content in contents:
            sentences = re.split(r'[。！？]', content)
            total_sentences += len(sentences)
            
            exclamations += content.count('！')
            questions += content.count('？')
            
            for pronoun in personal_pronouns:
                count = content.count(pronoun)
                if count > 0:
                    tone_indicators['personal_pronouns'][pronoun] = \
                        tone_indicators['personal_pronouns'].get(pronoun, 0) + count
            
            for expr in emotional_expressions:
                if expr in content:
                    tone_indicators['emotional_expressions'].append(expr)
        
        if total_sentences > 0:
            tone_indicators['exclamation_ratio'] = exclamations / total_sentences
            tone_indicators['question_ratio'] = questions / total_sentences
        
        self.writing_patterns['tone_indicators'] = tone_indicators
    
    def _update_user_profile(self):
        """分析結果をユーザープロファイルに反映"""
        # 文体レベルの判定
        if self.writing_patterns['tone_indicators']['exclamation_ratio'] > 0.1:
            self.user_profile['writing_style']['tone'] = 'enthusiastic'
        elif 'です' in str(self.writing_patterns['sentence_endings']):
            self.user_profile['writing_style']['formality_level'] = 'semi-formal'
        
        # 語彙選択の更新
        if self.writing_patterns['vocabulary_preferences']['katakana_ratio'] > 0.1:
            self.user_profile['vocabulary_preferences']['foreign_words'] = 'moderate'
        
        # パターンデータの保存
        self.user_profile['learned_patterns'] = self.writing_patterns
        
        self.save_user_profile()
    
    def personalize_content(self, content: str, target_style: str = None) -> str:
        """コンテンツをユーザーの文体に合わせて個人化"""
        if not target_style:
            target_style = self.user_profile['writing_style']['formality_level']
        
        personalized = content
        
        # 文末表現の調整
        personalized = self._adjust_sentence_endings(personalized, target_style)
        
        # 語彙の調整
        personalized = self._adjust_vocabulary(personalized)
        
        # フレーズの調整
        personalized = self._add_personal_phrases(personalized)
        
        # 段落構造の調整
        personalized = self._adjust_paragraph_structure(personalized)
        
        return personalized
    
    def _adjust_sentence_endings(self, content: str, style: str) -> str:
        """文末表現を調整"""
        if style == 'casual':
            # 「です・ます」を「だ・である」に変換
            content = re.sub(r'です。', 'だ。', content)
            content = re.sub(r'ます。', 'る。', content)
        elif style == 'formal':
            # カジュアルな表現をフォーマルに
            content = re.sub(r'だ。', 'である。', content)
            content = re.sub(r'だよ。', 'です。', content)
        
        return content
    
    def _adjust_vocabulary(self, content: str) -> str:
        """語彙を調整"""
        # ユーザーの好みに応じた語彙置換
        if self.user_profile['vocabulary_preferences']['technical_terms'] == 'minimal':
            # 技術用語を平易な表現に置換
            replacements = {
                'アルゴリズム': '手順',
                'インターフェース': '画面',
                'パラメータ': '設定値'
            }
            for tech, simple in replacements.items():
                content = content.replace(tech, simple)
        
        return content
    
    def _add_personal_phrases(self, content: str) -> str:
        """個人的なフレーズを追加"""
        common_phrases = self.writing_patterns.get('common_phrases', {})
        
        if 'ちなみに' in common_phrases:
            # 適切な位置に「ちなみに」を追加
            paragraphs = content.split('\n\n')
            if len(paragraphs) > 1:
                paragraphs[1] = 'ちなみに、' + paragraphs[1]
                content = '\n\n'.join(paragraphs)
        
        return content
    
    def _adjust_paragraph_structure(self, content: str) -> str:
        """段落構造を調整"""
        structure = self.writing_patterns.get('paragraph_structure', {})
        
        if structure.get('uses_bullet_points'):
            # リスト形式に変換できる部分を探す
            content = re.sub(
                r'(\d+)[.)]([^。]+。)',
                r'• \2',
                content
            )
        
        return content
    
    def generate_personalized_introduction(self, topic: str) -> str:
        """個人化された導入文を生成"""
        intro_style = self.user_profile['content_preferences']['introduction_style']
        
        if intro_style == 'question':
            return f"{topic}について、どう思いますか？今回はこのテーマについて詳しく見ていきましょう。"
        elif intro_style == 'story':
            return f"先日、{topic}に関する興味深い話を聞きました。今回はその内容をシェアしたいと思います。"
        else:  # direct
            return f"今回は{topic}について解説していきます。"
    
    def generate_personalized_conclusion(self, topic: str) -> str:
        """個人化された結論を生成"""
        conclusion_style = self.user_profile['content_preferences']['conclusion_style']
        
        if conclusion_style == 'call-to-action':
            return f"{topic}について、ぜひあなたも試してみてください。何か質問があれば、コメントでお聞かせください。"
        elif conclusion_style == 'open-ended':
            return f"{topic}については、まだまだ奥が深いテーマです。皆さんはどう思われますか？"
        else:  # summary
            return f"以上、{topic}についてまとめました。参考になれば幸いです。"
    
    def get_personalization_report(self) -> Dict:
        """個人化の設定状況をレポート"""
        return {
            'user_profile': self.user_profile,
            'learned_patterns': self.writing_patterns,
            'last_updated': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """個人化改善の推奨事項を生成"""
        recommendations = []
        
        if not self.writing_patterns:
            recommendations.append("文体分析のため、過去の記事サンプルを提供してください。")
        
        if self.user_profile['writing_style']['formality_level'] == 'casual':
            recommendations.append("カジュアルな文体が設定されています. フォーマルな記事では調整を検討してください。")
        
        return recommendations