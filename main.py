from flask import Flask, render_template_string, request, jsonify, send_file
import os
import tempfile
import requests
from gtts import gTTS
from elevenlabs import ElevenLabs, save
from moviepy.editor import ImageClip, AudioFileClip

app = Flask(__name__)

# ========== CONFIGURAÇÕES ==========
from dotenv import load_dotenv
load_dotenv()

ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
eleven = ElevenLabs(api_key=ELEVEN_API_KEY) if ELEVEN_API_KEY else None
VOZ_NARRADOR = "pNInz6obpgDQGcFmaJgB"

# ========== NOME DO APP ==========
NOME_APP_CURTO = "CinePágina"
NOME_APP_COMPLETO = "CinePágina — Livro em Cena"
SLOGAN = "A alma da história ganha vida em cada cena"

# ========== GERAR CAPA ==========
def gerar_capa_url(titulo):
    prompt = f"capa de novel fantasia épica, {titulo}, herói e heroína, dragão, fênix, castelo, iluminação dramática, cores vibrantes, proporção 9:16, alta qualidade cinematográfica"
    return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=720&height=1280&nologo=true&quality=95"

# ========== GERAR ÁUDIO ==========
def criar_arquivo_audio(texto):
    try:
        if eleven and ELEVEN_API_KEY:
            audio = eleven.generate(text=texto, voice=VOZ_NARRADOR, model="eleven_multilingual_v2")
            caminho = tempfile.mktemp(suffix=".mp3")
            save(audio, caminho)
            return caminho
    except Exception as e:
        print(f"ElevenLabs falhou: {e}")
    caminho = tempfile.mktemp(suffix=".mp3")
    gTTS(texto, lang="pt-br").save(caminho)
    return caminho

# ========== MONTAR VÍDEO ==========
def criar_video_arquivo(imagem_url, caminho_audio):
    try:
        resp = requests.get(imagem_url, timeout=30)
        if resp.status_code != 200: return None
        img_temp = tempfile.mktemp(suffix=".jpg")
        with open(img_temp, "wb") as f: f.write(resp.content)
        
        clip_img = ImageClip(img_temp)
        clip_audio = AudioFileClip(caminho_audio)
        video = clip_img.set_duration(clip_audio.duration).set_audio(clip_audio)
        video_path = tempfile.mktemp(suffix=".mp4")
        video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        
        os.remove(img_temp)
        clip_audio.close()
        clip_img.close()
        return video_path
    except Exception as e:
        print(f"Erro vídeo: {e}")
        return None

