from flask import Flask, render_template_string, request, jsonify, send_file
import os
import google.generativeai as genai
from gtts import gTTS
import io

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel — Sua Central de Leitura</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body { background: #12121f; color: #e5e5e5; font-family: system-ui, sans-serif; }
        .card-hover:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
        .gradient-text { background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
</head>
<body class="min-h-screen">
    <!-- CABEÇALHO -->
    <header class="bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text">
                <i class="fas fa-book-open mr-2 text-blue-400"></i>Central Novel
            </h1>
            <div class="hidden md:flex items-center gap-4">
                <div class="relative">
                    <input type="text" id="searchInput" placeholder="Buscar novel ou capítulo..."
                        class="bg-slate-800 border border-slate-700 rounded-full px-4 py-2 pl-10 w-72 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                    <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
                </div>
                <button onclick="buscarNovel()" class="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-full text-sm font-medium transition">
                    <i class="fas fa-magic mr-1"></i> Processar
                </button>
            </div>
            <button class="md:hidden text-xl"><i class="fas fa-bars"></i></button>
        </div>
        <!-- BANNER TELEGRAM -->
        <div class="bg-red-600 text-center py-2 text-sm font-medium">
            <a href="#" class="hover:underline"><i class="fab fa-telegram mr-1"></i> Participe do nosso grupo no Telegram!</a>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6 space-y-10">

        <!-- SEÇÃO DE BUSCA (MOBILE) -->
        <section class="md:hidden bg-slate-900 rounded-xl p-4 border border-slate-800">
            <input type="text" id="searchInputMobile" placeholder="Buscar novel ou capítulo..."
                class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <button onclick="buscarNovel()" class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-lg font-medium transition">
                🚀 Buscar e Gerar Áudio
            </button>
        </section>

        <!-- ESCOLHA DO EDITOR -->
        <section>
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-star text-yellow-400"></i> Escolha do Editor
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 card-hover transition">
                    <div class="flex">
                        <img src="https://picsum.photos/id/24/150/200" alt="Capa" class="w-28 h-36 object-cover">
                        <div class="p-3 flex-1">
                            <h3 class="font-bold text-lg">Tales of Demons & Gods</h3>
                            <p class="text-yellow-400 text-sm font-medium">2015</p>
                            <p class="text-slate-400 text-xs mt-1">Status: Em andamento</p>
                            <div class="flex gap-2 mt-2">
                                <span class="bg-blue-600/30 text-blue-300 text-xs px-2 py-1 rounded">Ação</span>
                                <span class="bg-orange-600/30 text-orange-300 text-xs px-2 py-1 rounded">Artes Marciais</span>
                            </div>
                        </div>
                        <div class="p-3 text-yellow-400 font-bold text-xl">7.6</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- TENDÊNCIAS DA SEMANA -->
        <section>
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-fire text-orange-500"></i> Tendências da Semana
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-slate-900 rounded-xl p-3 border border-slate-800 card-hover transition flex gap-3 relative">
                    <span class="absolute top-2 right-2 bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">9.4</span>
                    <img src="https://picsum.photos/id/42/100/140" alt="Capa" class="w-20 h-28 object-cover rounded-lg">
                    <div>
                        <h3 class="font-bold">The Beginning After The End</h3>
                        <p class="text-slate-400 text-xs mt-1">Dizem que a solidão acompanha aqueles com grande poder...</p>
                        <div class="flex gap-2 mt-2 flex-wrap">
                            <span class="bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded">Novel Ocidental</span>
                            <span class="bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded">Ação</span>
                        </div>
                    </div>
                </div>
                <div class="bg-slate-900 rounded-xl p-3 border border-slate-800 card-hover transition flex gap-3 relative">
                    <span class="absolute top-2 right-2 bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">9.56</span>
                    <img src="https://picsum.photos/id/43/100/140" alt="Capa" class="w-20 h-28 object-cover rounded-lg">
                    <div>
                        <h3 class="font-bold">Shadow Slave</h3>
                        <p class="text-slate-400 text-xs mt-1">Crescendo na pobreza, Sunny nunca esperou nada de bom...</p>
                        <div class="flex gap-2 mt-2 flex-wrap">
                            <span class="bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded">Novel Ocidental</span>
                            <span class="bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded">Ação</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- RESULTADO DO PROCESSAMENTO -->
        <section id="resultadoSecao" class="hidden">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2 text-blue-400">
                <i class="fas fa-sparkles"></i> Resultado
            </h2>
            <div class="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div id="textoGerado" class="text-slate-300 whitespace-pre-wrap leading-relaxed"></div>
                <div class="mt-5 pt-4 border-t border-slate-800">
                    <p class="text-xs text-slate-400 mb-2"><i class="fas fa-volume-up mr-1"></i> Ouça a narração:</p>
                    <audio id="audioPlayer" controls class="w-full rounded-lg">
                </div>
            </div>
        </section>

        <!-- CARREGANDO -->
        <div id="loading" class="hidden text-center py-10">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent"></div>
            <p class="text-slate-400 mt-3">Processando capítulo e gerando áudio...</p>
        </div>

        <!-- POPULARES HOJE -->
        <section>
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-chart-line text-blue-400"></i> Popular Hoje
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div class="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 card-hover transition">
                    <img src="https://picsum.photos/id/43/200/280" alt="Capa" class="w-full h-44 object-cover">
                    <div class="p-3">
                        <h3 class="font-bold text-sm truncate">Shadow Slave</h3>
                        <p class="text-slate-400 text-xs">Vol.13 Cap.3169</p>
                        <span class="inline-block mt-1 bg-green-600/20 text-green-400 text-xs px-2 py-0.5 rounded">Em andamento</span>
                    </div>
                </div>
                <div class="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 card-hover transition">
                    <img src="https://picsum.photos/id/44/200/280" alt="Capa" class="w-full h-44 object-cover">
                    <div class="p-3">
                        <h3 class="font-bold text-sm truncate">Lord of Mysteries</h3>
                        <p class="text-slate-400 text-xs">Vol.Extra Cap.1437</p>
                        <span class="inline-block mt-1 bg-blue-600/20 text-blue-400 text-xs px-2 py-0.5 rounded">Completo</span>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <script>
        async function buscarNovel() {
            const query = document.getElementById('searchInput').value || document.getElementById('searchInputMobile').value;
            if (!query) {
                alert('Digite o nome ou capítulo que deseja buscar!');
                return;
            }

            const loading = document.getElementById('loading');
            const resultadoSecao = document.getElementById('resultadoSecao');
            const textoGerado = document.getElementById('textoGerado');
            const audioPlayer = document.getElementById('audioPlayer');

            loading.classList.remove('hidden');
            resultadoSecao.classList.add('hidden');

            try {
                const response = await fetch('/api/processar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                textoGerado.innerText = data.resposta;
                audioPlayer.src = '/api/audio?t=' + new Date().getTime();
                resultadoSecao.classList.remove('hidden');
                resultadoSecao.scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                alert('Oops, ocorreu um erro: ' + error);
            } finally {
                loading.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

texto_atual = ""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/processar", methods=["POST"])
def processar():
    global texto_atual
    data = request.json
    query = data.get("query", "")
    
    if not query:
        return jsonify({"resposta": "Nenhuma consulta foi enviada."}), 400

    try:
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = (
            f"Você é um especialista em novels. O usuário pediu: '{query}'. "
            f"Faça um resumo envolvente com narração em português, fluido, natural e bem estruturado. "
            f"Inclua um trecho representativo do capítulo."
        )
        resposta = model.generate_content(prompt)
        texto_atual = resposta.text
        return jsonify({"resposta": texto_atual})
    except Exception as e:
        return jsonify({"resposta": f"Erro: {str(e)}"}), 500

@app.route("/api/audio")
def gerar_audio():
    global texto_atual
    if not texto_atual:
        return "Sem texto", 404
    
    tts = gTTS(text=texto_atual, lang='pt', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return send_file(fp, mimetype="audio/mpeg", download_name="narracao.mp3")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
