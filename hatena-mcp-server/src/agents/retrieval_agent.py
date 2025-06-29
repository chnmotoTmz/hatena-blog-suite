import os
import re
from typing import List, Dict, Optional, Tuple
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import chromadb
from chromadb.config import Settings
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class RetrievalAgent:
    def __init__(self, openai_api_key: str, chroma_persist_dir: str = "./chroma_db"):
        self.openai_api_key = openai_api_key
        self.chroma_persist_dir = chroma_persist_dir
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            temperature=0.7,
            model_name="gpt-4"
        )
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def create_vectorstore_from_articles(self, articles: List[Dict]):
        documents = []
        
        for article in articles:
            content = article.get('full_content', '') or article.get('summary', '')
            if not content:
                continue
                
            metadata = {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'categories': ', '.join(article.get('categories', [])),
                'word_count': article.get('word_count', 0)
            }
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
        
        split_documents = self.text_splitter.split_documents(documents)
        
        self.vectorstore = Chroma.from_documents(
            documents=split_documents,
            embedding=self.embeddings,
            persist_directory=self.chroma_persist_dir
        )
        self.vectorstore.persist()
        
    def load_vectorstore(self):
        self.vectorstore = Chroma(
            persist_directory=self.chroma_persist_dir,
            embedding_function=self.embeddings
        )
    
    def find_related_articles(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Create or load it first.")
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results
    
    def generate_article_with_links(self, 
                                  content: str, 
                                  tone_reference: Optional[str] = None,
                                  max_links: int = 3) -> str:
        related_docs = self.find_related_articles(content, k=max_links * 2)
        
        unique_articles = {}
        for doc, score in related_docs:
            url = doc.metadata.get('url', '')
            if url and url not in unique_articles:
                unique_articles[url] = {
                    'title': doc.metadata.get('title', ''),
                    'url': url,
                    'score': score,
                    'content_snippet': doc.page_content[:200]
                }
        
        sorted_articles = sorted(
            unique_articles.values(), 
            key=lambda x: x['score']
        )[:max_links]
        
        links_context = "\n".join([
            f"- [{article['title']}]({article['url']})"
            for article in sorted_articles
        ])
        
        tone_instruction = ""
        if tone_reference:
            tone_instruction = f"\n\n参考文体：\n{tone_reference[:500]}...\n\nこの文体を参考にして統一感のある文章を作成してください。"
        
        prompt = PromptTemplate(
            template="""以下の内容を元に、関連記事へのリンクを自然に組み込んだ記事を作成してください。

元の内容：
{content}

利用可能な関連記事：
{links_context}
{tone_instruction}

要件：
1. 関連記事へのリンクを自然に文章に組み込む
2. リンクは適切な文脈で挿入する
3. 元の内容の意味を保持する
4. 読みやすく自然な日本語で書く

生成した記事：""",
            input_variables=["content", "links_context", "tone_instruction"]
        )
        
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": prompt}
        )
        
        result = chain.run(
            content=content,
            links_context=links_context,
            tone_instruction=tone_instruction
        )
        
        return result
    
    def analyze_writing_style(self, sample_articles: List[str]) -> str:
        combined_text = "\n\n".join(sample_articles[:5])
        
        prompt = f"""以下の文章サンプルを分析して、文体の特徴を抽出してください：

{combined_text[:2000]}

以下の観点で分析してください：
1. 文末表現（です・ます調、だ・である調など）
2. 語彙の選択（専門用語の使い方、カジュアル/フォーマル）
3. 文章の長さと構造
4. 特徴的な表現やフレーズ
5. 段落構成の特徴

分析結果："""
        
        response = self.llm.predict(prompt)
        return response
    
    def auto_detect_similar_articles(self, content: str, threshold: float = 0.8) -> List[Dict]:
        """記事の類似度を自動検出して関連記事を見つける"""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Create or load it first.")
        
        results = self.vectorstore.similarity_search_with_score(content, k=10)
        
        similar_articles = []
        for doc, score in results:
            if score < threshold:  # スコアが低いほど類似度が高い
                similar_articles.append({
                    'title': doc.metadata.get('title', ''),
                    'url': doc.metadata.get('url', ''),
                    'similarity_score': score,
                    'snippet': doc.page_content[:200] + '...',
                    'categories': doc.metadata.get('categories', ''),
                    'date': doc.metadata.get('date', '')
                })
        
        return similar_articles
    
    def generate_cross_references(self, articles: List[Dict]) -> Dict:
        """記事間のクロスリファレンスを自動生成"""
        cross_refs = {}
        
        for i, article in enumerate(articles):
            content = article.get('full_content', '') or article.get('summary', '')
            if not content:
                continue
                
            similar = self.auto_detect_similar_articles(content)
            
            # 自分自身を除外
            similar = [s for s in similar if s['url'] != article.get('url')]
            
            cross_refs[article.get('url', f'article_{i}')] = {
                'title': article.get('title', ''),
                'related_articles': similar[:5],  # 上位5件
                'categories': article.get('categories', []),
                'generated_at': datetime.now().isoformat()
            }
        
        return cross_refs
    
    def enhance_content_with_internal_links(self, content: str, max_links: int = 3) -> str:
        """コンテンツに内部リンクを自動挿入"""
        if not self.vectorstore:
            return content
        
        # 関連記事を検索
        related_articles = self.auto_detect_similar_articles(content, threshold=0.7)[:max_links]
        
        if not related_articles:
            return content
        
        # コンテンツを解析してリンク挿入ポイントを特定
        sentences = re.split(r'[。！？]', content)
        enhanced_content = content
        
        # 各関連記事について適切な挿入ポイントを探す
        for article in related_articles:
            title_words = article['title'].split()
            
            # タイトルのキーワードが含まれる文を探す
            for sentence in sentences:
                for word in title_words:
                    if word in sentence and len(word) > 2:  # 短すぎる単語は除外
                        # リンクを挿入
                        link_text = f"[{article['title']}]({article['url']})"
                        enhanced_content = enhanced_content.replace(
                            sentence, 
                            sentence + f"\n\n関連記事: {link_text}",
                            1  # 最初の1件のみ
                        )
                        break
                else:
                    continue
                break
        
        return enhanced_content