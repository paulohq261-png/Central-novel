import os
from flask import Flask, render_template_string

app = Flask(__name__)

chave = os.environ.get("OPENAI_API_KEY")
if chave:
    from openai import OpenAI
    client = OpenAI(api_key=chave)
else:
    client = None
    print("⚠️ Chave não configurada — interface funciona normalmente")

cache_vozes = {}
VOZES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel 2</title>
    <style>
        body{background:#121212;color:#e0e0e0;font-family:sans-serif;padding:20px}
        .caixa{max-width:600px;margin:0 auto;background:#1e1e1e;padding:24px;border-radius:12px}
        h1{color:#bb86fc;text-align:center}
        button{background:#bb86fc;border:none;padding:12px;width:100%;border-radius:6px;font-size:18px;font-weight:bold;cursor:pointer}
    </style>
</head>
<body>
    <div class="caixa">
        <h1>📖 Central Novel 2</h1>
        <p style="text-align:center;color:#999">Audiobook com vozes únicas por personagem</p>
        <button style="margin-top:20px">🔊 Ouvir Capítulo 1</button>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
