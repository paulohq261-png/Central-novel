import os
from flask import Flask, render_template_string

app = Flask(__name__)

# Pega a chave com segurança — se não tiver, avisa sem quebrar tudo
chave = os.environ.get("OPENAI_API_KEY")
if chave:
    from openai import OpenAI
    client = OpenAI(api_key=chave)
else:
    client = None
    print("⚠️ Chave OPENAI_API_KEY não configurada ainda — interface vai funcionar normalmente")

cache_vozes_personagens = {}
VOzes_disponiveis = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

def escolher_voz_para_personagem(nome_personagem):
    if nome_personagem not in cache_vozes_personagens:
        idx = len(cache_vozes_personagens) % len(VOzes_disponiveis)
        cache_vozes_personagens[nome_personagem] = VOzes_disponiveis[idx]
    return cache_vozes_personagens[nome_personagem]

HTML_DESIGN = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel 2 — Audiobook IA</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:#121212;color:#e0e0e0;font-family:'Segoe UI',sans-serif;padding:20px}
        .container{max-width:600px;margin:0 auto;background:#1e1e1e;padding:24px;border-radius:12px;box-shadow:0 8px 16px rgba(0,0,0,.5)}
        h1{color:#bb86fc;text-align:center;font-size:24px;margin-bottom:8px}
        p.sub{color:#999;text-align:center;margin-bottom:24px}
        .card{background:#2c2c2c;padding:20px;border-radius:8px;margin-bottom:16px}
        h3{color:#fff;margin-bottom:8px}
        button{background:#bb86fc;color:#000;border:none;padding:10px 20px;border-radius:6px;font-weight:bold;cursor:pointer;width:100%;font-size:16px}
        button:hover{background:#9965f4}
        .status{margin-top:12px;padding:10px;border-radius:4px;background:#333;font-size:14px}
    </style>
</head>
<body>
    <div class="container">
        <h1>📖 Central Novel 2</h1>
        <p class="sub">Audiobook com vozes únicas por personagem</p>
        <div class="card">
            <h3>Capítulo 01</h3>
            <p>Status: Pronto para ouvir</p>
            <button>🔊 Ouvir Capítulo</button>
            <div class="status">Sistema de vozes: Ativo • Memória de personagens: OK</div>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_DESIGN)

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