# ========== PÁGINA PRINCIPAL ==========
@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + NOME_APP_COMPLETO + """</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0f051a, #1a0f2e, #0f1a2e); color: white; min-height: 100vh; }
        .font-title { font-family: 'Playfair Display', serif; }
        .logo-icon { background: linear-gradient(135deg, #ff9500, #7928ca); }
        .btn-grad { background: linear-gradient(90deg, #ff9500, #7928ca); transition: 0.3s; }
        .btn-grad:hover { transform: scale(1.03); box-shadow: 0 0 25px rgba(121,40,202,0.4); }
        .input { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); }
        .input:focus { border-color: #ff9500; outline: none; box-shadow: 0 0 0 3px rgba(255,149,0,0.2); }
        .capa { border-radius: 1rem; box-shadow: 0 0 40px rgba(121,40,202,0.2); }
        .spinner { border: 3px solid #ffffff33; border-top-color: #ff9500; border-radius: 50%; width: 28px; height: 28px; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .fade { animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
    </style>
</head>
<body>
    <header class="px-6 py-5 flex items-center justify-between max-w-lg mx-auto">
        <div class="flex items-center gap-3">
            <div class="logo-icon w-11 h-11 rounded-xl flex items-center justify-center">
                <i class="fas fa-film text-white text-xl"></i>
            </div>
            <div>
                <h1 class="font-title font-bold text-lg">""" + NOME_APP_CURTO + """</h1>
                <p class="text-xs text-gray-400">Livro em Cena</p>
            </div>
        </div>
    </header>

    <main class="max-w-lg mx-auto px-6 pb-10">
        <!-- Tela Início -->
        <section id="inicio" class="fade">
            <div class="text-center mb-8 pt-4">
                <h2 class="font-title text-3xl font-bold mb-3">A Alma da História<br>em Cada Cena ✨</h2>
                <p class="text-gray-400">Cole o título e a história — e a IA transforma em vídeo pronto!</p>
            </div>
            
            <div class="space-y-4 mb-8">
                <div>
                    <label class="block text-sm font-medium mb-2">📖 Título da História</label>
                    <input id="titulo" type="text" placeholder="Ex: Traído pelo Meu Dragão..." 
                        class="input w-full rounded-xl px-4 py-3 text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">✨ Sinopse / História</label>
                    <textarea id="sinopse" rows="5" placeholder="Há dez anos, Aleric foi traído..." 
                        class="input w-full rounded-xl px-4 py-3 text-white resize-none"></textarea>
                </div>
            </div>
            
            <button onclick="gerar()" class="btn-grad w-full py-4 rounded-xl text-white font-bold text-lg">
                <i class="fas fa-magic mr-2"></i> Criar Meu Vídeo
            </button>
        </section>

        <!-- Tela Carregando -->
        <section id="carregando" class="hidden text-center py-16 fade">
            <div class="spinner mx-auto mb-4"></div>
            <p class="text-lg font-medium" id="status">Gerando capa...</p>
            <p class="text-sm text-gray-500 mt-2">A alma da história está ganhando vida ✨</p>
        </section>

        <!-- Tela Resultado -->
        <section id="resultado" class="hidden fade">
            <div class="text-center mb-6">
                <h3 id="titulo_final" class="font-title text-2xl font-bold"></h3>
                <p class="text-sm text-gray-400 mt-1">""" + NOME_APP_COMPLETO + """</p>
            </div>
            
            <div class="capa mb-6 overflow-hidden">
                <img id="img_capa" class="w-full aspect-[9/16] object-cover">
            </div>
            
            <p id="texto_final" class="text-gray-300 mb-8 leading-relaxed"></p>
            
            <div class="space-y-3">
                <a id="link_download" href="#" download class="btn-grad block text-center py-4 rounded-xl text-white font-bold">
                    <i class="fas fa-download mr-2"></i> Baixar Vídeo .MP4
                </a>
                <button onclick="reiniciar()" class="w-full py-3 rounded-xl border border-gray-700 text-gray-300 hover:bg-gray-800 transition">
                    <i class="fas fa-plus mr-2"></i> Criar Nova História
                </button>
            </div>
        </section>
    </main>

<script>
async function gerar() {
    const titulo = document.getElementById('titulo').value.trim();
    const sinopse = document.getElementById('sinopse').value.trim();
    
    if (!titulo || !sinopse) {
        alert('Preencha o título e a história! 📖');
        return;
    }
    
    document.getElementById('inicio').classList.add('hidden');
    document.getElementById('resultado').classList.add('hidden');
    document.getElementById('carregando').classList.remove('hidden');
    
    try {
        // 1. Capa
        document.getElementById('status').textContent = 'Desenhando a alma da história...';
        const capaRes = await fetch('/gerar-capa', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({titulo})
        });
        const capaDados = await capaRes.json();
        
        // 2. Áudio
        document.getElementById('status').textContent = 'Dando voz à história...';
        const audioRes = await fetch('/gerar-audio', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({texto: sinopse})
        });
        const audioDados = await audioRes.json();
        
        // 3. Vídeo
        document.getElementById('status').textContent = 'Montando em cena...';
        const videoRes = await fetch('/criar-video', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({imagem: capaDados.url, audio: audioDados.caminho})
        });
        
        if (!videoRes.ok) throw new Error('Erro ao criar vídeo');
        const blob = await videoRes.blob();
        const url = URL.createObjectURL(blob);
        
        // Mostra resultado
        document.getElementById('carregando').classList.add('hidden');
        document.getElementById('resultado').classList.remove('hidden');
        document.getElementById('titulo_final').textContent = titulo;
        document.getElementById('img_capa').src = capaDados.url;
        document.getElementById('texto_final').textContent = sinopse;
        document.getElementById('link_download').href = url;
        document.getElementById('link_download').download = titulo.replace(/\W+/g, '_') + '.mp4';
        
    } catch (erro) {
        alert('Deu algo errado: ' + erro.message + ' Tente novamente!');
        reiniciar();
    }
}

function reiniciar() {
    document.getElementById('inicio').classList.remove('hidden');
    document.getElementById('carregando').classList.add('hidden');
    document.getElementById('resultado').classList.add('hidden');
    document.getElementById('titulo').value = '';
    document.getElementById('sinopse').value = '';
}
</script>
</body>
</html>
    """)

# ========== ROTAS DA API ==========
@app.route("/gerar-capa", methods=["POST"])
def rota_capa():
    dados = request.json
    return jsonify({"url": gerar_capa_url(dados.get("titulo", ""))})

@app.route("/gerar-audio", methods=["POST"])
def rota_audio():
    dados = request.json
    return jsonify({"caminho": criar_arquivo_audio(dados.get("texto", ""))})

@app.route("/criar-video", methods=["POST"])
def rota_video():
    dados = request.json
    video_path = criar_video_arquivo(dados.get("imagem"), dados.get("audio"))
    if not video_path:
        return jsonify({"erro": "Falha ao montar vídeo"}), 500
    return send_file(video_path, as_attachment=True, download_name="CinePagina_LivroEmCena.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
