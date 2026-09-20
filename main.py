from flask import Flask, render_template_string, request, jsonify, send_file
import os
import google.generativeai as genai
from gtts import gTTS

app = Flask(__name__)

# Configura a API do Google Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Front-end limpo, profissional e sem nomes da assistente
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novel Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center p-4">
    <div class="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 mt-6">
        <header class="text-center mb-6">
            <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-500">
                Novel Hub 📖✨
            </h1>
            <p class="text-slate-400 text-sm mt-1">Sua central inteligente de leitura e áudio</p>
        </header>

        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Nome da Novel ou Link:</label>
                <input type="text" id="novelInput" placeholder="Ex: Shadow Slave - Capítulo 1" 
                    class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button onclick="buscarNovel()" id="btnBuscar"
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold py-3 rounded-xl shadow-lg hover:opacity-90 transition">
                🚀 Buscar e Gerar Áudio
            </button>
        </div>

        <div id="loading" class="hidden text-center my-6">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
            <p class="text-slate-400 text-sm mt-2">Processando texto e gerando áudio...</p>
        </div>

        <div id="resultado" class="mt-6 hidden space-y-4">
            <h2 class="text-lg font-bold text-blue-400">Resultado:</h2>
            <div id="textoGerado" class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-300 max-h-60 overflow-y-auto whitespace-pre-wrap"></div>
            
            <!-- PLAYER DE ÁUDIO -->
            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                <p class="text-xs text-slate-400 mb-2">Ouça a narração:</p>
                <audio id="audioPlayer" controls class="w-full"></audio>
            </div>
        </div>
    </div>

    <script>
        async function buscarNovel() {
            const query = document.getElementById('novelInput').value;
            if (!query) {
                alert('Por favor, digite o nome ou link da novel!');
                return;
            }

            const btn = document.getElementById('btnBuscar');
            const loading = document.getElementById('loading');
            const resultado = document.getElementById('resultado');
            const textoGerado = document.getElementById('textoGerado');
            const audioPlayer = document.getElementById('audioPlayer');

            btn.disabled = true;
            loading.classList.remove('hidden');
            resultado.classList.add('hidden');

            try {
                const response = await fetch('/api/processar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                
                textoGerado.innerText = data.resposta;
                audioPlayer.src = '/api/audio?t=' + new Date().getTime();
                resultado.classList.remove('hidden');
            } catch (error) {
                alert('Oops, ocorreu um erro: ' + error);
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
    
    if not query:
        return jsonify({"resposta": "Nenhuma consulta foi enviada."}), 400

    try:
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        prompt = (
            f"Traduza, adapte e resuma o seguinte conteúdo de novel para o português de forma fluída, "
