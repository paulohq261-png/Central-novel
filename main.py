from flask import Flask, render_template_string, request, send_file
import os
import re
import io
import requests
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import tempfile
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🎭 VOZES DISPONÍVEIS
VOZES = {
    "narrador": {"nome": "Narrador", "prefixo": "", "cor": "#d4bfff"},
    "heroi": {"nome": "Herói", "prefixo": "Com determinação: ", "cor": "#90ee90"},
    "heroina": {"nome": "Heroína", "prefixo": "Com voz suave: ", "cor": "#87ceeb"},
    "vilao": {"nome": "Vilão", "prefixo": "Com tom sombrio: ", "cor": "#ff6b6b"},
    "sabio": {"nome": "Sábio", "prefixo": "Com calma e sabedoria: ", "cor": "#ffd700"},
    "crianca": {"nome": "Criança", "prefixo": "Com voz leve: ", "cor": "#ffb6c1"},
    "narrador_profundo": {"nome": "Narrador Sério", "prefixo": "Com tom solene: ", "cor": "#b8a9ff"}
}

# 🎨 ESTILOS VISUAIS
ESTILOS = {
    "fantasia_epica": {
        "nome": "Fantasia Épica",
        "cor1": "#1a1a3e", "cor2": "#2d1b69", "texto": "#e0d0ff",
        "desc": "Céus estrelados, reinos mágicos"
    },
    "sombrio_misterio": {
        "nome": "Sombrio e Misterioso",
        "cor1": "#0f0f1a", "cor2": "#1a1a2e", "texto": "#a0a0c0",
        "desc": "Noite, segredos, perigo"
    },
    "aventura_brilhante": {
        "nome": "Aventura Brilhante",
        "cor1": "#1e3a5f", "cor2": "#2a5298", "texto": "#ffd700",
        "desc": "Sol, jornada, esperança"
    },
    "romance_doce": {
        "nome": "Romance Doce",
        "cor1": "#3d1f3d", "cor2": "#5a2f5a", "texto": "#ffd0e0",
        "desc": "Afeto, momentos ternos"
    },
    "acao_energia": {
        "nome": "Ação e Energia",
        "cor1": "#2b1010", "cor2": "#501a1a", "texto": "#ffcc00",
        "desc": "Batalhas, movimento, tensão"
    }
}

