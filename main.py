from flask import Flask, render_template_string, request, jsonify, send_file
import os
import google.generativeai as genai
from gtts import gTTS
import io
import re

app = Flask(__name__)

# ============= CONFIGURAÇÕES =============
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ============= SISTEMA DE PERSONAGENS E VOZES =============
personagem_para_voz = {}

VOZES = [
    {"id": "narrador", "lang": "pt", "slow": False, "nome_exibicao": "Narrador (Padrão)"},
    {"id": "masculino_grave", "lang": "pt-pt", "slow": True, "nome_exibicao": "Masculina Grave"},
    {"id": "feminina_aguda", "lang": "pt-br", "slow": False, "nome_exibicao": "Feminina Leve"},
    {"id": "jovem_rapida", "lang": "pt", "slow": False, "nome_exibicao": "Jovem Animada"},
    {"id": "calma_madura", "lang": "pt-pt", "slow": True, "nome_exibicao": "Calma e Séria"},
    {"id": "forte_imponente", "lang": "pt-br", "slow": True, "nome_exibicao": "Forte e Profunda"},
]

indice_proxima_voz = 0
texto_gerado_ia = ""
audio_completo = None
dados_novel = {}

# ============= FUNÇÕES AUXILIARES =============
def extrair_personagem(linha_texto):
    match = re.match(r"^(.*?):\s*(.*)$", linha_texto.strip())
    if match:
        nome = match.group(1).strip()
        fala = match.group(2).strip()
        if nome and len(nome) < 30 and nome.lower() not in ["narrador", "narração", "descricao", "ação"]:
            return nome, fala
    return None, linha_texto.strip()

def obter_voz_para_personagem(nome_personagem):
    global personagem_para_voz, indice_proxima_voz
    if nome_personagem in personagem_para_voz:
        return personagem_para_voz[nome_personagem]
    
    indice = (indice_proxima_voz % (len(VOZES) - 1)) + 1
    voz_escolhida = VOZES[indice]
    personagem_para_voz[nome_personagem] = voz_escolhida
    indice_proxima_voz += 1
    return voz_escolhida

def gerar_audio_para_texto(texto, voz_info):
    if not texto or not texto.strip():
        return None
    try:
        tts = gTTS(text=texto, lang=voz_info["lang"], slow=voz_info["slow"])
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
            trecho = gerar_audio_para_texto(fala, voz)
            if trecho: trechos_audio.append(trecho)
        else:
            trecho = gerar_audio_para_texto(linha, VOZES[0])
            if trecho: trechos_audio.append(trecho)
    
    if trechos_audio:
        audio_completo = juntar_audios(trechos_audio)
        return True
    return False

# ============= BUSCA NA WEB COM GEMINI =============
def pesquisar_novel_na_web(nome_novel):
    global dados_novel
    try:
        modelo = genai.GenerativeModel("gemini-3.6-flash")
        
        prompt = f"""
Você é um pesquisador de novels experiente. O usuário procura por: '{nome_novel}'.

Responda SEMPRE neste formato exato, sem usar asteriscos ou marcadores:

TITULO: Nome completo da novel
AUTOR: Nome do autor
STATUS: Em andamento / Completo / Hiato
GENERO: Ação, Fantasia, Romance, etc.
SINOPSE: Breve resumo em 2-3 frases
HISTORIA:
Escreva um capítulo ou trecho envolvente com no mínimo 300 palavras.
Crie 3 a 4 personagens com nomes próprios falando várias vezes.
Use SEMPRE: "Nome do Personagem: o que ele disse"
A narração normal vai direto, sem rótulo.
"""
        
        resposta = modelo.generate_content(prompt)
        texto_resposta = resposta.text
        
        dados = {}
        padroes = {
            "titulo": r"TITULO:\s*(.*)",
            "autor": r"AUTOR:\s*(.*)",
            "status": r"STATUS:\s*(.*)",
            "genero": r"GENERO:\s*(.*)",
            "sinopse": r"SINOPSE:\s*(.*?)(?=HISTORIA:|$)",
            "historia": r"HISTORIA:\s*(.*)"
        }
        
        for chave, padrao in padroes.items():
            m = re.search(padrao, texto_resposta, re.DOTALL)
            if m:
                dados[chave] = m.group(1).strip()
        
        dados_novel = dados
        return dados.get("historia", texto_resposta), None
    except Exception as e:
        return None, f"Erro: {str(e)}"

