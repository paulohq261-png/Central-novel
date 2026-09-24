from flask import Flask, render_template_string, request, jsonify, send_file
import os
import google.generativeai as genai
from gtts import gTTS
import io
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ============= CONFIGURAÇÕES =============
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ============= SISTEMA DE PERSONAGENS =============
personagem_para_voz = {}
vozes_disponiveis = [
    "voz_narrador",
    "voz_masculina_grave",
    "voz_feminina_aguda",
    "voz_jovem_animada",
    "voz_calma_madura",
    "voz_vilao_sombria"
]
indice_proxima_voz = 0

texto_gerado_ia = ""
audio_completo = None

# ============= FUNÇÃO DE PESQUISA NA WEB =============
def pesquisar_novel_na_web(nome_novel):
    try:
        modelo = genai.GenerativeModel("gemini-3.6-flash")
        
        prompt_pesquisa = f"""
Você é um pesquisador de novels experiente. O usuário procura por: '{nome_novel}'.

Faça o seguinte:
1. Busque informações sobre essa novel: sinopse, autor, status, capítulos principais.
2. Escreva um resumo detalhado e envolvente.
3. Se houver cenas ou diálogos importantes, formate assim:
   - Narração: texto normal
   - Fala de personagem: "Nome do Personagem: o que ele diz"
4. Crie de 2 a 4 personagens com falas naturais ao longo do texto.
5. Mantenha tudo em português brasileiro, fluido e bem estruturado.

Se não encontrar exatamente o nome, crie uma história no mesmo estilo.
"""
        
        resposta = modelo.generate_content(prompt_pesquisa)
        return resposta.text, None
        
    except Exception as e:
        return None, f"Erro na busca: {str(e)}"

# ============= FUNÇÕES DE ÁUDIO =============
def extrair_personagem(linha_texto):
    match = re.match(r"^(.*?):\s*(.*)$", linha_texto.strip())
    if match:
        nome = match.group(1).strip()
        fala = match.group(2).strip()
        if nome and len(nome) < 30 and nome.lower() not in ["narrador", "descricao", "acao"]:
            return nome, fala
    return None, linha_texto.strip()

def obter_voz_para_personagem(nome_personagem):
    global personagem_para_voz, indice_proxima_voz
    if nome_personagem in personagem_para_voz:
        return personagem_para_voz[nome_personagem]
    if vozes_disponiveis:
        voz = vozes_disponiveis[indice_proxima_voz % len(vozes_disponiveis)]
        personagem_para_voz[nome_personagem] = voz
        indice_proxima_voz += 1
        return voz
    return "voz_narrador"

def gerar_audio_para_texto(texto, tipo_voz="voz_narrador"):
    if not texto or not texto.strip():
        return None
    
    try:
        opcoes = {
            "voz_narrador": {"lang": "pt", "slow": False},
            "voz_masculina_grave": {"lang": "pt", "slow": True},
            "voz_feminina_aguda": {"lang": "pt-br", "slow": False},
            "voz_jovem_animada": {"lang": "pt", "slow": False},
            "voz_calma_madura": {"lang": "pt-pt", "slow": True},
            "voz_vilao_sombria": {"lang": "pt", "slow": True}
        }
        
        cfg = opcoes.get(tipo_voz, opcoes["voz_narrador"])
        
        tts = gTTS(text=texto, lang=cfg["lang"], slow=cfg["slow"])
        memoria = io.BytesIO()
        tts.write_to_fp(memoria)
        memoria.seek(0)
        return memoria
        
    except Exception as e:
        print(f"Erro TTS: {e}")
        return None

def juntar_audios(lista_audios):
    saida = io.BytesIO()
    for trecho in lista_audios:
        if trecho:
            trecho.seek(0)
            saida.write(trecho.read())
    saida.seek(0)
    return saida

def processar_texto_com_personagens(texto_completo):
    global audio_completo
    linhas = texto_completo.split("\n")
    trechos_audio = []

    for linha in linhas:
        if not linha.strip():
            continue
        
        personagem, fala = extrair_personagem(linha)
        
        if personagem:
            voz = obter_voz_para_personagem(personagem)
            texto_narrar = f"{personagem} diz: {fala}"
        else:
            voz = "voz_narrador"
            texto_narrar = linha
        
        trecho = gerar_audio_para_texto(texto_narrar, voz)
        if trecho:
            trechos_audio.append(trecho)
    
    if trechos_audio:
        audio_completo = juntar_audios(trechos_audio)
        return True
    return False