# 📄 INTERFACE COMPLETA
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovelVision — Transforme Leitura em Vídeo 🎬</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
    <style>
        :root {--bg: #080810; --card: #121224; --accent: #a855f7; --texto: #e5e7eb;}
        body {background: var(--bg); color: var(--texto); font-family: sans-serif;}
        .card {background: var(--card); border: 1px solid rgba(168, 85, 247, 0.2);}
        .btn {background: linear-gradient(90deg, #a855f7, #ec4899); transition: transform 0.2s;}
        .btn:hover {opacity: 0.9; transform: scale(1.02);}
        .btn-secundario {background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4);}
        .aba {transition: all 0.2s;}
        .aba.ativa {background: rgba(168, 85, 247, 0.2); border-bottom: 2px solid #a855f7;}
        @keyframes rodar {to {transform: rotate(360deg);}}
        .carregando {animation: rodar 1s linear infinite;}
    </style>
</head>
<body class="min-h-screen p-4">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-bold text-center mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            🎬 NovelVision
        </h1>
        <p class="text-center text-gray-400 mb-8">Transforme capítulos de webnovel em vídeo para assistir</p>

        <!-- ABAS -->
        <div class="flex mb-6 rounded-lg overflow-hidden">
            <button class="aba ativa flex-1 py-3 px-4 font-bold" onclick="mudarAba('texto')" id="aba_texto">
                <i class="fa-solid fa-pen-to-square mr-2"></i>Colar Texto
            </button>
            <button class="aba flex-1 py-3 px-4 font-bold text-gray-400" onclick="mudarAba('busca')" id="aba_busca">
                <i class="fa-solid fa-globe mr-2"></i>Buscar Novel
            </button>
        </div>

        <!-- ABA: COLAR TEXTO -->
        <div id="painel_texto">
            <div class="card rounded-xl p-5 mb-6">
                <h2 class="font-bold text-lg mb-3">📖 Cole o capítulo</h2>
                <textarea id="texto" rows="10" class="w-full p-4 rounded-lg bg-gray-900/50 border border-purple-500/30 focus:border-purple-400 outline-none"
                placeholder="Cole o texto do capítulo aqui...&#10;&#10;Formato:&#10;**Narrador:** Texto da história&#10;**Nome:** Fala do personagem">
**Narrador:** O sol se punha sobre as torres de Eldoria. O céu brilhava em tons de roxo e ouro.

**Lira:** Kael, olha para o horizonte. Há algo estranho na névoa.

**Kael:** Eu sinto isso há horas. O selo está enfraquecendo.

**Narrador:** Naquela noite, decidiram partir. Ninguém sabia o que encontrariam, mas não havia escolha.

**Lira:** Não vamos recuar agora.

**Kael:** Juntos, chegaremos ao fim.
                </textarea>
            </div>
        </div>

        <!-- ABA: BUSCAR NOVEL -->
        <div id="painel_busca" class="hidden">
            <div class="card rounded-xl p-5 mb-6">
                <h2 class="font-bold text-lg mb-3">🔍 Buscar capítulo na web</h2>
                <p class="text-sm text-gray-400 mb-3">Cole o link do capítulo ou digite o nome da novel</p>
                <input type="text" id="link_busca" placeholder="Ex: centralnovel.com/nome-do-capitulo"
                    class="w-full p-3 rounded-lg bg-gray-900/50 border border-purple-500/30 focus:border-purple-400 outline-none mb-3">
                <button onclick="buscarCapitulo()" class="btn-secundario w-full py-3 rounded-lg font-bold">
                    <i class="fa-solid fa-magnifying-glass mr-2"></i>Buscar Capítulo
                </button>
                <div id="resultado_busca" class="mt-4 hidden">
                    <h3 class="font-bold text-green-400 mb-2">✅ Capítulo encontrado!</h3>
                    <textarea id="texto_busca" rows="8" class="w-full p-3 rounded-lg bg-gray-900/50 border border-green-500/30 mb-3"></textarea>
                    <button onclick="usarTextoBuscado()" class="btn w-full py-2 rounded-lg font-bold">
                        <i class="fa-solid fa-check mr-2"></i>Usar este capítulo
                    </button>
                </div>
            </div>
        </div>

        <!-- CONFIGURAÇÕES -->
        <div class="card rounded-xl p-5 mb-6">
            <h2 class="font-bold text-lg mb-3">⚙️ Configurações do vídeo</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="text-sm text-gray-400">Formato do vídeo</label>
                    <select id="formato" class="w-full mt-1 p-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                        <option value="vertical">📱 Vertical 9:16 (TikTok/Reels)</option>
                        <option value="paisagem">📺 Paisagem 16:9 (YouTube)</option>
                        <option value="quadrado">⬜ Quadrado 1:1</option>
                    </select>
                </div>
                <div>
                    <label class="text-sm text-gray-400">Estilo visual</label>
                    <select id="estilo" class="w-full mt-1 p-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                        <option value="fantasia_epica">🏰 Fantasia Épica</option>
                        <option value="sombrio_misterio">🌙 Sombrio e Misterioso</option>
                        <option value="aventura_brilhante">☀️ Aventura Brilhante</option>
                        <option value="romance_doce">💕 Romance Doce</option>
                        <option value="acao_energia">⚔️ Ação e Energia</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="text-sm text-gray-400">Voz padrão para personagens não identificados</label>
                <select id="voz_padrao" class="w-full mt-1 p-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                    <option value="narrador">Narrador</option>
                    <option value="heroina">Heroína</option>
                    <option value="heroi">Herói</option>
                    <option value="sabio">Sábio</option>
                </select>
            </div>
        </div>

        <!-- BOTÃO PRINCIPAL -->
        <button onclick="criarVideo()" class="btn w-full py-4 rounded-xl font-bold text-lg mb-6">
            <i class="fa-solid fa-film mr-2"></i> 🎬 Criar Vídeo Agora
        </button>

        <!-- STATUS -->
        <div id="status" class="hidden card rounded-xl p-5 text-center">
            <i class="fa-solid fa-spinner carregando text-2xl text-purple-400 mb-3"></i>
            <p id="texto_status">Processando capítulo...</p>
            <div class="w-full bg-gray-800 rounded-full h-2 mt-3">
                <div id="barra_progresso" class="bg-purple-500 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
            </div>
        </div>

        <!-- RESULTADO -->
        <div id="resultado" class="hidden card rounded-xl p-5 text-center">
            <i class="fa-solid fa-check-circle text-3xl text-green-400 mb-3"></i>
            <h3 class="font-bold text-lg mb-2">🎉 Vídeo Pronto!</h3>
            <video id="player_video" controls class="w-full rounded-lg mb-4 bg-black"></video>
            <a id="link_download" class="btn inline-block px-6 py-3 rounded-xl font-bold" download="novel_capitulo.mp4">
                <i class="fa-solid fa-download mr-2"></i> Baixar Vídeo .MP4
            </a>
        </div>
    </div>

<script>
function mudarAba(nome){
    document.querySelectorAll('.aba').forEach(a=>a.classList.remove('ativa', 'text-white'));
    document.querySelectorAll('.aba').forEach(a=>a.classList.add('text-gray-400'));
    document.getElementById('aba_'+nome).classList.add('ativa', 'text-white');
    document.getElementById('aba_'+nome).classList.remove('text-gray-400');
    
    document.getElementById('painel_texto').classList.toggle('hidden', nome!=='texto');
    document.getElementById('painel_busca').classList.toggle('hidden', nome!=='busca');
}

async function buscarCapitulo(){
    const link = document.getElementById('link_busca').value.trim();
    if(!link){alert('Digite um link ou nome!'); return;}
    
    document.getElementById('resultado_busca').classList.add('hidden');
    
    const resp = await fetch('/buscar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({link})
    });
    
    const dados = await resp.json();
    if(dados.sucesso){
        document.getElementById('texto_busca').value = dados.texto;
        document.getElementById('resultado_busca').classList.remove('hidden');
    }else{
        alert('Não foi possível buscar: ' + dados.erro);
    }
}

function usarTextoBuscado(){
    document.getElementById('texto').value = document.getElementById('texto_busca').value;
    mudarAba('texto');
    alert('Capítulo carregado! Agora é só criar o vídeo 🎬');
}

async function criarVideo(){
    const texto = document.getElementById('texto').value.trim();
    if(!texto){alert('Cole ou busque um capítulo primeiro!'); return;}

    document.getElementById('status').classList.remove('hidden');
    document.getElementById('resultado').classList.add('hidden');
    document.getElementById('barra_progresso').style.width = '5%';
    document.getElementById('texto_status').textContent = 'Preparando...';

    try{
        const resp = await fetch('/gerar-video', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texto: texto,
                formato: document.getElementById('formato').value,
                estilo: document.getElementById('estilo').value,
                voz_padrao: document.getElementById('voz_padrao').value
            })
        });

        document.getElementById('barra_progresso').style.width = '40%';
        document.getElementById('texto_status').textContent = 'Gerando narração...';

        const blob = await resp.blob();

        document.getElementById('barra_progresso').style.width = '100%';
        document.getElementById('texto_status').textContent = 'Pronto! 🎉';

        setTimeout(()=>{
            document.getElementById('status').classList.add('hidden');
            document.getElementById('resultado').classList.remove('hidden');
            const url = URL.createObjectURL(blob);
            document.getElementById('player_video').src = url;
            document.getElementById('link_download').href = url;
        }, 600);
    }catch(erro){
        alert('Erro: ' + erro);
        document.getElementById('status').classList.add('hidden');
    }
}
</script>
</body>
</html>
"""

# 🎨 CRIAR IMAGEM DE FUNDO
def criar_imagem(texto_cena, estilo_nome, larg, alt):
    estilo = ESTILOS.get(estilo_nome, ESTILOS["fantasia_epica"])
    c1 = estilo["cor1"]
    c2 = estilo["cor2"]
    cor_texto = estilo["texto"]

    img = Image.new("RGB", (larg, alt), c1)
    draw = ImageDraw.Draw(img)

    # Gradiente vertical
    r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    
    for y in range(alt):
        f = y / alt
        r = int(r1 + (r2 - r1) * f)
        g = int(g1 + (g2 - g1) * f)
        b = int(b1 + (b2 - b1) * f)
        draw.line([(0, y), (larg, y)], fill=(r, g, b))

    # Fonte
    try:
        if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(24, int(larg / 22)))
        else:
            fonte = ImageFont.load_default()
    except:
        fonte = ImageFont.load_default()

    # Quebrar texto em linhas
    linhas = []
    linha_atual = ""
    for palavra in texto_cena.split():
        teste = f"{linha_atual} {palavra}".strip()
        if draw.textlength(teste, fonte) > larg * 0.9:
            linhas.append(linha_atual)
            linha_atual = palavra
        else:
            linha_atual = teste
    if linha_atual:
        linhas.append(linha_atual)

    # Centralizar
    espaco_entre_linhas = int(alt / 18)
    total_linhas = len(linhas) * espaco_entre_linhas
    y = (alt - total_linhas) / 2.5

    for linha in linhas:
        w = draw.textlength(linha, fonte)
        draw.text(((larg - w) / 2, y), linha, fill=cor_texto, font=fonte)
        y += espaco_entre_linhas

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return buf

# 🔍 BUSCAR CAPÍTULO NA WEB
@app.route("/buscar", methods=["POST"])
def buscar_capitulo():
    dados = request.get_json()
    link = dados.get("link", "").strip()
    
    if not link.startswith("http"):
        link = f"https://{link}"
    
    try:
        cabecalhos = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(link, headers=cabecalhos, timeout=15)
        
        if resp.status_code != 200:
            return {"sucesso": False, "erro": f"Não consegui acessar (código {resp.status_code})"}
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove elementos que não são texto
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        texto = soup.get_text(separator="\n", strip=True)
        
        # Limpa linhas vazias repetidas
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        texto_limpo = "\n\n".join(linhas[:100])  # Limita tamanho
        
        if len(texto_limpo) < 50:
            return {"sucesso": False, "erro": "Conteúdo muito curto ou não encontrado"}
        
        return {"sucesso": True, "texto": texto_limpo}
    
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

# 🎬 GERAR VÍDEO
@app.route("/gerar-video", methods=["POST"])
def gerar_video():
    dados = request.get_json()
    texto = dados.get("texto", "")
    formato = dados.get("formato", "vertical")
    estilo = dados.get("estilo", "fantasia_epica")
    voz_padrao = dados.get("voz_padrao", "narrador")

    # Dimensões
    dimensoes = {
        "vertical": (1080, 1920),
        "paisagem": (1920, 1080),
        "quadrado": (1080, 1080)
    }
    largura, altura = dimensoes.get(formato, (1080, 1920))

    # Extrair falas no formato **Nome:** Texto
    padrao = re.compile(r"\*\*([^*]+?)\*\*:\s*(.+?)(?=\n\s*\n|\Z)", re.DOTALL)
    trechos = padrao.findall(texto)

    if not trechos:
        # Se não tiver formato, usa tudo como narrador
        trechos = [("Narrador", texto)]

    clips = []
    pasta_temp = tempfile.TemporaryDirectory()

    try:
        for indice, (nome_pessoa, fala) in enumerate(trechos):
            # Define voz
            chave_voz = nome_pessoa.lower().strip()
            if chave_voz not in VOZES:
                chave_voz = voz_padrao
            configuracao_voz = VOZES[chave_voz]

            # Gera áudio
            texto_audio = f"{configuracao_voz['prefixo']}{fala}".strip()
            tts = gTTS(text=texto_audio, lang="pt-BR", slow=False)
            caminho_audio = f"{pasta_temp.name}/audio_{indice}.mp3"
            tts.save(caminho_audio)
            clip_audio = AudioFileClip(caminho_audio)

            # Gera imagem
            texto_imagem = f"{nome_pessoa}: {fala[:70]}..."
            buffer_imagem = criar_imagem(texto_imagem, estilo, largura, altura)
            caminho_imagem = f"{pasta_temp.name}/imagem_{indice}.jpg"
            with open(caminho_imagem, "wb") as f:
                f.write(buffer_imagem.read())
            
            clip_imagem = ImageClip(caminho_imagem).set_duration(clip_audio.duration)
            clip_final = clip_imagem.set_audio(clip_audio)
            clips.append(clip_final)

        # Junta tudo
        video_completo = concatenate_videoclips(clips, method="compose")
        caminho_video = f"{pasta_temp.name}/capitulo_video.mp4"
        
        video_completo.write_videofile(
            caminho_video,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )

        # Lê e envia
        with open(caminho_video, "rb") as f:
            saida = io.BytesIO(f.read())
        saida.seek(0)

        return send_file(
            saida,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="novel_capitulo_video.mp4"
        )

    finally:
        pasta_temp.cleanup()

@app.route("/")
def pagina_inicial():
    return render_template_string(HTML)

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=porta)
