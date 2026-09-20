import os
from flask import Flask, render_template_string
from openai import OpenAI

app = Flask(__name__)

# Configuração da IA (Certifique-se de colocar sua chave da OpenAI nas variáveis de ambiente do Render!)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# "Banco de dados" simples na memória para manter a mesma voz do personagem
# Exemplo: {"Heroi": "alloy", "Vilao": "onyx"}
cache_vozes_personagens = {}

VOzes_disponiveis = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

def escolher_voz_para_personagem(nome_personagem):
    if nome_personagem not in cache_vozes_personagens:
        # Pega a próxima voz disponível de forma rotativa
        indice = len(cache_vozes_personagens) % len(VOzes_disponiveis)
        cache_vozes_personagens[nome_personagem] = VOzes_disponiveis[indice]
    return cache_vozes_personagens[nome_personagem]

# Design da interface em Dark Mode moderno
HTML_DESIGN = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novel Audiobook IA</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 600px;
            background: #1e1e1e;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        }
        h1 {
            color: #bb86fc;
            font-size: 24px;
            text-align: center;
        }
        p {
            color: #b0b0b0;
            text-align: center;
        }
        .player-box {
            background: #2c2c2c;
            padding: 16px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
        }
        button {
            background-color: #bb86fc;
            color: #121212;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #9965f4;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Novel Audiobook IA</h1>
        <p>Seu leitor inteligente com vozes humanas consistentes por personagem.</p>
        
        <div class="player-box">
            <h3>Capítulo Atual: 01</h3>
            <p>Status: Pronto para gerar o audiobook.</p>
            <button onclick="alert('Gerando áudio com vozes personalizadas!')">Ouvir Capítulo</button>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_DESIGN)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
