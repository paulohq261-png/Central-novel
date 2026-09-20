from flask import Flask, render_template_string, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

# Configura a IA da OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Front-end moderno
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dola Novel Audio</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center p-4">
    <div class="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 mt-6">
        <header class="text-center mb-6">
            <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
                Dola Novel Hub 🎙️✨
            </h1>
            <p class="text-slate-400 text-sm mt-1">Sua central inteligente de leitura e áudio</p>
        </header>

        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Nome da Novel ou Link:</label>
                <input type="text" id="novelInput" placeholder="Ex: Shadow Slave - Capítulo 1" 
                    class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500">
            </div>
            <button onclick="buscarNovel()" id="btnBuscar"
                class="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 rounded-xl shadow-lg hover:opacity-90 transition">
                🚀 Buscar e Processar Capítulo
            </button>
        </div>

        <div id="loading" class="hidden text-center my-6">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-purple-500 border-t-transparent"></div>
            <p class="text-slate-400 text-sm mt-2">Dola está buscando e traduzindo...</p>
        </div>

        <div id="resultado" class="mt-6 hidden">
            <h2 class="text-lg font-bold text-purple-400 mb-2">Resultado:</h2>
            <div id="textoGerado" class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-300 max-h-60 overflow-y-auto"></div>
        </div>
    </div>

    <script>
        async function buscarNovel() {
            const query = document.getElementById('novelInput').value;
            if (!query) { alert('Digite o nome ou link da novel!'); return; }

            const btn = document.getElementById('btnBuscar');
            const loading = document.getElementById('loading');
            const resultado = document.getElementById('resultado');
            const textoGerado = document.getElementById('textoGerado');

            btn.disabled = true;
            loading.classList.remove('hidden');
            resultado.classList.add('hidden');

            try {
                const res = await fetch('/api/processar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await res.json();
                textoGerado.innerText = data.resposta;
                resultado.classList.remove('hidden');
            } catch (err) {
                alert('Erro: ' + err);
            } finally {
                btn.disabled = false;
                loading.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/processar", methods=["POST"])
def processar():
    data = request.json
    query = data.get("query", "")

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é a Dola, especialista em novels. Busca, resume e narra histórias em português."},
                {"role": "user", "content": f"Capítulo/história: {query}. Apresente um resumo e trecho em português fluído, estilo narrativo."}
            ]
        )
        return jsonify({"resposta": resposta.choices[0].message.content})
    except Exception as e:
        return jsonify({"resposta": f"Erro: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
