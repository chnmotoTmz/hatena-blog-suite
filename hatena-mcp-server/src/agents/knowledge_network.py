import os
import json
import networkx as nx
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI不要のバックエンドを使用


class KnowledgeNetworkManager:
    def __init__(self, output_dir: str = "./knowledge_network"):
        self.output_dir = output_dir
        self.graph = nx.Graph()
        self.article_vectors = {}
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 日本語のストップワードは別途設定
            ngram_range=(1, 2)
        )
        self.topic_clusters = {}
        self.relationship_matrix = None
        
        os.makedirs(output_dir, exist_ok=True)
    
    def build_knowledge_graph(self, articles: List[Dict]) -> Dict:
        """記事データから知識グラフを構築"""
        print("知識グラフを構築中...")
        
        # 記事をノードとして追加
        for i, article in enumerate(articles):
            node_id = f"article_{i}"
            self.graph.add_node(node_id, **{
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'categories': article.get('categories', []),
                'word_count': article.get('word_count', 0),
                'content': article.get('full_content', '') or article.get('summary', '')
            })
        
        # 記事間の類似度を計算してエッジを追加
        self._calculate_article_similarities(articles)
        
        # トピッククラスターを生成
        self._generate_topic_clusters(articles)
        
        # 知識ネットワークの統計を計算
        stats = self._calculate_network_statistics()
        
        # グラフを保存
        self._save_knowledge_graph()
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'statistics': stats,
            'topic_clusters': len(self.topic_clusters),
            'created_at': datetime.now().isoformat()
        }
    
    def _calculate_article_similarities(self, articles: List[Dict]):
        """記事間の類似度を計算してエッジを追加"""
        # テキストデータを準備
        contents = []
        node_ids = []
        
        for i, article in enumerate(articles):
            content = article.get('full_content', '') or article.get('summary', '')
            if content.strip():
                contents.append(content)
                node_ids.append(f"article_{i}")
        
        if len(contents) < 2:
            return
        
        # TF-IDFベクトル化
        tfidf_matrix = self.vectorizer.fit_transform(contents)
        
        # コサイン類似度を計算
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # 類似度の高い記事間にエッジを追加
        threshold = 0.3  # 類似度の閾値
        
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                similarity = similarity_matrix[i][j]
                if similarity > threshold:
                    self.graph.add_edge(
                        node_ids[i], 
                        node_ids[j], 
                        weight=similarity,
                        relationship_type='content_similarity'
                    )
        
        # ベクトルを保存
        for i, node_id in enumerate(node_ids):
            self.article_vectors[node_id] = tfidf_matrix[i].toarray().flatten()
    
    def _generate_topic_clusters(self, articles: List[Dict]):
        """トピッククラスターを生成"""
        from sklearn.cluster import KMeans
        
        if not self.article_vectors:
            return
        
        # ベクトルデータを準備
        vectors = np.array(list(self.article_vectors.values()))
        node_ids = list(self.article_vectors.keys())
        
        # 適切なクラスター数を決定（記事数の平方根程度）
        n_clusters = max(2, min(8, int(np.sqrt(len(articles)))))
        
        # K-meansクラスタリング
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(vectors)
        
        # クラスター情報を整理
        clusters = defaultdict(list)
        for node_id, label in zip(node_ids, cluster_labels):
            clusters[f"cluster_{label}"].append(node_id)
        
        # 各クラスターの特徴語を抽出
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id, cluster_nodes in clusters.items():
            # クラスター内の記事のベクトルを平均
            cluster_vectors = [self.article_vectors[node] for node in cluster_nodes]
            mean_vector = np.mean(cluster_vectors, axis=0)
            
            # 重要な特徴語を抽出
            top_features_idx = np.argsort(mean_vector)[-10:]
            top_features = [feature_names[i] for i in top_features_idx]
            
            # クラスター内の記事タイトルを取得
            titles = []
            for node in cluster_nodes:
                title = self.graph.nodes[node].get('title', '')
                if title:
                    titles.append(title)
            
            self.topic_clusters[cluster_id] = {
                'nodes': cluster_nodes,
                'titles': titles,
                'key_features': top_features,
                'size': len(cluster_nodes)
            }
    
    def _calculate_network_statistics(self) -> Dict:
        """ネットワークの統計情報を計算"""
        stats = {}
        
        if self.graph.number_of_nodes() == 0:
            return stats
        
        # 基本統計
        stats['density'] = nx.density(self.graph)
        stats['average_clustering'] = nx.average_clustering(self.graph)
        
        # 中心性指標
        if self.graph.number_of_edges() > 0:
            degree_centrality = nx.degree_centrality(self.graph)
            stats['most_central_articles'] = sorted(
                degree_centrality.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # ベットウィーン中心性（小さなグラフのみ）
            if self.graph.number_of_nodes() < 100:
                betweenness = nx.betweenness_centrality(self.graph)
                stats['bridge_articles'] = sorted(
                    betweenness.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
        
        # 連結成分の分析
        components = list(nx.connected_components(self.graph))
        stats['connected_components'] = len(components)
        stats['largest_component_size'] = max(len(c) for c in components) if components else 0
        
        return stats
    
    def find_related_articles(self, article_content: str, top_k: int = 5) -> List[Dict]:
        """指定されたコンテンツに関連する記事を検索"""
        if not self.article_vectors or not hasattr(self.vectorizer, 'vocabulary_'):
            return []
        
        # 入力コンテンツをベクトル化
        content_vector = self.vectorizer.transform([article_content]).toarray().flatten()
        
        # 各記事との類似度を計算
        similarities = []
        for node_id, article_vector in self.article_vectors.items():
            similarity = cosine_similarity([content_vector], [article_vector])[0][0]
            
            node_data = self.graph.nodes[node_id]
            similarities.append({
                'node_id': node_id,
                'title': node_data.get('title', ''),
                'url': node_data.get('url', ''),
                'similarity': similarity,
                'categories': node_data.get('categories', [])
            })
        
        # 類似度順にソート
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def get_article_neighbors(self, article_id: str, max_hops: int = 2) -> Dict:
        """指定された記事の近隣ノードを取得"""
        if article_id not in self.graph:
            return {}
        
        neighbors = {}
        
        # 直接の隣接ノード
        direct_neighbors = list(self.graph.neighbors(article_id))
        neighbors['direct'] = []
        
        for neighbor in direct_neighbors:
            edge_data = self.graph.edges[article_id, neighbor]
            node_data = self.graph.nodes[neighbor]
            
            neighbors['direct'].append({
                'node_id': neighbor,
                'title': node_data.get('title', ''),
                'url': node_data.get('url', ''),
                'similarity': edge_data.get('weight', 0),
                'relationship_type': edge_data.get('relationship_type', 'unknown')
            })
        
        # 2ホップ先の隣接ノード
        if max_hops >= 2:
            two_hop_neighbors = []
            for neighbor in direct_neighbors:
                for second_neighbor in self.graph.neighbors(neighbor):
                    if second_neighbor != article_id and second_neighbor not in direct_neighbors:
                        node_data = self.graph.nodes[second_neighbor]
                        two_hop_neighbors.append({
                            'node_id': second_neighbor,
                            'title': node_data.get('title', ''),
                            'url': node_data.get('url', ''),
                            'via': neighbor
                        })
            
            neighbors['two_hop'] = two_hop_neighbors[:10]  # 上位10件
        
        return neighbors
    
    def generate_knowledge_map_visualization(self, output_file: str = None):
        """知識マップの可視化を生成"""
        if self.graph.number_of_nodes() == 0:
            return
        
        plt.figure(figsize=(15, 10))
        
        # レイアウトを計算
        if self.graph.number_of_nodes() < 50:
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        else:
            pos = nx.random_layout(self.graph)
        
        # ノードの色をクラスターごとに分ける
        node_colors = []
        cluster_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        for node in self.graph.nodes():
            color = 'lightblue'  # デフォルト色
            for i, (cluster_id, cluster_data) in enumerate(self.topic_clusters.items()):
                if node in cluster_data['nodes']:
                    color = cluster_colors[i % len(cluster_colors)]
                    break
            node_colors.append(color)
        
        # ノードサイズを次数に基づいて設定
        node_sizes = [300 + 50 * self.graph.degree(node) for node in self.graph.nodes()]
        
        # エッジの重みに基づいて透明度を設定
        edge_weights = [self.graph.edges[edge].get('weight', 0.1) for edge in self.graph.edges()]
        edge_alphas = [min(1.0, weight * 2) for weight in edge_weights]
        
        # グラフを描画
        nx.draw_networkx_nodes(
            self.graph, pos, 
            node_color=node_colors, 
            node_size=node_sizes,
            alpha=0.8
        )
        
        nx.draw_networkx_edges(
            self.graph, pos,
            alpha=0.3,
            edge_color='gray'
        )
        
        # ラベルを追加（ノード数が少ない場合のみ）
        if self.graph.number_of_nodes() <= 20:
            labels = {}
            for node in self.graph.nodes():
                title = self.graph.nodes[node].get('title', '')
                labels[node] = title[:20] + '...' if len(title) > 20 else title
            
            nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        
        plt.title('Knowledge Network Map', fontsize=16)
        plt.axis('off')
        
        # 保存
        if not output_file:
            output_file = os.path.join(self.output_dir, 'knowledge_map.png')
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def export_for_notebook_lm(self, output_file: str = None) -> str:
        """Google NotebookLM用のデータをエクスポート"""
        if not output_file:
            output_file = os.path.join(self.output_dir, 'notebook_lm_export.json')
        
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_articles': self.graph.number_of_nodes(),
                'connections': self.graph.number_of_edges(),
                'topic_clusters': len(self.topic_clusters)
            },
            'articles': [],
            'relationships': [],
            'topic_clusters': self.topic_clusters,
            'network_statistics': self._calculate_network_statistics()
        }
        
        # 記事データをエクスポート
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            export_data['articles'].append({
                'id': node_id,
                'title': node_data.get('title', ''),
                'url': node_data.get('url', ''),
                'date': node_data.get('date', ''),
                'categories': node_data.get('categories', []),
                'content': node_data.get('content', '')[:1000] + '...',  # 最初の1000文字
                'word_count': node_data.get('word_count', 0)
            })
        
        # 関係性データをエクスポート
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            export_data['relationships'].append({
                'source': source,
                'target': target,
                'similarity': data.get('weight', 0),
                'type': data.get('relationship_type', 'similarity')
            })
        
        # JSON形式で保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def _save_knowledge_graph(self):
        """知識グラフを保存"""
        # GraphMLフォーマットで保存（リストデータを文字列に変換）
        try:
            # ノードデータのリストを文字列に変換し、Noneを空文字に変換
            for node, data in self.graph.nodes(data=True):
                for key, value in data.items():
                    if value is None:
                        data[key] = ''
                    elif isinstance(value, list):
                        data[key] = ', '.join(map(str, value))
                    else:
                        data[key] = str(value)
            
            graphml_file = os.path.join(self.output_dir, 'knowledge_graph.graphml')
            nx.write_graphml(self.graph, graphml_file)
        except Exception as e:
            print(f"GraphML保存でエラー: {e}")
        
        # Pickleフォーマットで保存（高速読み込み用）
        pickle_file = os.path.join(self.output_dir, 'knowledge_graph.pkl')
        with open(pickle_file, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'article_vectors': self.article_vectors,
                'topic_clusters': self.topic_clusters,
                'vectorizer': self.vectorizer
            }, f)
    
    def load_knowledge_graph(self):
        """保存された知識グラフを読み込み"""
        pickle_file = os.path.join(self.output_dir, 'knowledge_graph.pkl')
        
        try:
            with open(pickle_file, 'rb') as f:
                data = pickle.load(f)
                self.graph = data['graph']
                self.article_vectors = data['article_vectors']
                self.topic_clusters = data['topic_clusters']
                self.vectorizer = data['vectorizer']
            return True
        except FileNotFoundError:
            return False
    
    def generate_knowledge_report(self) -> str:
        """知識ネットワークのレポートを生成"""
        stats = self._calculate_network_statistics()
        
        report_lines = []
        report_lines.append("# 知識ネットワーク分析レポート")
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 基本統計
        report_lines.append("## ネットワーク統計")
        report_lines.append(f"- 記事数: {self.graph.number_of_nodes()}")
        report_lines.append(f"- 関連性リンク数: {self.graph.number_of_edges()}")
        report_lines.append(f"- ネットワーク密度: {stats.get('density', 0):.3f}")
        report_lines.append(f"- クラスタリング係数: {stats.get('average_clustering', 0):.3f}")
        report_lines.append("")
        
        # トピッククラスター
        report_lines.append("## トピッククラスター")
        for cluster_id, cluster_data in self.topic_clusters.items():
            report_lines.append(f"### {cluster_id} ({cluster_data['size']}記事)")
            report_lines.append("記事:")
            for title in cluster_data['titles'][:5]:
                report_lines.append(f"- {title}")
            report_lines.append(f"キーワード: {', '.join(cluster_data['key_features'][:5])}")
            report_lines.append("")
        
        # 中心性の高い記事
        if 'most_central_articles' in stats:
            report_lines.append("## 影響力の高い記事")
            for node_id, centrality in stats['most_central_articles']:
                title = self.graph.nodes[node_id].get('title', 'Unknown')
                report_lines.append(f"- {title} (中心性: {centrality:.3f})")
            report_lines.append("")
        
        return "\n".join(report_lines)