from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
import openai

app = Flask(__name__)

# Coloque sua chave da OpenAI aqui
openai.api_key = "SUA_CHAVE_DA_OPENAI_AQUI"

HTML_MODERNO = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovelAI Reader</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8">
        <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 mb-2">NovelAI Reader</h1>
        <p class="text-slate-400 text-sm mb-6">Cole o link do capítulo para raspar o texto e direcionar as vozes com IA.</p>
        
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">URL do Capítulo da Novel</label>
                <input type="text" name="url" placeholder="https://exemplo.com/capitulo-1" required
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-indigo-500 transition">
            </div>
            <button type="submit" 
                class="w-full bg-gradient-to-r from-indigo-500 to-cyan-500 text-slate-950 font-bold py-3 px-4 rounded-xl hover:opacity-90 transition shadow-lg shadow-indigo-500/20 cursor-pointer">
                Processar Capítulo
            </button>
        </form>

        {% if resultado %}
        <div class="mt-8 border-t border-slate-800 pt-6">
            <h2 class="text-lg font-semibold text-indigo-300 mb-2">Resultado da Análise:</h2>
            <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-300 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {{ resultado }}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        url_do_capitulo = request.form.get("url")
        try:
            # 1. Pega o capítulo
            headers = {'User-Agent': 'Mozilla/5.0'}
            resposta = requests.get(url_do_capitulo, headers=headers)
            
            if resposta.status_code == 200:
                site = BeautifulSoup(resposta.text, 'html.parser')
                paragrafos = site.find_all('p')
                texto = "\n".join([p.get_text() for p in paragrafos])
                
                # 2. Analisa com a OpenAI
                prompt = f"Analise o texto abaixo. Identifique o narrador e personagens, sugerindo vozes ideais para cada um:\n\n{texto[:3000]}"
                ai_resp = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                resultado = ai_resp.choices[0].message.content
            else:
                resultado = "Erro ao acessar a URL informada."
        except Exception as e:
            resultado = f"Ocorreu um erro: {str(e)}"
            
    return render_template_string(HTML_MODERNO, resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
