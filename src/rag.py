from flask import Flask, request, Response,render_template,flash,redirect,url_for
import os
import pickle
from janome.tokenizer import Tokenizer
from janome.analyzer import Analyzer
from janome.charfilter import UnicodeNormalizeCharFilter
from janome.tokenfilter import POSKeepFilter, POSStopFilter, LowerCaseFilter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re
import jsonify
from flask import Flask, request, Response, render_template
import os
import pickle
import pandas as pd
from werkzeug.utils import secure_filename


# アプリケーションの初期化
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)


# Configuration
UPLOAD_FOLDER = 'uploads'
MODELS_FOLDER = 'models'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)

# Initialize Janome tokenizer
tokenizer = Tokenizer()

def get_available_models():
    """利用可能なモデルの一覧を取得"""
    return [f.replace('.pkl', '') for f in os.listdir(MODELS_FOLDER) if f.endswith('.pkl')]

def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z0-9ぁ-んァ-ヶヷ-ヺー一-龥、。！？\s.,!?]', '', text)
    return text

def keitaiso(texts):
    char_filters = [UnicodeNormalizeCharFilter()]
    token_filters = [
        POSKeepFilter(['名詞', '動詞', '形容詞']),
        POSStopFilter(['助詞', '助動詞']),
        LowerCaseFilter(),
    ]
    
    analyzer = Analyzer(char_filters=char_filters, tokenizer=tokenizer, token_filters=token_filters)
    
    processed_texts = []
    for text in texts:
        tokens = [token.surface for token in analyzer.analyze(text)]
        processed_texts.append(' '.join(tokens))
    
    return processed_texts



# API Routes
@app.route('/api/models', methods=['GET'])
def get_models():
    """利用可能なモデル一覧を返すAPI"""
    models = get_available_models()
    return jsonify({
        "models": models,
        "total": len(models)
    })

def format_response(results):
    """APIレスポンスを読みやすく整形する"""
    formatted_text = ""
    
    # 基本情報
    formatted_text += "■ 検索条件\n"
    formatted_text += f"検索クエリ: {results['query']}\n"
    if results['instruction']:
        formatted_text += f"指示内容: {results['instruction']}\n"
    formatted_text += f"使用モデル: {results['model_used']}\n"
    formatted_text += "\n"
    
    # 検索結果
    formatted_text += "■ 検索結果\n"
    for i, result in enumerate(results['results'], 1):
        formatted_text += f"[結果 {i}]\n"
        formatted_text += f"類似度: {result['similarity']:.3f}\n"
        formatted_text += f"タイトル: {result['text']['title']}\n"
        
        # URLが正しく抽出されている場合のみ表示
        if result['text']['link'] and result['text']['link'] != "https":
            formatted_text += f"URL: {result['text']['link']}\n"
        
        formatted_text += "本文:\n"
        # 本文を適度な長さで改行
        content = result['text']['content']
        content = '\n'.join(content[i:i+80] for i in range(0, len(content), 80))
        formatted_text += content
        formatted_text += "\n\n"
    
    return formatted_text


