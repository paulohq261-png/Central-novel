from flask import Flask, render_template_string, request, jsonify, send_file
import os
import re
import io
import requests
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, TextClip, ColorClip
import tempfile

app = Flask(__name__)

# === DADOS ===
VOZES_DISPONIVEIS = {
    "narrador": {"nome": "Narrador / Neutro", "prefixo": ""},
    "heroi": {"nome": "Herói (Enérgico)", "prefixo": "Com determinação e coragem: "},
    "vilao": {"nome": "Vilão (Grave/Sombrio)", "prefixo": "Com tom frio e ameaçador: "},
    "princesa": {"nome": "Princesa (Suave)", "prefixo": "Com voz doce e gentil: "},
    "misterioso": {"nome": "Misterioso (Sussurrado)", "prefixo": "Em tom baixo e enigmático: "},
    "anciao": {"nome": "Ancião (Sábio)", "prefixo": "Com voz calma e experiente: "}
}

BANCO_NOVELS = [
    {
        "titulo": "O Despertar das Sombras",
        "resumo": "Em um mundo onde a luz está desaparecendo, Lira, uma jovem guardiã, encontra Kael, um guerreiro exilado. Juntos, eles devem cruzar terras proibidas para selar o Reino das Sombras antes que ele consuma tudo.",
        "capa": "https://picsum.photos/id/237/400/250",
        "genero": "Fantasia / Ação"
    },
    {
        "titulo": "A Vilã Rejeitada Renascida",
        "resumo": "Uma leitora morre e renasce no corpo da vilã de um romance que conhece de cor. Sabendo que está destinada a morrer, ela rejeita o príncipe e conquista seu próprio poder para mudar o destino.",
        "capa": "https://picsum.photos/id/22/400/250",
        "genero": "Isekai / Romance"
    },
    {
        "titulo": "Código & Cultivo Digital",
        "resumo": "Um programador acorda em um universo onde códigos são magia. Para sobreviver, precisa dominar a 'linguagem dos deuses', subir de nível e descobrir por que foi trazido para lá.",
        "capa": "https://picsum.photos/id/180/400/250",
        "genero": "Sci-Fi / Cultivo"
    },
    {
        "titulo": "A Herdeira das Estrelas Perdidas",
        "resumo": "Filha esquecida de um império galáctico descobre seus poderes ao completar 18 anos. Deve viajar entre planetas para reunir fragmentos de um relicário e impedir uma guerra interestelar.",
        "capa": "https://picsum.photos/id/119/400/250",
        "genero": "Espaço / Aventura"
    },
    {
        "titulo": "O Último Guardião da Chama",
        "resumo": "O fogo sagrado que mantém o mundo vivo está apagando. O último portador do fogo precisa encontrar a Origem, enfrentar criaturas das trevas e reacender a esperança.",
        "capa": "https://picsum.photos/id/133/400/250",
        "genero": "Fantasia Épica"
    }
]

