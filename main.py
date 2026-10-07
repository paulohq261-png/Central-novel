from flask import Flask, render_template_string, request, jsonify, send_file
import os
import re
import io
import requests
import zipfile
from gtts import gTTS

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
        "resumo": "Um programador acorda em um universo onde códigos são magia. Para sobreviver, precisa dominar a linguagem dos deuses, subir de nível e descobrir por que foi trazido para lá.",
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

# === TEMPLATE ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovelToVision — Kit de Produção Rápido</title>
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
        body { background: var(--bg); color: var(--texto); font-family: 'Segoe UI', sans-serif; }
        .glass { background: rgba(26,26,46,0.7); backdrop-filter: blur(12px); border: 1px solid rgba(139,92,246,0.2); }
        .glow-border { box-shadow: 0 0 20px rgba(139,92,246,0.2), inset 0 0 15px rgba(217,70,239,0.1); }
        .gradient-text { background: linear-gradient(90deg, #8b5cf6, #d946ef, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card-novel:hover { transform: translateY(-4px); border-color: #8b5cf6; box-shadow: 0 10px 25px rgba(139,92,246,0.2); }
        .custom-scroll::-webkit-scrollbar { width: 6px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
        .loading-spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse-glow {
            0%,100% { box-shadow: 0 0 10px rgba(139,92,246,0.4); }
            50% { box-shadow: 0 0 25px rgba(217,70,239,0.6); }
        }
        .pulse-btn { animation: pulse-glow 2s infinite; }
        .progress-bar { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #8b5cf6, #d946ef); width: 0%; transition: width 0.5s ease; }
    </style>
</head>
<body class="min-h-screen">
    <header class="glass border-b border-purple-500/20 px-4 py-3 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text">✨ NovelToVision</h1>
            <nav class="hidden md:flex gap-4 text-sm">
                <a href="#busca" class="hover:text-purple-400 transition">🔍 Buscar Novel</a>
                <a href="#editor" class="hover:text-purple-400 transition">✍️ Editor</a>
                <a href="#personagens" class="hover:text-purple-400 transition">👤 Vozes</a>
                <a href="#exportar" class="hover:text-purple-400 transition">📦 Exportar</a>
            </nav>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 space-y-12">
        <section class="glass rounded-2xl p-4 border border-green-500/30 bg-green-950/20">
            <h3 class="font-bold text-green-300 flex items-center gap-2">
                <i class="fa-solid fa-bolt"></i> Versão Estável — Render Compatível
            </h3>
            <p class="text-sm text-gray-300 mt-1">
                Exporta um ZIP com áudios, imagens e legendas. Monta no CapCut em segundos.
            </p>
        </section>

        <section id="busca" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-magnifying-glass text-purple-400"></i> Pesquisar Novels
            </h2>
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="termoBusca" placeholder="Nome ou gênero..."
                    class="flex-1 px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30 focus:border-purple-400 outline-none">
                <button onclick="buscarNovels()" class="bg-purple-600 hover:bg-purple-500 px-6 py-3 rounded-xl font-semibold transition pulse-btn">
                    <i class="fa-solid fa-search mr-2"></i> Pesquisar
                </button>
            </div>
            <div id="resultadosBusca" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4"></div>
        </section>

        <section id="editor" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-pen-to-square text-fuchsia-400"></i> Editor de Capítulo
            </h2>
            <textarea id="textoHistoria" rows="12" 
                class="w-full rounded-xl bg-gray-900/50 border border-purple-500/30 p-4 focus:border-purple-400 outline-none custom-scroll text-sm"
                placeholder='Cole sua história. Use: **Nome:** Fala'>
O sol se punha sobre a cidade antiga. Lira observava do alto da torre.

**Lira:** O que vamos fazer agora?

**Kael:** Vamos enfrentar o Reino das Sombras. Não há volta.

**Narrador:** E assim começou a jornada que mudaria tudo.
            </textarea>
            <button onclick="processarTexto()" class="bg-gradient-to-r from-purple-600 to-fuchsia-600 px-6 py-3 rounded-xl font-bold hover:opacity-90 transition">
                <i class="fa-solid fa-wand-magic-sparkles mr-2"></i> Analisar e Criar Cenas
            </button>
        </section>

        <section id="personagens" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-users text-cyan-400"></i> Vozes dos Personagens
            </h2>
            <p class="text-sm text-gray-400">Detecta automaticamente: <code>**Nome:** Fala</code></p>
            <div id="listaPersonagens" class="grid grid-cols-1 sm:grid-cols-2 gap-3"></div>
        </section>

        <section id="exportar" class="space-y-4">
            <h2 class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-download text-amber-400"></i> Baixar Kit de Produção
            </h2>
            <div class="glass rounded-2xl p-5 glow-border space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Formato</label>
                        <select id="formato" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="9:16">Vertical 9:16</option>
                            <option value="16:9">Paisagem 16:9</option>
                            <option value="1:1">Quadrado 1:1</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Duração por Cena</label>
                        <select id="duracao" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="3">3s</option>
                            <option value="5" selected>5s</option>
                            <option value="8">8s</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-purple-300 mb-2">Legenda</label>
                        <select id="legenda" class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-purple-500/30">
                            <option value="nenhuma">Sem legenda</option>
                            <option value="branca">Branca</option>
                            <option value="amarela">Amarela Neon</option>
                        </select>
                    </div>
                </div>
                <button onclick="baixarKit()" class="bg-gradient-to-r from-green-600 via-emerald-600 to-cyan-600 px-6 py-3 rounded-xl font-bold hover:opacity-90 transition pulse-btn">
                    <i class="fa-solid fa-file-zipper mr-2"></i> Baixar ZIP
                </button>
                <div id="progresso" class="hidden space-y-2">
                    <p class="text-sm text-gray-300"><i class="fa-solid fa-spinner loading-spin mr-2"></i> Gerando arquivos...</p>
                    <div class="progress-bar" id="barra"></div>
                </div>
                <div id="linkDownload" class="hidden">
                    <a id="aDownload" href="#" download="novel_kit.zip" class="inline-block mt-3 bg-purple-600 hover:bg-purple-500 px-6 py-2 rounded-xl font-semibold">
                        <i class="fa-solid fa-download mr-2"></i> Baixar ZIP
                    </a>
                </div>
            </div>
            <div id="cenas" class="space-y-4 mt-6"></div>
        </section>
    </main>

    <script>
        let cenas = [];
        let personagens = new Set();
        const bancoNovels = """ + str(BANCO_NOVELS).replace("'", "\\'") + "";

        function buscarNovels() {
            const termo = document.getElementById('termoBusca').value.toLowerCase().trim();
            const res = bancoNovels.filter(n => !termo || n.titulo.toLowerCase().includes(termo) || n.genero.toLowerCase().includes(termo) || n.resumo.toLowerCase().includes(termo));
            const container = document.getElementById('resultadosBusca');
            if (!res.length) { container.innerHTML = '<p class=\"text-gray-400\">Nenhum resultado.</p>'; return; }
            container.innerHTML = '';
            res.forEach(n => {
                container.innerHTML += `
                <div class=\"glass rounded-xl p-4 card-novel transition-all duration-300 cursor-pointer\"
                     onclick=\"usarNovel('${n.titulo.replace(/'/g, "\\'")}', '${n.resumo.replace(/'/g, "\\'")}')\">
                    <img src=\"${n.capa}\" alt=\"${n.titulo}\" class=\"w-full h-40 object-cover rounded-lg mb-3\">
                    <span class=\"text-xs bg-purple-900/50 text-purple-300 px-2 py-1 rounded-full\">${n.genero}</span>
                    <h3 class=\"font-bold text-lg text-purple-300 mt-2\">${n.titulo}</h3>
                    <p class=\"text-sm text-gray-400 mt-1\">${n.resumo.substring(0, 80)}...</p>
                </div>`;
            });
        }

        function usarNovel(titulo, resumo) {
            document.getElementById('textoHistoria').value = '# ' + titulo + '\\n\\n' + resumo;
            document.getElementById('editor').scrollIntoView({behavior: 'smooth'});
        }

        function processarTexto() {
            const texto = document.getElementById('textoHistoria').value;
            personagens.clear();
            cenas = [];
            const padrao = /\\*\\*([^*]+?)\\*\\*:\\s*(.+)/g;
            let m;
            while ((m = padrao.exec(texto)) !== null) personagens.add(m[1].trim());

            const lista = document.getElementById('listaPersonagens');
            const vozes = [
                {id:'narrador', nome:'Narrador'},
                {id:'heroi', nome:'Herói'},
                {id:'vilao', nome:'Vilão'},
                {id:'princesa', nome:'Princesa'},
                {id:'misterioso', nome:'Misterioso'},
                {id:'anciao', nome:'Ancião'}
            ];
            lista.innerHTML = '';
            if (!personagens.size) {
                lista.innerHTML = '<p class=\"text-gray-400 text-sm\">Use: **Nome:** Fala</p>';
            } else {
                personagens.forEach(p => {
                    lista.innerHTML += `
                    <div class=\"glass rounded-lg p-3\">
                        <label class=\"font-semibold text-purple-300\">${p}</label>
                        <select class=\"mt-2 w-full bg-gray-900/70 rounded-lg p-2 text-sm\" data-pessoa=\"${p}\">
                            ${vozes.map((v,i) => `<option value=\"${v.id}\" ${i===0?'selected':''}>${v.nome}</option>`).join('')}
                        </select>
                    </div>`;
                });
            }

            const blocos = texto.split(/\\n\\n+/);
            const cenasDiv = document.getElementById('cenas');
            cenasDiv.innerHTML = '';
            blocos.forEach((bloco, i) => {
                if (!bloco.trim()) return;
                cenas.push({id:i+1, texto:bloco});
                cenasDiv.innerHTML += `
                <div class=\"glass rounded-xl p-4 glow-border\">
                    <h4 class=\"font-bold text-fuchsia-300 mb-2\">Cena ${i+1}</h4>
                    <p class=\"text-sm text-gray-300 whitespace-pre-wrap\">${bloco}</p>
                </div>`;
            });
            document.getElementById('personagens').scrollIntoView({behavior: 'smooth'});
        }

        async function baixarKit() {
            if (!cenas.length) { alert('Analise uma história primeiro!'); return; }
            const sel = {};
            document.querySelectorAll('[data-pessoa]').forEach(s => sel[s.dataset.pessoa] = s.value);

            document.getElementById('progresso').classList.remove('hidden');
            document.getElementById('linkDownload').classList.add('hidden');
            document.getElementById('barra').style.width = '0%';

            try {
                const res = await fetch('/api/baixar-kit', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({
                        cenas: cenas,
                        vozes: sel,
                        formato: document.getElementById('formato').value,
                        duracao: parseInt(document.getElementById('duracao').value),
                        legenda: document.getElementById('legenda').value
                    })
                });
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                document.getElementById('aDownload').href = url;
                document.getElementById('barra').style.width = '100%';
                document.getElementById('linkDownload').classList.remove('hidden');
            } catch (e) {
                alert('Erro: ' + e);
            } finally {
                document.getElementById('progresso').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

# === ROTAS ===
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/buscar-novels")
def buscar_novels():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify(BANCO_NOVELS)
    filtrados = [n for n in BANCO_NOVELS if q in n["titulo"].lower() or q in n["genero"].lower() or q in n["resumo"].lower()]
    return jsonify(filtrados if filtrados else BANCO_NOVELS[:2])

@app.route("/api/baixar-kit", methods=["POST"])
def baixar_kit():
    dados = request.get_json()
    cenas = dados.get("cenas", [])
    vozes = dados.get("vozes", {})
    formato = dados.get("formato", "9:16")
    duracao = dados.get("duracao", 5)
    legenda = dados.get("legenda", "nenhuma")

    dims = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080)
    }
    largura, altura = dims.get(formato, (1080, 1920))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cena in enumerate(cenas):
            n = idx + 1
            texto = cena["texto"]

            def processar_fala(match):
                nome = match.group(1).strip()
                fala = match.group(2).strip()
                v = vozes.get(nome, "narrador")
                return f"{VOZES_DISPONIVEIS[v]['prefixo']}{fala}"

            texto_audio = re.sub(r"\*\*[^*]+?\*\*:\s*(.+)", lambda m: processar_fala(m), texto)
            texto_audio = re.sub(r"\*\*([^*]+)\*\*", r"\1 disse: ", texto_audio)

            tts = gTTS(text=texto_audio, lang="pt-BR", slow=False)
            audio_buf = io.BytesIO()
            tts.write_to_fp(audio_buf)
            audio_buf.seek(0)
            zf.writestr(f"cena_{n:02d}/audio_{n}.mp3", audio_buf.read())

            img_url = f"https://picsum.photos/seed/{n+2000}/{largura}/{altura}"
            img = requests.get(img_url, timeout=15)
            zf.writestr(f"cena_{n:02d}/imagem_{n}.jpg", img.content)

            zf.writestr(f"cena_{n:02d}/texto.txt", texto)

            if legenda != "nenhuma":
                curto = texto_audio[:90] + "..." if len(texto_audio) > 90 else texto_audio
                zf.writestr(f"cena_{n:02d}/legenda.txt", f"Estilo: {legenda}\\n\\n{curto}")

        instrucoes = f"""NOVEL TO VISION — KIT DE PRODUÇÃO

Formato: {formato}
Duração sugerida: {duracao}s por cena

COMO MONTAR NO CAPCUT:
1. Importe todas as imagens e áudios
2. Coloque cada imagem na linha do tempo
3. Ajuste a duração para {duracao} segundos
4. Adicione o áudio correspondente
5. Use o texto da legenda na parte inferior
6. Exporte em 1080p

Feito com ✨ NovelToVision
"""
        zf.writestr("INSTRUCOES.txt", instrucoes)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="novel_kit.zip"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