# ============= PÁGINA WEB BONITA =============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel — Áudio & Narração</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        
        body { 
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); 
            min-height: 100vh;
        }
        
        .gradient-text { 
            background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
        }
        
        .card-glow { 
            background: rgba(30, 41, 59, 0.7); 
            backdrop-filter: blur(12px); 
            border: 1px solid rgba(96, 165, 250, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        }
        
        .card-glow:hover { 
            border-color: rgba(96, 165, 250, 0.4); 
            box-shadow: 0 12px 40px rgba(96, 165, 250, 0.15);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            transition: all 0.3s ease;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        }
        
        .capa-card {
            background: linear-gradient(135deg, #1e40af, #7c3aed);
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.25);
        }
        
        .fala { 
            border-left: 3px solid #a78bfa; 
            background: rgba(167, 139, 250, 0.08);
        }
        
        .loading-dot { animation: pulse 1.4s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
        
        .player-custom {
            background: rgba(30, 64, 175, 0.2);
            border: 1px solid rgba(96, 165, 250, 0.3);
        }
    </style>
</head>
<body class="text-gray-100">
    <!-- Cabeçalho -->
    <header class="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-lg border-b border-blue-500/20">
        <div class="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text flex items-center gap-2">
                <i class="fas fa-book-open text-blue-400"></i>
                Central Novel
            </h1>
            <span class="hidden md:flex items-center gap-2 text-sm text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full">
                <i class="fas fa-circle text-xs animate-pulse"></i>
                Busca & Vozes Ativas
            </span>
        </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <!-- Área de Busca -->
        <section class="card-glow rounded-2xl p-7">
            <h2 class="text-xl font-semibold mb-5 flex items-center gap-2">
                <i class="fas fa-search text-blue-400"></i>
                Encontrar Novel
            </h2>
            
            <label class="block text-sm font-medium text-gray-300 mb-2">
                Nome da novel, autor ou capítulo:
            </label>
            <input 
                type="text" 
                id="consulta" 
                placeholder="Ex: Shadow Slave, The Beginning After The End..."
                class="w-full bg-slate-800/60 border border-slate-600 rounded-xl px-5 py-4 mb-4 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
            
            <button 
                onclick="buscarNovel()" 
                class="w-full btn-primary text-white font-semibold py-4 rounded-xl text-lg"
            >
                <i class="fas fa-magic mr-2"></i>
                Buscar e Criar Narração
            </button>
        </section>

        <!-- Carregando -->
        <div id="loading" class="hidden text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mb-4"></div>
            <p class="text-gray-400 text-lg" id="statusTexto">Preparando...</p>
        </div>

        <!-- Resultado -->
        <section id="resultado" class="hidden space-y-6">
            <h2 class="text-xl font-bold text-emerald-400 flex items-center gap-2">
                <i class="fas fa-check-circle"></i>
                Encontrado!
            </h2>
            
            <!-- Capa e Dados -->
            <div class="card-glow rounded-2xl p-6">
                <div class="flex flex-col md:flex-row gap-6">
                    <!-- Capa -->
                    <div class="capa-card w-full md:w-40 h-56 rounded-xl flex items-center justify-center text-5xl shadow-lg">
                        <i class="fas fa-book text-white/90"></i>
                    </div>
                    
                    <!-- Info -->
                    <div class="flex-1 space-y-3">
                        <h3 class="text-2xl font-bold text-white" id="res-titulo">—</h3>
                        
                        <div class="grid grid-cols-2 gap-3 text-sm">
                            <div>
                                <span class="text-gray-400">Autor:</span>
                                <span class="ml-2 font-medium" id="res-autor">—</span>
                            </div>
                            <div>
                                <span class="text-gray-400">Status:</span>
                                <span class="ml-2 font-medium text-emerald-400" id="res-status">—</span>
                            </div>
                            <div class="col-span-2">
                                <span class="text-gray-400">Gênero:</span>
                                <span class="ml-2 font-medium text-blue-300" id="res-genero">—</span>
                            </div>
                        </div>
                        
                        <div class="mt-2">
                            <span class="text-gray-400 text-sm">Sinopse:</span>
                            <p class="text-gray-300 mt-1" id="res-sinopse">—</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- História -->
            <div class="card-glow rounded-2xl p-6">
                <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
                    <i class="fas fa-book-reader text-blue-400"></i>
                    História
                </h3>
                <div id="textoSaida" class="whitespace-pre-wrap text-gray-200 leading-relaxed space-y-2"></div>
            </div>

            <!-- Áudio -->
            <div class="card-glow rounded-2xl p-6">
                <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
                    <i class="fas fa-volume-up text-blue-400"></i>
                    Ouvir Narração
                </h3>
                <audio id="player" controls class="w-full rounded-lg player-custom">
                    Seu navegador não suporta áudio.
                
            </div>

            <!-- Personagens -->
            <div class="card-glow rounded-2xl p-6">
                <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
                    <i class="fas fa-users text-yellow-400"></i>
                    Personagens & Vozes
                </h3>
                <div id="listaPersonagens" class="space-y-3"></div>
                <p class="text-xs text-gray-500 mt-4">
                    💡 Cada personagem mantém a MESMA voz sempre — consistência garantida ✅
                </p>
            </div>
        </section>
    </main>

    <script>
        async function buscarNovel() {
            const consulta = document.getElementById("consulta").value;
            if (!consulta.trim()) return alert("Digite o nome da novel!");

            const loading = document.getElementById("loading");
            const resultado = document.getElementById("resultado");
            
            loading.classList.remove("hidden");
            resultado.classList.add("hidden");

            try {
                document.getElementById("statusTexto").innerText = "🔍 Buscando informações...";
                
                const resp = await fetch("/api/buscar-novel", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ nome: consulta })
                });
                
                const dados = await resp.json();
                if (dados.erro) throw new Error(dados.erro);

                // Preencher dados da capa
                document.getElementById("res-titulo").innerText = dados.info?.titulo || "—";
                document.getElementById("res-autor").innerText = dados.info?.autor || "—";
                document.getElementById("res-status").innerText = dados.info?.status || "—";
                document.getElementById("res-genero").innerText = dados.info?.genero || "—";
                document.getElementById("res-sinopse").innerText = dados.info?.sinopse || "—";
                
                // Texto formatado
                document.getElementById("textoSaida").innerText = dados.texto;

                // Gerar áudio
                document.getElementById("statusTexto").innerText = "🎙️ Criando vozes diferentes...";
                await fetch("/api/gerar-audio", { method: "POST" });

                // Carregar player
                document.getElementById("player").src = "/api/baixar-audio?t=" + Date.now();
                
                // Listar personagens
                await carregarPersonagens();

                resultado.classList.remove("hidden");
                resultado.scrollIntoView({ behavior: "smooth" });

            } catch (erro) {
                alert("Erro: " + erro.message);
            } finally {
                loading.classList.add("hidden");
            }
        }

        async function carregarPersonagens() {
            const resp = await fetch("/api/personagens");
            const dados = await resp.json();
            const lista = document.getElementById("listaPersonagens");
            lista.innerHTML = "";
            
            if (!dados.lista || dados.lista.length === 0) {
                lista.innerHTML = "<p class='text-gray-400'>Apenas narração.</p>";
                return;
            }
            
            dados.lista.forEach(p => {
                lista.innerHTML += `
                <div class="flex justify-between items-center py-3 px-4 bg-slate-800/50 rounded-xl border border
                
