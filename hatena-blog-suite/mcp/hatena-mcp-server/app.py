from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# ルートディレクトリを基準に main.py のパスを設定
# app.py は hatena-blog-suite/mcp/hatena-mcp-server/app.py にある
# main.py は hatena-blog-suite/main.py にあると想定 (READMEのクイックスタートより)
# os.path.dirname(__file__) は hatena-blog-suite/mcp/hatena-mcp-server
# ".." で hatena-blog-suite/mcp
# "../.." で hatena-blog-suite (これがリポジトリルートだと想定)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAIN_PY_PATH = os.path.join(BASE_DIR, "main.py")
# print(f"BASE_DIR (expected: <path_to_repo>/hatena-blog-suite): {BASE_DIR}")
# print(f"MAIN_PY_PATH (expected: <path_to_repo>/hatena-blog-suite/main.py): {MAIN_PY_PATH}")
# print(f"Current working directory: {os.getcwd()}")


@app.route('/mcp', methods=['POST'])
def mcp_handler():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400

    message = data['message']
    hatena_id = os.environ.get("HATENA_ID")
    if not hatena_id:
        # MCPサーバー設定の例から、環境変数で渡されることを期待
        # それがない場合は、リクエストから取得しようと試みるか、エラーとする
        # ここでは、デモのために固定値を一時的に使うか、エラーを返す
        # 本来は起動時に環境変数で設定されるべき
        # return jsonify({"error": "HATENA_ID environment variable is not set."}), 500
        # READMEのMCP Server設定例では "env": { "HATENA_ID": "your-id" } となっているので、
        # 実際にはClaude Desktopから環境変数が渡される想定
        # ここではダミーのIDを使うか、リクエストに含めてもらう必要がある
        # 簡単のため、もし環境変数になければ 'your-id' を使う
        hatena_id = data.get("hatena_id", "your-id") # 環境変数になければリクエストから、それもなければデフォルト

    response_message = ""
    command_to_run = []

    if "記事を抽出してください" in message:
        response_message = "記事抽出コマンドを実行します。"
        # python main.py --mode extract --hatena-id your-id
        command_to_run = ["python", MAIN_PY_PATH, "--mode", "extract", "--hatena-id", hatena_id]
    elif "画像を生成してください" in message:
        response_message = "画像生成コマンドを実行します。"
        # python main.py --mode image --hatena-id your-id
        command_to_run = ["python", MAIN_PY_PATH, "--mode", "image", "--hatena-id", hatena_id]
    elif "リンクをチェックしてください" in message:
        response_message = "リンクチェックコマンドを実行します。"
        # python main.py --mode linkcheck --hatena-id your-id
        command_to_run = ["python", MAIN_PY_PATH, "--mode", "linkcheck", "--hatena-id", hatena_id]
    else:
        return jsonify({"response": f"不明なコマンドです: {message}"}), 200

    if command_to_run:
        # 計画通り、ここでは実際にサブプロセスを実行せず、実行すべきコマンドを返す
        # 実際の運用ではサブプロセスを実行するか、RQなどのキューイングシステムにジョブを投げる
        # subprocess.Popen(command_to_run, cwd=BASE_DIR)
        return jsonify({
            "response": response_message,
            "command_to_execute": " ".join(command_to_run)
        }), 200
    else:
        # このケースは実際には上記のif分岐でカバーされるはず
        return jsonify({"error": "コマンド実行準備に失敗しました。"}), 500


if __name__ == '__main__':
    # 環境変数を設定する例 (実際の運用では .env ファイルや起動スクリプトで行う)
    # os.environ['HATENA_ID'] = 'test-user-id'
    # os.environ['HATENA_API_KEY'] = 'test-api-key'
    # os.environ['BLOG_DOMAIN'] = 'test-blog.hatenablog.com'
    app.run(debug=True, port=5001) # MCPサーバーは通常、異なるポートで実行される想定
