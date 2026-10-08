from flask import Flask, render_template_string, request, jsonify, send_file
import os
import re
import io
import requests
import zipfile
from gtts import gTTS

app = Flask(__name__)

VOZES_DISPONIVEIS = {
    "narrador": {"nome": "Narrador / Neutro", "prefixo": ""},
    "heroi": {"nome": "Herói", "prefixo": "Com determinação: "},
    "vilao": {"nome": "Vilão", "prefixo": "Com tom firme: "},
    "princesa": {"nome": "Princesa", "prefixo": "Com voz doce: "},
    "misterioso": {"nome": "Misterioso", "prefixo": "Com tom calmo: "},
    "anciao": {"nome": "Ancião", "prefixo": "Com voz sábia: "}
}

BANCO_NOVELS = [
    {
        "titulo": "O Despertar das Sombras",
        "resumo": "Em um mundo onde a luz está desaparecendo, Lira encontra Kael, um guerreiro exilado. Juntos devem proteger o reino.",
        "capa": "https://picsum.photos/id/237/400/250",
        "genero": "Fantasia / Ação"
    },
    {
        "titulo": "A Herdeira das Estrelas",
        "resumo": "Uma jovem descobre seus poderes e precisa viajar pelo espaço para proteger o relicário sagrado.",
        "capa": "https://picsum.photos/id/119/400/250",
        "genero": "Aventura / Magia"
    }
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Novel 2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
    <style>
        :root {--bg: #05050f; --accent: #8b5cf6; --accent2: #d946ef; --texto: #e5e7eb;}
        body {background: var(--bg); color: var(--texto); font-family: sans-serif;}
        .glass {background: rgba(26,26,46,0.7); backdrop-filter: blur(12px); border: 1px solid rgba(139,92,246,0.2);}
        .gradient-text {background: linear-gradient(90deg, #8b5cf6, #d946ef, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
        .btn-gradient {background: linear-gradient(90deg, #8b5cf6, #d946ef);}
        .btn-gradient:hover {opacity: 0.9;}
        .card-novel:hover {transform: translateY(-3px); transition: 0.3s; box-shadow: 0 10px 25px rgba(139,92,246,0.2);}
    </style>
</head>
<body class="min-h-screen">
    <header class="glass border-b border-purple-500/20 px-4 py-3 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <h1 class="text-2xl font-bold gradient-text">✨ Central Novel 2.0</h1>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-8 space-y-10">
        <section class="glass rounded-2xl p-4 border border-green-500/30 bg-green-950/20">
            <h3 class="font-bold text-green-300"><i class="fa-solid fa-bolt mr-2"></i>Sistema Ativo — Pronto para Uso</h3>
            <p class="text-sm text-gray-300 mt-1">Escreva sua história → defina vozes → baixe o pacote ZIP com áudio + imagens.</p>
        </section>

        <section id="editor">
            <h2 class="text-xl font-bold text-fuchsia-400 mb-3"><i class="fa-solid fa-pen-to-square mr-2"></i>Escreva sua História</h2>
            <textarea id="textoHistoria" rows="10" class="w-full rounded-xl bg-gray-900/50 border border-purple-500/30 p-4 focus:border-purple-400 outline-none" placeholder="Use: **Nome do Personagem:** Fala...">
O sol se punha sobre a torre.

**Narrador:** O reino estava em paz, mas algo mudava no horizonte.

**Lira:** O que você vê lá?

**Kael:** Sombra. Vem rápido.
            </textarea>
            <button onclick="preparar()" class="mt-3 btn-gradient px-6 py-3 rounded-xl font-bold">
                <i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Preparar e Gerar
            </button>
        </section>

        <section id="vozes" class="hidden">
            <h2 class="text-xl font-bold text-cyan-400 mb-3"><i class="fa-solid fa-users mr-2"></i>Escolha as Vozes</h2>
            <div id="listaVozes" class="grid grid-cols-1 sm:grid-cols-2 gap-3"></div>
            <div class="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="text-sm font-semibold text-purple-300">Formato</label>
                    <select id="formato" class="w-full mt-1 px-3 py-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                        <option value="9:16">Vertical 9:16</option>
                        <option value="16:9">Paisagem 16:9</option>
                        <option value="1:1">Quadrado 1:1</option>
                    </select>
                </div>
                <div>
                    <label class="text-sm font-semibold text-purple-300">Duração (seg)</label>
                    <select id="duracao" class="w-full mt-1 px-3 py-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                        <option value="3">3s</option>
                        <option value="5" selected>5s</option>
                        <option value="8">8s</option>
                    </select>
                </div>
                <div>
                    <label class="text-sm font-semibold text-purple-300">Legenda</label>
                    <select id="legenda" class="w-full mt-1 px-3 py-2 rounded-lg bg-gray-900/50 border border-purple-500/30">
                        <option value="nenhuma">Sem legenda</option>
                        <option value="branca">Branca</option>
                        <option value="amarela">Amarela</option>
                    </select>
                </div>
            </div>
            <button onclick="baixar()" class="mt-5 bg-green-600 hover:bg-green-500 px-6 py-3 rounded-xl font-bold">
                <i class="fa-solid fa-download mr-2"></i>Baixar Pacote ZIP
            </button>
            <div id="status" class="mt-4 hidden">
                <p class="text-gray-300"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Gerando arquivos...</p>
            </div>
            <div id="linkFinal" class="mt-4 hidden">
                <a id="botaoDownload" href="#" download="central_novel_pacote.zip" class="inline-block bg-purple-600 hover:bg-purple-500 px-6 py-2 rounded-xl font-bold">
                    <i class="fa-solid fa-file-zipper mr-2"></i>Baixar Arquivo
                </a>
            </div>
        </section>
    </main>

    <script>
        let cenas = [];
        let perso = new Set();
        const vozes = Object.keys({{VOZES}});

        function preparar(){
            const t = document.getElementById('textoHistoria').value;
            perso.clear(); cenas = [];
            const r = /\\*\\*([^*]+?)\\*\\*:\\s*(.+)/g;
            let m;
            while((m=r.exec(t))!==null) perso.add(m[1].trim());
            const blocos = t.split(/\\n\\n+/);
            blocos.forEach((b,i)=>{if(b.trim()) cenas.push({id:i+1,texto:b});});

            const lista = document.getElementById('listaVozes');
            lista.innerHTML='';
            if(!perso.size){alert('Escreva algo com: **Nome:** Fala'); return;}
            perso.forEach(p=>{
                lista.innerHTML += `<div class="glass rounded-lg p-3">
                    <label class="font-semibold text-purple-300">${p}</label>
                    <select data-pessoa="${p}" class="mt-2 w-full bg-gray-900/70 rounded-lg p-2">
                        ${vozes.map((v,i)=>`<option value="${v}" ${i===0?'selected':''}>${{{{VOZES}}}[v].nome}</option>`).join('')}
                    </select>
                </div>`;
            });
            document.getElementById('vozes').classList.remove('hidden');
            document.getElementById('vozes').scrollIntoView({behavior:'smooth'});
        }

        async function baixar(){
            const sel={};
            document.querySelectorAll('[data-pessoa]').forEach(s=>sel[s.dataset.pessoa]=s.value);
            document.getElementById('status').classList.remove('hidden');
            document.getElementById('linkFinal').classList.add('hidden');
            try{
                const res = await fetch('/api/baixar', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({
                        cenas, vozes:sel,
                        formato:document.getElementById('formato').value,
                        duracao:parseInt(document.getElementById('duracao').value),
                        legenda:document.getElementById('legenda').value
                    })
                });
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                document.getElementById('botaoDownload').href = url;
                document.getElementById('linkFinal').classList.remove('hidden');
            }catch(e){alert('Erro: '+e);}
            finally{document.getElementById('status').classList.add('hidden');}
        }
    </script>
</body>
</html>
""".replace("{{VOZES}}", str(VOZES_DISPONIVEIS))

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/baixar", methods=["POST"])
def api_baixar():
    dados = request.get_json()
    cenas = dados.get("cenas", [])
    sel_vozes = dados.get("vozes", {})
    formato = dados.get("formato", "9:16")
    duracao = dados.get("duracao", 5)
    legenda = dados.get("legenda", "nenhuma")

    dims = {"9:16":(1080,1920), "16:9":(1920,1080), "1:1":(1080,1080)}
    larg, alt = dims.get(formato, (1080,1920))

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cena in enumerate(cenas):
            n = idx + 1
            texto = cena["texto"]

            def trocar_fala(m):
                nome = m.group(1).strip()
                fala = m.group(2).strip()
                v = sel_vozes.get(nome, "narrador")
                return f"{VOZES_DISPONIVEIS[v]['prefixo']}{fala}"

            txt_audio = re.sub(r"\*\*[^*]+?\*\*:\s*(.+)", trocar_fala, texto)
            txt_audio = re.sub(r"\*\*([^*]+)\*\*", r"\1 disse: ", txt_audio)

            tts = gTTS(text=txt_audio, lang="pt-BR", slow=False)
            aud_buf = io.BytesIO()
            tts.write_to_fp(aud_buf)
            aud_buf.seek(0)
            zf.writestr(f"cena_{n:02d}/audio.mp3", aud_buf.read())

            img = requests.get(f"https://picsum.photos/seed/{n+3000}/{larg}/{alt}", timeout=15)
            zf.writestr(f"cena_{n:02d}/imagem.jpg", img.content)
            zf.writestr(f"cena_{n:02d}/texto.txt", texto)

            if legenda != "nenhuma":
                curto = txt_audio[:90] + "..." if len(txt_audio) > 90 else txt_audio
                zf.writestr(f"cena_{n:02d}/legenda.txt", f"Estilo: {legenda}\\n\\n{curto}")

        inst = f"""CENTRAL NOVEL 2.0 — PACOTE DE PRODUÇÃO
Formato: {formato} | Duração: {duracao}s/cena
Como usar:
1. Abra o CapCut
2. Importe as imagens e os áudios de cada pasta
3. Coloque na linha do tempo
4. Ajuste a duração
5. Exporte em 1080p
Feito com ✨ Central Novel
"""
        zf.writestr("INSTRUCOES.txt", inst)

    zip_buf.seek(0)
    return send_file(zip_buf, as_attachment=True, download_name="pacote_novel.zip")

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=porta)
