from flask import Flask, render_template_string, request, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dola Novel Hub - Gemini</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center p-4">
    <div class="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 mt-6">
        <header class="text-center mb-6">
            <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-500">
                Dola Novel Hub 🎙️✨
            </h1>
            <p class="text-slate-400 text-sm mt-1">Central Inteligente de Leitura e Áudio</p>
        </header>

        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Nome da Novel ou Link:</label>
                <input type="text" id="novelInput" placeholder="Ex: Shadow Slave - Capítulo 1" 
                    class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button onclick="buscarNovel()" id="btnBuscar"
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold py-3 rounded-xl shadow-lg hover:opacity-90 transition">
                🚀 Buscar e Processar Capítulo
            </button>
        </div>

        <div id="loading" class="hidden text-center my-6">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
            <p class="text-slate-400 text-sm mt-2">Dola está buscando e traduzindo para você...</p>
        </div>

        <div id="resultado" class="mt-6 hidden">
            <h2 class="text-lg font-bold text-blue-400 mb-2">Resultado:</h2>
            <div id="textoGerado" class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-300 max-h-60 overflow-y-auto whitespace-pre-wrap"></div>
            
            <!-- BOTÃO DE ÁUDIO -->
            <div class="mt-4 flex gap-3">
                <button onclick="falarTexto()" id="btnFalar"
                    class="flex-1 bg-green-600 hover:bg-green-500 text-white font-semibold py-3 rounded-xl transition flex items-center justify-center gap-2">
                    🔊 Ouvir Dola
                </button>
                <button onclick="pararFala()" id="btnParar"
                    class="bg-red-600 hover:bg-red-500 text-white font-semibold py-3 px-4 rounded-xl transition hidden">
                    ⏹️
                </button>
            </div>
        </div>
    </div>

    <script>
        let utteranceAtual = null;

        async function buscarNovel() {
            const query = document.getElementById('novelInput').value;
            if (!query) {
                alert('Por favor, digite o nome ou link da novel!');
                return;
            }

            pararFala(); // Para qualquer áudio anterior

            const btn = document.getElementById('btnBuscar');
            const loading = document.getElementById('loading');
            const resultado = document.getElementById('resultado');
            const textoGerado = document.getElementById('textoGerado');
            const btnParar = document.getElementById('btnParar');
            btnParar.classList.add('hidden');

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
                resultado.classList.remove('hidden');
            } catch (error) {
                alert('Oops, ocorreu um erro: ' + error);
            } finally {
                btn.disabled = false;
                loading.classList.add('hidden');
            }
        }

        function falarTexto() {
            const texto = document.getElementById('textoGerado').innerText;
            if (!texto) return;

            pararFala();

            utteranceAtual = new SpeechSynthesisUtterance(texto);
            utteranceAtual.lang = 'pt-BR';
            utteranceAtual.rate = 1.0; // Velocidade normal
            utteranceAtual.pitch = 1.1; // Voz mais suave

            // Tenta usar uma voz feminina em português
            const vozes = window.speechSynthesis.getVoices();
            const vozDola = vozes.find(v => v.lang === 'pt-BR' && v.name.includes('Feminina') || v.name.includes('Google')) || vozes.find(v => v.lang === 'pt-BR');
            if (vozDola) utteranceAtual.voice = vozDola;

            utteranceAtual.onstart = () => {
                document.getElementById('btnParar').classList.remove('hidden');
            };
            utteranceAtual.onend = () => {
                document.getElementById('btnParar').classList.add('hidden');
            };

            window.speechSynthesis.speak(utteranceAtual);
        }

        function pararFala() {
            window.speechSynthesis.cancel();
            utteranceAtual = null;
            document.getElementById('btnParar').classList.add('hidden');
        }

        // Carrega as vozes quando o navegador estiver pronto
        window.speechSynthesis.onvoiceschanged = () => {};
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
            f"Você é a Dola, especialista em novels, tradução e narração. "
            f"O usuário pediu: '{query}'. "
            f"Faça um resumo envolvente e um trecho em português fluido, com tom de narração, "
            f"curto e direto, ideal para leitura em voz."
        )
        
        resposta = model.generate_content(prompt)
        return jsonify({"resposta": resposta.text})
        
    except Exception as e:
        return jsonify({"resposta": f"Erro: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