# === TEMPLATE DA INTERFACE ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovelToVision — Gerador de Vídeos de Novel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
    <style>
        :root {
            --bg: #05050f;
            --panel: #0f0f1f;
            --card: #1a1a2e;
            --accent: #8b5cf6;
            --accent2: #d946ef;
            --texto: #e5e7eb;
        }
        body {
            background: var(--bg);
            color: var(--texto);
            font-family: 'Segoe UI', sans-serif;
        }
        .glass {
            background: rgba(26, 26, 46, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(139, 92, 246, 0.2);
        }
        .glow-border {
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.2), inset 0 0 15px rgba(217, 70, 239, 0.1);
        }
        .gradient-text {
            background: linear-gradient(90deg, #8b5cf6, #d946ef, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .card-novel:hover {
            transform: translateY(-4px);
            border-color: #8b5cf6;
            box-shadow: 0 10px 25px rgba(139, 92, 246, 0.2);
        }
        .custom-scroll::-webkit-scrollbar { width: 6px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
        .loading-spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 10px rgba(139, 92, 246, 0.4); }
            50% { box-shadow: 0 0 25px rgba(217, 70, 239, 0.6); }
        }
        .pulse-btn { animation: pulse-glow 2s infinite; }
        .video-preview {
            width: 100%;
            max-height: 500px;
            border-radius: 12px;
            background: #000;
        }
        .progress-bar {
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(90deg, #8b5cf6, #d946ef);
            width: 0%;
            transition: width 0.5s ease;
        }
    </style>
</head>
<body class="min-h-screen">
    <!-- Cabeçalho -->
    <header class="glass border-b border-purple-500/20 px-4 py-3 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text">✨ NovelToVision</h1>
            <nav class="hidden md:flex gap-4 text-sm">
                <a href="#busca" class="hover:text-purple-400 transition">🔍 Buscar Novel</a>
                <a href="#editor" class="hover:text-purple-400 transition">✍️ Editor</a>
                <a href="#personagens" class="hover:text-purple-400 transition">👤 Vozes</a>
                <a href="#video" class="hover:text-purple-400 transition">🎬 Vídeo</a>
            </nav>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 space-y-12">

        <!-- === BUSCA DE NOVELS === -->
        <section id="busca" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-magnifying-glass text-purple-400"></i>
                Pesquisar Novels
            </h2>
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="termoBusca" placeholder="Nome ou gênero..."
                    class="flex-1 px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30 focus:border-purple-400 outline-none">
                <button onclick="buscarNovels()" class="bg-purple-600 hover:bg-purple-500 px-6 py-3 rounded-xl font-semibold transition pulse-btn">
                    <i class="fa-solid fa-search mr-2"></i> Pesquisar
                </button>
            </div>
            <div id="resultadosBusca" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                <!-- Resultados -->
            </div>
        </section>

        <!-- === EDITOR DE TEXTO === -->
        <section id="editor" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-pen-to-square text-fuchsia-400"></i>
                Editor de Capítulo
            </h2>
            <textarea id="textoHistoria" rows="12" 
                class="w-full rounded-xl bg-gray-900/50 border border-purple-500/30 p-4 focus:border-purple-400 outline-none custom-scroll text-sm"
                placeholder='Cole ou escreva sua história aqui... Use: **Nome:** Fala para os personagens. Exemplo:&#10;&#10;O sol se punha sobre a torre.&#10;&#10;**Lira:** O que vamos fazer agora?&#10;&#10;**Kael:** Enfrentar as sombras. Não há volta.&#10;&#10;**Narrador:** E assim começou a jornada.'>
O sol se punha sobre a cidade antiga. Lira observava do alto da torre.

**Lira:** O que vamos fazer agora?

**Kael:** Vamos enfrentar o Reino das Sombras. Não há volta.

**Narrador:** E assim começou a jornada que mudaria tudo.
            </textarea>
            <button onclick="processarTexto()" class="bg-gradient-to-r from-purple-600 to-fuchsia-600 px-6 py-3 rounded-xl font-bold hover:opacity-90 transition">
                <i class="fa-solid fa-wand-magic-sparkles mr-2"></i> Analisar e Criar Cenas
            </button>
        </section>

        <!-- === PERSONAGENS & VOZES === -->
        <section id="personagens" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-users text-cyan-400"></i>
                Vozes dos Personagens
            </h2>
            <p class="text-sm text-gray-400">Sistema detecta automaticamente: <code>**Nome:** Fala</code></p>
            <div id="listaPersonagens" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <!-- Preenchido após processar -->
            </div>
        </section>

        <!-- === GERAÇÃO DE VÍDEO === -->
        <section id="video" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-film text-amber-400"></i>
                Gerador de Vídeo
            </h2>

            <div class="glass rounded-2xl p-5 glow-border space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Formato</label>
                        <select id="videoFormato" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="9:16">Vertical 9:16 (TikTok/Reels)</option>
                            <option value="16:9">Paisagem 16:9 (YouTube)</option>
                            <option value="1:1">Quadrado 1:1 (Instagram)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Duração por Cena</label>
                        <select id="duracaoCena" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="3">3 segundos</option>
                            <option value="5" selected>5 segundos</option>
                            <option value="8">8 segundos</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Legenda</label>
                        <select id="estiloLegenda" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="nenhuma">Sem legenda</option>
                            <option value="branca">Legenda Branca</option>
                            <option value="amarela">Legenda Amarela Neon</option>
                        </select>
                    </div>
                </div>

                <button onclick="gerarVideo()" class="bg-gradient-to-r from-purple-600 via-fuchsia-600 to-cyan-600 px-6 py-3 rounded-xl font-bold hover:opacity-90 transition pulse-btn">
                    <i class="fa-solid fa-clapperboard mr-2"></i> Gerar Vídeo Completo
                </button>

                <div id="progressoVideo" class="hidden space-y-2">
                    <p class="text-sm text-gray-300"><i class="fa-solid fa-spinner loading-spin mr-2"></i> Montando vídeo...</p>
                    <div class="progress-bar" id="barraProgresso"></div>
                </div>

                <div id="previewVideo" class="hidden">
                    <video id="videoPlayer" class="video-preview" controls></video>
                    <a id="downloadVideo" href="#" download="novel_video.mp4" class="inline-block mt-3 bg-green-600 hover:bg-green-500 px-6 py-2 rounded-xl font-semibold">
                        <i class="fa-solid fa-download mr-2"></i> Baixar Vídeo
                    </a>
                </div>
            </div>

            <div id="cenasGeradas" class="space-y-4 mt-6">
                <!-- Cenas aparecem aqui -->
            </div>
        </section>

    </main>

    <footer class="text-center py-6 text-xs text-gray-500 mt-12">
        NovelToVision — Gerador de Vídeos de Novel 🎬✨
    </footer>

    <script>
        let cenas = [];
        let personagensDetectados = new Set();
        const bancoNovels = """ + str(BANCO_NOVELS).replace("'", "\\'") + "";

        // Buscar novels
        function buscarNovels() {
            const termo = document.getElementById('termoBusca').value.toLowerCase().trim();
            const container = document.getElementById('resultadosBusca');
            
            const dados = bancoNovels.filter(n => 
                !termo || n.titulo.toLowerCase().includes(termo) || n.genero.toLowerCase().includes(termo) || n.resumo.toLowerCase().includes(termo)
            );
            
            if (dados.length === 0) {
                container.innerHTML = '<p class="text-gray-400">Nenhum resultado encontrado.</p>';
                return;
            }
            
            container.innerHTML = '';
            dados.forEach(n => {
                container.innerHTML += `
                <div class="glass rounded-xl p-4 card-novel transition-all duration-300 cursor-pointer"
                     onclick="usarNovel('${n.titulo.replace(/'/g, "\\'")}', '${n.resumo.replace(/'/g, "\\'")}')">
                    <img src="${n.capa}" alt="${n.titulo}" class="w-full h-40 object-cover rounded-lg mb-3">
                    <span class="text-xs bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded-full">${n.genero}</span>
                    <h3 class="font-bold text-lg text-purple-300 mt-2">${n.titulo}</h3>
                    <p class="text-sm text-gray-400 mt-1 line-clamp-2">${n.resumo}</p>
                    <span class="text-xs text-fuchsia-400 mt-2 inline-block">Clique → Usar esta história</span>
                </div>`;
            });
        }

        function usarNovel(titulo, resumo) {
            document.getElementById('textoHistoria').value = `# ${titulo}\\n\\n${resumo}`;
            window.scrollTo({top: document.getElementById('editor').offsetTop, behavior: 'smooth'});
        }

        // Processar texto → personagens + cenas
        function processarTexto() {
            const texto = document.getElementById('textoHistoria').value;
            personagensDetectados.clear();
            cenas = [];
            
            // Extrair nomes de personagens
            const padraoFala = /\\*\\*([^*]+?)\\*\\*:\\s*(.+)/g;
            let match;
            while ((match = padraoFala.exec(texto)) !== null) {
                personagensDetectados.add(match[1].trim());
            }
            
            // Preencher lista de personagens com seleção de voz
            const lista = document.getElementById('listaPersonagens');
            const vozes = [
                {id: 'narrador', nome: 'Narrador / Neutro'},
                {id: 'heroi', nome: 'Herói (Enérgico)'},
                {id: 'vilao', nome: 'Vilão (Grave)'},
                {id: 'princesa', nome: 'Princesa (Suave)'},
                {id: 'misterioso', nome: 'Misterioso'},
                {id: 'anciao', nome: 'Ancião (Sábio)'}
            ];
            
            lista.innerHTML = '';
            if (personagensDetectados.size === 0) {
                lista.innerHTML = '<p class="text-gray-400 text-sm">Nenhum personagem detectado. Use: <code>**Nome:** Fala</code> no texto.</p>';
            } else {
                personagensDetectados.forEach(p => {
                    lista.innerHTML += `
                    <div class="glass rounded-lg p-3">
                        <label class="font-semibold text-purple-300">${p}</label>
                        <select class="mt-2 w-full bg-gray-900/70 rounded-lg p-2 text-sm" data-personagem="${p}">
                            ${vozes.map((v,i) => `<option value="${v.id}" ${i===0?'selected':''}>${v.nome}</option>`).join('')}
                        </select>
                    </div>`;
                });
            }
            
            // Dividir em cenas
            const blocos = texto.split(/\\n\\n+/);
            const cenasContainer = document.getElementById('cenasGeradas');
            cenasContainer.innerHTML = '';
            
            blocos.forEach((bloco, idx) => {
                if (!bloco.trim()) return;
                cenas.push({id: idx+1, texto: bloco});
                cenasContainer.innerHTML += `
                <div class="glass rounded-xl p-4 glow-border">
                    <h4 class="font-bold text-fuchsia-300 mb-2">Cena ${idx+1}</h4>
                    <p class="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">${bloco}</p>
                </div>`;
            });
            
            window.scrollTo({top: document.getElementById('personagens').offsetTop, behavior: 'smooth'});
        }

        // Gerar vídeo
        async function gerarVideo() {
            if (cenas.length === 0) {
                alert('Primeiro analise uma história no editor!');
                return;
            }

            const formato = document.getElementById('videoFormato').value;
            const duracao = parseInt(document.getElementById('duracaoCena').value);
            const legenda = document.getElementById('estiloLegenda').value;

            const selecoes = {};
            document.querySelectorAll('[data-personagem]').forEach(s => {
                selecoes[s.dataset.personagem] = s.value;
            });

            document.getElementById('progressoVideo').classList.remove('hidden');
            document.getElementById('previewVideo').classList.add('hidden');
            document.getElementById('barraProgresso').style.width = '0%';

            try {
                const res = await fetch('/api/gerar-video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        cenas: cenas,
                        vozesSelecionadas: selecoes,
                        formato: formato,
                        duracaoCena: duracao,
                        legenda: legenda
                    })
                });

                const blob = await res.blob();
                const url = URL.createObjectURL(blob);

                document.getElementById('videoPlayer').src = url;
                document.getElementById('downloadVideo').href = url;
                document.getElementById('previewVideo').classList.remove('hidden');
                document.getElementById('barraProgresso').style.width = '100%';

            } catch (erro) {
                alert('Erro ao gerar vídeo. Tente novamente.');
                console.error(erro);
            } finally {
                document.getElementById('progressoVideo').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

# === API: Buscar Novels ===
@app.route("/api/buscar-novels")
def api_buscar_novels():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify(BANCO_NOVELS)
    filtrados = [
        n for n in BANCO_NOVELS
        if q in n["titulo"].lower() or q in n["genero"].lower() or q in n["resumo"].lower()
    ]
    return jsonify(filtrados if filtrados else BANCO_NOVELS[:2])

# === API: Gerar Áudio ===
@app.route("/api/gerar-audio", methods=["POST"])
def api_gerar_audio():
    dados = request.get_json()
    texto = dados.get("texto", "")
    vozes_selecionadas = dados.get("vozesSelecionadas", {})
    
    def processar_fala(match):
        nome = match.group(1).strip()
        fala = match.group(2).strip()
        voz_id = vozes_selecionadas.get(nome, "narrador")
        prefixo = VOZES_DISPONIVEIS[voz_id]["prefixo"]
        return f"{prefixo}{fala}"
    
    texto_processado = re.sub(r"\*\*[^*]+?\*\*:\s*(.+)", lambda m: processar_fala(m), texto)
    texto_final = re.sub(r"\*\*([^*]+)\*\*", r"\1 disse: ", texto_processado)
    
    tts = gTTS(text=texto_final, lang="pt-BR", slow=False)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    
    return send_file(buffer, mimetype="audio/mpeg")

# === API: Gerar Vídeo ===
@app.route("/api/gerar-video", methods=["POST"])
def api_gerar_video():
    dados = request.get_json()
    cenas = dados.get("cenas", [])
    vozes_selecionadas = dados.get("vozesSelecionadas", {})
    formato = dados.get("formato", "9:16")
    duracao_cena = dados.get("duracaoCena", 5)
    estilo_legenda = dados.get("legenda", "nenhuma")

    # Dimensões
    dims = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080)
    }
    largura, altura = dims.get(formato, (1080, 1920))

    clips = []

    for idx, cena in enumerate(cenas):
        texto_cena = cena["texto"]

        # 1. Texto para áudio
        def processar_fala(match):
            nome = match.group(1).strip()
            fala = match.group(2).strip()
            voz_id = vozes_selecionadas.get(nome, "narrador")
            prefixo = VOZES_DISPONIVEIS[voz_id]["prefixo"]
            return f"{prefixo}{fala}"

        texto_processado = re.sub(r"\*\*[^*]+?\*\*:\s*(.+)", lambda m: processar_fala(m), texto_cena)
        texto_final = re.sub(r"\*\*([^*]+)\*\*", r"\1 disse: ", texto_processado)

        # 2. Gerar áudio temporário
        tts = gTTS(text=texto_final, lang="pt-BR", slow=False)
        temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tts.write_to_fp(temp_audio)
        temp_audio.close()

        audio_clip = AudioFileClip(temp_audio.name)
        duracao = max(duracao_cena, audio_clip.duration)

        # 3. Baixar imagem de cena
        img_url = f"https://picsum.photos/seed/{idx+100}/{largura}/{altura}"
        temp_img = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temp_img.close()

        with requests.get(img_url) as r:
            with open(temp_img.name, "wb") as f:
                f.write(r.content)

        imagem_clip = ImageClip(temp_img.name).resize((largura, altura)).set_duration(duracao)

        # 4. Legenda
        if estilo_legenda != "nenhuma":
            cor = "white" if estilo_legenda == "branca" else "#fde047"
            texto_curto = texto_final[:90] + "..." if len(texto_final) > 90 else texto_final

            txt_clip = TextClip(
                texto_curto,
                fontsize=48,
                color=cor,
                font="Arial-Bold",
                method="label"
            )

            txt_clip = txt_clip.set_position(("center", altura - 160)).set_duration(duracao)
            imagem_clip = CompositeVideoClip([imagem_clip, txt_clip])

        imagem_clip = imagem_clip.set_audio(audio_clip)
        clips.append(imagem_clip)

    # 5. Montar vídeo final
    from moviepy.editor import concatenate_videoclips
    video_final = concatenate_videoclips(clips, method="compose")

    temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_video.close()

    video_final.write_videofile(
        temp_video.name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=tempfile.gettempdir() + "/temp_audio.mp4",
        remove_temp=True
    )

    # Limpar arquivos temporários
    try:
        os.unlink(temp_audio.name)
        os.unlink(temp_img.name)
    except:
        pass

    return send_file(temp_video.name, mimetype="video/mp4", as_attachment=True, download_name="novel_video.mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