# ============= PÁGINA WEB =============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel — Busca e Narração</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body { background: #12121f; color: #e5e5e5; font-family: system-ui, sans-serif; }
        .card-hover:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
        .gradient-text { background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
</head>
<body class="min-h-screen">
    <header class="bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text">
                <i class="fas fa-book-open mr-2 text-blue-400"></i>Central Novel
            </h1>
            <span class="hidden md:inline text-sm text-green-400">
                <i class="fas fa-search-location mr-1"></i>Busca na Web Ativa 🌐
            </span>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <!-- ÁREA DE BUSCA -->
        <section class="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h2 class="text-xl font-bold mb-4"><i class="fas fa-search text-blue-400 mr-2"></i>Buscar Novel</h2>
            
            <label class="block text-sm font-medium text-slate-300 mb-2">Nome da novel, autor ou capítulo:</label>
            <input type="text" id="consulta" placeholder="Ex: Shadow Slave, The Beginning After The End..."
                class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg">

            <button onclick="buscarNovel()" 
                class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-lg font-medium transition text-lg">
                🔍 Buscar e Gerar Narração
            </button>
        </section>

        <!-- CARREGANDO -->
        <div id="loading" class="hidden text-center py-10">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent"></div>
            <p class="text-slate-400 mt-3" id="statusTexto">Buscando informações na web...</p>
        </div>

        <!-- RESULTADO -->
        <section id="resultado" class="hidden space-y-5">
            <h2 class="text-xl font-bold text-green-400"><i class="fas fa-check-double"></i> Encontrado!</h2>
            
            <div class="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h3 class="font-bold mb-2 text-slate-300">📖 Conteúdo:</h3>
                <div id="textoSaida" class="whitespace-pre-wrap text-slate-300 leading-relaxed"></div>
            </div>

            <div class="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h3 class="font-bold mb-3 text-blue-400"><i class="fas fa-volume-up"></i> 🔊 Ouvir Narração</h3>
                <audio id="player" controls class="w-full rounded-lg">
                    Seu navegador não suporta áudio.
                
            </div>

            <div class="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h3 class="font-bold mb-3 text-yellow-400"><i class="fas fa-users"></i> 🎭 Personagens Detectados</h3>
                <div id="listaPersonagens" class="text-sm text-slate-300 space-y-1"></div>
                <p class="text-xs text-slate-500 mt-3">💡 Cada personagem mantém sua voz sempre! ✅</p>
            </div>
        </section>
    </main>

    <script>
        async function buscarNovel() {
            const consulta = document.getElementById("consulta").value;
            if (!consulta) return alert("Digite o nome da novel!");

            const loading = document.getElementById("loading");
            const resultado = document.getElementById("resultado");
            const statusTexto = document.getElementById("statusTexto");
            
            loading.classList.remove("hidden");
            resultado.classList.add("hidden");

            try {
                statusTexto.innerText = "🌐 Buscando informações sobre a novel...";
                const respBusca = await fetch("/api/buscar-novel", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({nome: consulta})
                });
                const dados = await respBusca.json();
                
                if (dados.erro) throw new Error(dados.erro);
                
                document.getElementById("textoSaida").innerText = dados.texto;
                
                statusTexto.innerText = "🎙️ Criando vozes dos personagens...";
                await fetch("/api/gerar-audio", {method: "POST"});
                
                document.getElementById("player").src = "/api/baixar-audio?t=" + Date.now();
                await carregarPersonagens();
                
                resultado.classList.remove("hidden");
                resultado.scrollIntoView({behavior: "smooth"});

            } catch (erro) {
                alert("Erro: " + erro);
            } finally {
                loading.classList.add("hidden");
            }
        }

        async function carregarPersonagens() {
            const resp = await fetch("/api/personagens");
            const dados = await resp.json();
            const lista = document.getElementById("listaPersonagens");
            lista.innerHTML = "";
            
            if (dados.lista.length === 0) {
                lista.innerHTML = "<p class='text-slate-400'>Apenas narração.</p>";
                return;
            }
            
            dados.lista.forEach(p => {
                lista.innerHTML += `<div class="flex justify-between py-2 border-b border-slate-800">
                    <span class="font-medium">👤 ${p.nome}</span>
                    <span class="text-blue-400 text-xs">🎙️ ${p.voz.replace('_', ' ')}</span>
                </div>`;
            });
        }
    </script>
</body>
</html>
"""

# ============= ROTAS DA API =============
@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/buscar-novel", methods=["POST"])
def buscar_novel():
    global texto_gerado_ia, personagem_para_voz, indice_proxima_voz
    personagem_para_voz = {}
    indice_proxima_voz = 0

    dados = request.json
    nome_novel = dados.get("nome", "")
    
    if not nome_novel:
        return jsonify({"erro": "Digite o nome da novel!"}), 400
    
    texto, erro = pesquisar_novel_na_web(nome_novel)
    
    if erro:
        return jsonify({"erro": erro}), 500
    
    if not texto:
        return jsonify({"erro": "Não encontrei informações sobre essa novel."}), 404
    
    texto_gerado_ia = texto
    return jsonify({"texto": texto})

@app.route("/api/gerar-audio", methods=["POST"])
def rota_gerar_audio():
    global texto_gerado_ia
    if not texto_gerado_ia:
        return jsonify({"erro": "Sem texto para narrar"}), 400
    
    ok = processar_texto_com_personagens(texto_gerado_ia)
    if ok:
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Falha ao gerar áudio"}), 500

@app.route("/api/baixar-audio")
def baixar_audio():
    global audio_completo
    if not audio_completo:
        return "Áudio não encontrado", 404
    audio_completo.seek(0)
    return send_file(audio_completo, mimetype="audio/mpeg", download_name="novel.mp3")

@app.route("/api/personagens")
def listar_personagens():
    lista = [{"nome": nome, "voz": voz} for nome, voz in personagem_para_voz.items()]
    return jsonify({"lista": lista})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        
