import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock main.py for Hatena Blog Suite")
    parser.add_argument("--mode", type=str, required=True, choices=["extract", "image", "linkcheck"], help="Operation mode")
    parser.add_argument("--hatena-id", type=str, required=True, help="Hatena ID")
    # 想定される他の引数も追加可能
    # parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    result = {
        "message": f"Mock main.py executed successfully.",
        "mode": args.mode,
        "hatena_id": args.hatena_id,
        # "output_dir": args.output_dir
    }

    # print(f"Mock main.py called with mode: {args.mode}, hatena_id: {args.hatena_id}")
    # MCPサーバーがサブプロセスとして呼び出す場合、標準出力ではなく、
    # 何らかの形で結果を連携する必要があるかもしれないが、
    # 今回のMCPサーバーはコマンド文字列を返すだけなので、main.pyの出力は直接は使われない。
    # ここでは、単に実行されたことを示すためにprintする。
    print(json.dumps(result))