def predict_with_model(query_text, model_name, top_n=10):
    model_path = os.path.join('models', f"{model_name}.pkl")
    if not os.path.exists(model_path):
        return []
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
        vectorizer, tfidf_matrix, df = model_data
    
    processed_query = keitaiso([query_text])[0]
    query_vec = vectorizer.transform([processed_query])
    
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-top_n:][::-1]
    
    results = []
    for idx in top_indices:
        text = df.iloc[idx]['Column1']  # DataFrameから直接テキストを取得
        results.append({
            'similarity': float(similarities[idx]),
            'text': text
        })
    
    return results

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    try:
        data = request.get_json()
        query = data.get('query', '')
        instruction = data.get('instruction', '')
        top_n = int(data.get('top_n', 10))
        model_name = data.get('model', 'hatena_blog_entries')  # デフォルトのモデル名
        
        results = predict_with_model(query, model_name, top_n)
        
        # プレーンテキストでレスポンスを作成
        response_text = f"""検索条件：
クエリ: {query}
指示: {instruction}
モデル: {model_name}

検索結果：
"""
        for i, result in enumerate(results, 1):
            response_text += f"""
[{i}件目]
類似度: {result['similarity']:.3f}
本文:
{result['text']}

"""
        
        return Response(
            response=response_text,
            mimetype='text/plain; charset=utf-8'
        )
        
    except Exception as e:
        return f"エラー: {str(e)}", 500
    


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data_from_file(file_path):
    """ファイルからデータを読み込む"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_ext == '.xlsx':
            df = pd.read_excel(file_path)
        elif file_ext == '.txt':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        else:
            return None

        # 全カラムを結合して一つのテキストカラムにする
        df['Column1'] = df.apply(lambda row: ' '.join(str(cell) for cell in row if pd.notna(cell)), axis=1)
        return df[['Column1']]
        
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None

def train_and_save_model(texts_to_analyze, model_name):
    """モデルの学習と保存"""
    try:
        # テキストの形態素解析
        analyzed_texts = keitaiso(texts_to_analyze)
        
        # TF-IDF変換
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(analyzed_texts)
        
        # DataFrameの作成
        df = pd.DataFrame({'Column1': texts_to_analyze})
        
        # モデルデータの保存
        model_data = (vectorizer, tfidf_matrix, df)
        model_path = os.path.join(MODELS_FOLDER, f"{model_name}.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
            
        return True, "Model trained and saved successfully"
        
    except Exception as e:
        return False, f"Error training model: {str(e)}"


@app.route('/models', methods=['GET'])
def list_models():
    """利用可能なモデルの一覧を取得"""
    try:
        models = [f.replace('.pkl', '') for f in os.listdir(MODELS_FOLDER) if f.endswith('.pkl')]
        return {'models': models}
    except Exception as e:
        return {'error': str(e)}, 500

# Web Routes
@app.route('/')
def home():
    models = get_available_models()
    return render_template('index.html', models=models)

@app.route('/analyze_form')
def analyze_form():
    """分析フォームページ"""
    models = [f.replace('.pkl', '') for f in os.listdir(MODELS_FOLDER) if f.endswith('.pkl')]
    return render_template('analyze_form.html', models=models)

@app.route('/analyze', methods=['POST'])
def analyze():
    """テキスト分析の実行とフォーム送信後の処理"""
    instruction = request.form.get('instruction', '')
    query = request.form.get('query', '')
    model_name = request.form.get('model', '')
    top_n = int(request.form.get('top_n', 10))
    
    results = predict_with_model(query, model_name, top_n)
    
    # プレーンテキストで結果を表示
    response_text = f"""検索条件：
クエリ: {query}
指示: {instruction}
モデル: {model_name}

検索結果：
"""
    for i, result in enumerate(results, 1):
        response_text += f"""
[{i}件目]
類似度: {result['similarity']:.3f}
本文:
{result['text']}

"""
    
    return Response(
        response=response_text,
        mimetype='text/plain; charset=utf-8'
    )

@app.route('/upload_form')
def upload_form():
    """アップロードフォームページ"""
    return render_template('upload_form.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """ファイルアップロードの処理"""
    try:
        if 'file' not in request.files:
            flash('ファイルがアップロードされていません', 'error')
            return redirect(url_for('upload_form'))
            
        file = request.files['file']
        model_name = request.form.get('model_name', '')
        
        if file.filename == '':
            flash('ファイルが選択されていません', 'error')
            return redirect(url_for('upload_form'))
            
        if not model_name:
            flash('モデル名を入力してください', 'error')
            return redirect(url_for('upload_form'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                df = load_data_from_file(file_path)
                if df is None:
                    raise ValueError('ファイルの読み込みに失敗しました')
                    
                success, message = train_and_save_model(df['Column1'].tolist(), model_name)
                
                if success:
                    flash(message, 'success')
                else:
                    flash(f'モデルの学習に失敗しました: {message}', 'error')
                    
            finally:
                # 一時ファイルの削除
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            return redirect(url_for('upload_form'))
        else:
            flash('許可されていないファイル形式です', 'error')
            return redirect(url_for('upload_form'))
                
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('upload_form'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
