from flask import Flask, render_template_string, request, jsonify, send_file, after_this_request
import os
import re
import io
import requests
import tempfile
import json
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, TextClip, concatenate_videoclips

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
        "capa": "https://picsum.photos/id/237/600/400",
        "genero": "Fantasia / Ação"
    },
    {
        "titulo": "A Vilã Rejeitada Renascida",
        "resumo": "Uma leitora morre e renasce no corpo da vilã de um romance que conhece de cor. Sabendo que está destinada a morrer, ela rejeita o príncipe e conquista seu próprio poder para mudar o destino.",
        "capa": "https://picsum.photos/id/22/600/400",
        "genero": "Isekai / Romance"
    },
    {
        "titulo": "Código & Cultivo Digital",
        "resumo": "Um programador acorda em um universo onde códigos são magia. Para sobreviver, precisa dominar a 'linguagem dos deuses', subir de nível e descobrir por que foi trazido para lá.",
        "capa": "https://picsum.photos/id/180/600/400",
        "genero": "Sci-Fi / Cultivo"
    },
    {
        "titulo": "A Herdeira das Estrelas Perdidas",
        "resumo": "Filha esquecida de um império galáctico descobre seus poderes ao completar 18 anos. Deve viajar entre planetas para reunir fragmentos de um relicário e impedir uma guerra interestelar.",
        "capa": "https://picsum.photos/id/119/600/400",
        "genero": "Espaço / Aventura"
    },
    {
        "titulo": "O Último Guardião da Chama",
        "resumo": "O fogo sagrado que mantém o mundo vivo está apagando. O último portador do fogo precisa encontrar a Origem, enfrentar criaturas das trevas e reacender a esperança.",
        "capa": "https://picsum.photos/id/133/600/400",
        "genero": "Fantasia Épica"
    }
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR" class="dark scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovelToVision — Estúdio de Criação Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #030308;
            --accent-purple: #9333ea;
            --accent-pink: #ec4899;
            --accent-cyan: #06b6d4;
        }
        body {
            background-color: var(--bg-dark);
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #f3f4f6;
            overflow-x: hidden;
        }
        /* Glow Mesh Background */
        .glow-mesh {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: -1;
            background: 
                radial-gradient(circle at 15% 20%, rgba(147, 51, 234, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 85% 60%, rgba(236, 72, 153, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 50% 90%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
            filter: blur(40px);
        }
        /* Glassmorphism Ultra */
        .glass-card {
            background: rgba(13, 13, 26, 0.65);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
        }
        .glass-card:hover {
            border-color: rgba(147, 51, 234, 0.3);
        }
        .glass-input {
            background: rgba(5, 5, 12, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        .glass-input:focus {
            border-color: var(--accent-purple);
            box-shadow: 0 0 15px rgba(147, 51, 234, 0.3);
            outline: none;
        }
        /* Text Gradients */
        .text-gradient {
            background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .text-gradient-cyan {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        /* Botões Estilizados */
        .btn-gradient {
            background: linear-gradient(135deg, #9333ea 0%, #ec4899 100%);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 20px rgba(147, 51, 234, 0.3);
        }
        .btn-gradient:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(236, 72, 153, 0.5);
            filter: brightness(1.1);
        }
        .btn-gradient:active {
            transform: translateY(0);
        }
        /* Animações e Transições */
        .card-hover {
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .card-hover:hover {
            transform: translateY(-6px) scale(1.01);
            box-shadow: 0 20px 30px -10px rgba(147, 51, 234, 0.3);
        }
        @keyframes pulseGlow {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 0.8; }
        }
        .pulse-glow { animation: pulseGlow 3s infinite; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 99px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(147, 51, 234, 0.5); }
        
        /* Toast Notification */
        #toast {
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body class="min-h-screen relative custom-scrollbar">

    <!-- Fundo de iluminação dinâmica -->
    <div class="glow-mesh"></div>

    <!-- Toast Notification -->
    <div id="toast" class="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-gray-900/90 border border-purple-500/40 text-white px-5 py-3.5 rounded-2xl shadow-2xl backdrop-blur-xl">
        <i id="toastIcon" class="fa-solid fa-circle-check text-purple-400 text-lg"></i>
        <span id="toastMsg" class="text-sm font-medium">Ação concluída com sucesso!</span>
    </div>

    <!-- Navegação -->
    <header class="sticky top-0 z-40 border-b border-white/5 bg-black/40 backdrop-blur-xl">
        <div class="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                    <i class="fa-solid fa-wand-magic-sparkles text-white text-lg"></i>
                </div>
                <div>
                    <h1 class="text-xl font-extrabold tracking-wider text-white">Novel<span class="text-gradient">ToVision</span></h1>
                    <p class="text-[10px] text-gray-400 tracking-widest uppercase font-semibold">AI Video Generator Studio</p>
                </div>
            </div>
            
            <nav class="hidden md:flex items-center gap-1 bg-white/5 p-1.5 rounded-2xl border border-white/10">
                <a href="#busca" class="px-4 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/10 transition">
                    <i class="fa-solid fa-compass mr-1.5 text-purple-400"></i>Explorar
                </a>
                <a href="#editor" class="px-4 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/10 transition">
                    <i class="fa-solid fa-pen-nib mr-1.5 text-pink-400"></i>Editor
                </a>
                <a href="#personagens" class="px-4 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/10 transition">
                    <i class="fa-solid fa-microphone mr-1.5 text-cyan-400"></i>Vozes
                </a>
                <a href="#video" class="px-4 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/10 transition">
                    <i class="fa-solid fa-film mr-1.5 text-amber-400"></i>Estúdio Vídeo
                </a>
            </nav>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-10 space-y-16">

        <!-- HERO SECTION / BANNER -->
        <section class="relative rounded-3xl overflow-hidden p-8 md:p-12 glass-card border-purple-500/20">
            <div class="absolute -right-10 -bottom-10 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"></div>
            <div class="max-w-2xl space-y-4 relative z-10">
                <span class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-purple-500/10 border border-purple-500/30 text-purple-300 inline-flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                    Versão 2.0 Pro Ativa
                </span>
                <h2 class="text-3xl md:text-5xl font-black leading-tight tracking-tight">
                    Transforme <span class="text-gradient">Web Novels</span> em Vídeos Impressionantes
                </h2>
                <p class="text-gray-400 text-sm md:text-base font-normal leading-relaxed">
                    Converta capítulos, diálogos e narrações em curtas dinâmicos com narração por voz inteligente, formatação automática e legendas personalizadas em minutos.
                </p>
            </div>
        </section>

        <!-- === BUSCA DE NOVELS === -->
        <section id="busca" class="space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h3 class="text-2xl font-bold flex items-center gap-3">
                        <i class="fa-solid fa-fire text-purple-400"></i>
                        Explorar Biblioteca
                    </h3>
                    <p class="text-xs text-gray-400 mt-1">Selecione uma história pronta para testar o gerador instantaneamente.</p>
                </div>
                <div class="relative min-w-[300px]">
                    <i class="fa-solid fa-magnifying-glass absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                    <input type="text" id="termoBusca" onkeyup="buscarNovels()" placeholder="Pesquisar por título ou gênero..."
                        class="w-full pl-11 pr-4 py-3 rounded-2xl glass-input text-xs font-medium text-white placeholder-gray-500">
                </div>
            </div>

            <div id="resultadosBusca" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Cards renderizados via JS -->
            </div>
        </section>

        <!-- === EDITOR DE TEXTO === -->
        <section id="editor" class="space-y-6">
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="text-2xl font-bold flex items-center gap-3">
                        <i class="fa-solid fa-pen-to-square text-pink-400"></i>
                        Editor de Capítulos
                    </h3>
                    <p class="text-xs text-gray-400 mt-1">Escreva ou cole a história. Use a marcação <code class="text-pink-300">**Nome:** Fala</code> para atribuir vozes aos personagens.</p>
                </div>
                
                <!-- Indicadores dinâmicos -->
                <div class="hidden sm:flex items-center gap-4 text-xs text-gray-400 bg-white/5 px-4 py-2 rounded-xl border border-white/5">
                    <span><strong id="contadorCaracteres" class="text-purple-400">0</strong> Caracteres</span>
                    <span class="w-1 h-1 bg-gray-600 rounded-full"></span>
                    <span><strong id="contadorPalavras" class="text-pink-400">0</strong> Palavras</span>
                </div>
            </div>

            <div class="glass-card rounded-3xl p-4 border border-white/10 space-y-4">
                <textarea id="textoHistoria" rows="10" oninput="atualizarEstatisticas()"
                    class="w-full rounded-2xl glass-input p-5 text-sm leading-relaxed custom-scrollbar text-gray-200 placeholder-gray-600 focus:ring-0"
                    placeholder='Cole seu texto aqui... Exemplo:&#10;&#10;O vento soprava forte nas montanhas do sul.&#10;&#10;**Lira:** Nós não podemos recuar agora!&#10;&#10;**Kael:** Eu cubro a sua retaguarda. Avance!'>O sol se punha sobre a cidade antiga. Lira observava do alto da torre.

**Lira:** O que vamos fazer agora?

**Kael:** Vamos enfrentar o Reino das Sombras. Não há volta.

**Narrador:** E assim começou a jornada que mudaria tudo.</textarea>

                <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
                    <span class="text-xs text-gray-400 flex items-center gap-2">
                        <i class="fa-solid fa-circle-info text-purple-400"></i>
                        Parágrafos vazios dividem as cenas automaticamente.
                    </span>
                    <button onclick="processarTexto()" class="w-full sm:w-auto btn-gradient px-8 py-3.5 rounded-2xl text-xs font-bold tracking-wide uppercase flex items-center justify-center gap-2">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Analisar & Estruturar Cenas
                    </button>
                </div>
            </div>
        </section>

        <!-- === PERSONAGENS & VOZES === -->
        <section id="personagens" class="space-y-6">
            <div>
                <h3 class="text-2xl font-bold flex items-center gap-3">
                    <i class="fa-solid fa-microphone-lines text-cyan-400"></i>
                    Atribuição de Vozes
                </h3>
                <p class="text-xs text-gray-400 mt-1">Escolha o tom de voz ideal para cada personagem detectado no capítulo.</p>
            </div>

            <div id="listaPersonagens" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Personagens renderizados via JS -->
            </div>
        </section>

        <!-- === ESTÚDIO DE GERAÇÃO DE VÍDEO === -->
        <section id="video" class="space-y-6">
            <div>
                <h3 class="text-2xl font-bold flex items-center gap-3">
                    <i class="fa-solid fa-sliders text-amber-400"></i>
                    Configurações do Vídeo
                </h3>
                <p class="text-xs text-gray-400 mt-1">Ajuste o formato de renderização e estilos das legendas para sua rede social.</p>
            </div>

            <div class="glass-card rounded-3xl p-6 md:p-8 space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    <!-- Formato -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-purple-300">
                            <i class="fa-solid fa-mobile-screen mr-2"></i>Formato do Vídeo
                        </label>
                        <select id="videoFormato" class="w-full px-4 py-3.5 rounded-2xl glass-input text-xs font-medium text-white">
                            <option value="9:16">Vertical 9:16 (TikTok / Reels / Shorts)</option>
                            <option value="16:9">Horizontal 16:9 (YouTube Standard)</option>
                            <option value="1:1">Quadrado 1:1 (Feed Instagram)</option>
                        </select>
                    </div>

                    <!-- Duração -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-purple-300">
                            <i class="fa-regular fa-clock mr-2"></i>Duração Mín. por Cena
                        </label>
                        <select id="duracaoCena" class="w-full px-4 py-3.5 rounded-2xl glass-input text-xs font-medium text-white">
                            <option value="3">3 Segundos (Rápido)</option>
                            <option value="5" selected>5 Segundos (Recomendado)</option>
                            <option value="8">8 Segundos (Pausado)</option>
                        </select>
                    </div>

                    <!-- Legendas -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-purple-300">
                            <i class="fa-solid fa-closed-captioning mr-2"></i>Estilo das Legendas
                        </label>
                        <select id="estiloLegenda" class="w-full px-4 py-3.5 rounded-2xl glass-input text-xs font-medium text-white">
                            <option value="nenhuma">Sem Legendas</option>
                            <option value="branca" selected>Legenda Branca Clean</option>
                            <option value="amarela">Legenda Amarelo Neon (Destaque)</option>
                        </select>
                    </div>
                </div>

                <div class="pt-4 border-t border-white/5 flex flex-col items-center">
                    <button onclick="gerarVideo()" class="w-full md:w-auto btn-gradient px-12 py-4 rounded-2xl text-sm font-extrabold tracking-wider uppercase flex items-center justify-center gap-3">
                        <i class="fa-solid fa-clapperboard text-lg"></i> Gerar Vídeo Completo
                    </button>
                </div>

                <!-- Barra de Progresso Dinâmica -->
                <div id="progressoVideo" class="hidden space-y-3 p-6 rounded-2xl bg-black/40 border border-purple-500/20">
                    <div class="flex items-center justify-between text-xs font-semibold">
                        <span class="text-purple-300 flex items-center gap-2">
                            <i class="fa-solid fa-spinner animate-spin text-pink-400"></i>
                            Renderizando faixas de áudio e composições visuais...
                        </span>
                        <span id="porcentagemProgresso" class="text-pink-400">0%</span>
                    </div>
                    <div class="w-full bg-gray-800 h-2.5 rounded-full overflow-hidden p-0.5">
                        <div id="barraProgresso" class="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-400 rounded-full transition-all duration-300 w-0"></div>
                    </div>
                </div>

                <!-- Preview e Player de Vídeo Avançado -->
                <div id="previewVideo" class="hidden space-y-4 pt-4 border-t border-white/5">
                    <div class="flex items-center justify-between">
                        <h4 class="text-sm font-bold text-gray-200 flex items-center gap-2">
                            <i class="fa-solid fa-circle-play text-green-400"></i>
                            Pré-visualização do Resultado
                        </h4>
                        <div class="flex items-center gap-2">
                            <button onclick="alternarLoop()" id="btnLoop" class="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-gray-300 border border-white/10 transition">
                                <i class="fa-solid fa-repeat mr-1"></i> Loop
                            </button>
                        </div>
                    </div>

                    <div class="relative rounded-2xl overflow-hidden bg-black aspect-video max-h-[500px] flex items-center justify-center border border-white/10 shadow-2xl">
                        <video id="videoPlayer" class="w-full h-full object-contain" controls></video>
                    </div>

                    <div class="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2">
                        <a id="downloadVideo" href="#" download="novel_video.mp4" class="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-3.5 rounded-2xl text-xs font-bold tracking-wide uppercase transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30">
                            <i class="fa-solid fa-download"></i> Baixar Vídeo MP4
                        </a>
                    </div>
                </div>
            </div>

            <!-- Cenas Divididas -->
            <div id="cenasContainer" class="space-y-4">
                <!-- Cenas geradas aqui -->
            </div>
        </section>

    </main>

    <footer class="border-t border-white/5 py-8 mt-20 text-center text-xs text-gray-500">
        <p>NovelToVision Studio — Plataforma de Edição de Mídia Inteligente 🎬✨</p>
    </footer>

    <script>
        let cenas = [];
        let personagensDetectados = new Set();

        // Mostrar Toast Notification
        function showToast(mensagem, erro = false) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toastMsg');
            const toastIcon = document.getElementById('toastIcon');

            toastMsg.innerText = mensagem;
            if(erro) {
                toastIcon.className = "fa-solid fa-circle-xmark text-red-400 text-lg";
            } else {
                toastIcon.className = "fa-solid fa-circle-check text-purple-400 text-lg";
            }

            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3500);
        }

        // Estatísticas do Editor
        function atualizarEstatisticas() {
            const texto = document.getElementById('textoHistoria').value;
            document.getElementById('contadorCaracteres').innerText = texto.length;
            const palavras = texto.trim() ? texto.trim().split(/\\s+/).length : 0;
            document.getElementById('contadorPalavras').innerText = palavras;
        }

        // Buscar Novels na Rota API
        async function buscarNovels() {
            const termo = document.getElementById('termoBusca').value.trim();
            const container = document.getElementById('resultadosBusca');
            
            try {
                const res = await fetch(`/api/buscar-novels?q=${encodeURIComponent(termo)}`);
                const dados = await res.json();
                
                container.innerHTML = '';
                if (dados.length === 0) {
                    container.innerHTML = '<p class="text-xs text-gray-500 col-span-full text-center py-8">Nenhuma história encontrada com este termo.</p>';
                    return;
                }
                
                dados.forEach(n => {
                    const card = document.createElement('div');
                    card.className = 'glass-card rounded-2xl p-5 card-hover cursor-pointer space-y-4 border border-white/5 flex flex-col justify-between';
                    card.onclick = () => usarNovel(n.titulo, n.resumo);
                    card.innerHTML = `
                        <div class="space-y-3">
                            <div class="relative h-40 rounded-xl overflow-hidden">
                                <img src="${n.capa}" alt="${n.titulo}" class="w-full h-full object-cover">
                                <span class="absolute top-3 left-3 bg-black/60 backdrop-blur-md text-purple-300 text-[10px] font-bold px-3 py-1 rounded-full border border-white/10">
                                    ${n.genero}
                                </span>
                            </div>
                            <h4 class="font-bold text-base text-gray-100 leading-snug">${n.titulo}</h4>
                            <p class="text-xs text-gray-400 line-clamp-3 leading-relaxed">${n.resumo}</p>
                        </div>
                        <div class="pt-2 flex items-center justify-between text-xs font-semibold text-purple-400 group">
                            <span>Usar esta história</span>
                            <i class="fa-solid fa-arrow-right transform group-hover:translate-x-1 transition"></i>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch (err) {
                showToast("Erro ao carregar lista de novels.", true);
            }
        }

        function usarNovel(titulo, resumo) {
            document.getElementById('textoHistoria').value = `# ${titulo}\\n\\n${resumo}`;
            atualizarEstatisticas();
            showToast("Capítulo carregado no editor!");
            window.scrollTo({top: document.getElementById('editor').offsetTop - 100, behavior: 'smooth'});
        }

        // Processar Texto
        function processarTexto() {
            const texto = document.getElementById('textoHistoria').value;
            personagensDetectados.clear();
            cenas = [];
            
            const padraoFala = /\\*\\*([^*]+?)\\*\\*:/g;
            let match;
            while ((match = padraoFala.exec(texto)) !== null) {
                personagensDetectados.add(match[1].trim());
            }
            
            const lista = document.getElementById('listaPersonagens');
            lista.innerHTML = '';
            
            if (personagensDetectados.size === 0) {
                lista.innerHTML = `
                    <div class="col-span-full p-4 rounded-2xl bg-white/5 border border-white/5 text-center text-xs text-gray-400">
                        Nenhum diálogo com formato <code>**Nome:** Fala</code> foi detectado. Toda a narração usará a voz Padrão/Narrador.
                    </div>`;
            } else {
                personagensDetectados.forEach(p => {
                    lista.innerHTML += `
                    <div class="glass-card p-4 rounded-2xl border border-white/10 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-purple-300 flex items-center gap-2">
                                <i class="fa-solid fa-user-tag text-pink-400"></i> ${p}
                            </span>
                        </div>
                        <select class="w-full px-3 py-2 rounded-xl glass-input text-xs text-white" data-personagem="${p}">
                            <option value="narrador">Narrador / Neutro</option>
                            <option value="heroi">Herói (Enérgico)</option>
                            <option value="vilao">Vilão (Grave)</option>
                            <option value="princesa">Princesa (Suave)</option>
                            <option value="misterioso">Misterioso</option>
                            <option value="anciao">Ancião (Sábio)</option>
                        </select>
                    </div>`;
                });
            }
            
            const blocos = texto.split(/\\n\\s*\\n/);
            const cenasContainer = document.getElementById('cenasContainer');
            cenasContainer.innerHTML = '';
            
            blocos.forEach((bloco, idx) => {
                const limpo = bloco.trim();
                if (!limpo) return;
                cenas.push({id: idx + 1, texto: limpo});
                cenasContainer.innerHTML += `
                <div class="glass-card p-5 rounded-2xl border border-white/5 space-y-2">
                    <div class="flex items-center justify-between text-xs font-bold text-gray-400">
                        <span class="text-pink-400">Cena ${idx + 1}</span>
                        <span>${limpo.length} caracteres</span>
                    </div>
                    <p class="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">${limpo}</p>
                </div>`;
            });
            
            showToast(`${cenas.length} Cenas estruturadas com sucesso!`);
            window.scrollTo({top: document.getElementById('personagens').offsetTop - 100, behavior: 'smooth'});
        }

        // Gerar Vídeo
        async function gerarVideo() {
            if (cenas.length === 0) {
                showToast('Processe a história no editor antes de gerar o vídeo!', true);
                return;
            }

            const selecoes = {};
            document.querySelectorAll('[data-personagem]').forEach(s => {
                selecoes[s.dataset.personagem] = s.value;
            });

            const progressoBox = document.getElementById('progressoVideo');
            const barra = document.getElementById('barraProgresso');
            const porcentagem = document.getElementById('porcentagemProgresso');

            progressoBox.classList.remove('hidden');
            document.getElementById('previewVideo').classList.add('hidden');
            
            // Animação de carregamento simulada
            let progress = 10;
            barra.style.width = progress + '%';
            porcentagem.innerText = progress + '%';

            const timer = setInterval(() => {
                if(progress < 85) {
                    progress += Math.floor(Math.random() * 8) + 2;
                    barra.style.width = progress + '%';
                    porcentagem.innerText = progress + '%';
                }
            }, 800);

            try {
                const res = await fetch('/api/gerar-video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        cenas: cenas,
                        vozesSelecionadas: selecoes,
                        formato: document.getElementById('videoFormato').value,
                        duracaoCena: parseInt(document.getElementById('duracaoCena').value),
                        legenda: document.getElementById('estiloLegenda').value
                    })
                });

                clearInterval(timer);

                if (!res.ok) throw new Error("Erro na geração do vídeo");

                const blob = await res.blob();
                const url = URL.createObjectURL(blob);

                barra.style.width = '100%';
                porcentagem.innerText = '100%';

                setTimeout(() => {
                    document.getElementById('videoPlayer').src = url;
                    document.getElementById('downloadVideo').href = url;
                    document.getElementById('previewVideo').classList.remove('hidden');
                    progressoBox.classList.add('hidden');
                    showToast('Vídeo gerado com sucesso!');
                }, 500);

            } catch (erro) {
                clearInterval(timer);
                progressoBox.classList.add('hidden');
                showToast('Falha na renderização do vídeo.', true);
            }
        }

        function alternarLoop() {
            const player = document.getElementById('videoPlayer');
            const btn = document.getElementById('btnLoop');
            player.loop = !player.loop;
            if(player.loop) {
                btn.classList.add('bg-purple-600/40', 'border-purple-500');
            } else {
                btn.classList.remove('bg-purple-600/40', 'border-purple-500');
            }
        }

        // Inicializações
        buscarNovels();
        atualizarEstatisticas();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/buscar-novels")
def api_buscar_novels():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify(BANCO_NOVELS)
    filtrados = [
        n for n in BANCO_NOVELS
        if q in n["titulo"].lower() or q in n["genero"].lower() or q in n["resumo"].lower()
    ]
    return jsonify(filtrados)

@app.route("/api/gerar-video", methods=["POST"])
def api_gerar_video():
    dados = request.get_json() or {}
    cenas = dados.get("cenas", [])
    vozes_selecionadas = dados.get("vozesSelecionadas", {})
    formato = dados.get("formato", "9:16")
    duracao_cena = dados.get("duracaoCena", 5)
    estilo_legenda = dados.get("legenda", "nenhuma")

    dims = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
    largura, altura = dims.get(formato, (1080, 1920))

    temp_files = []
    clips = []

    try:
        for idx, cena in enumerate(cenas):
            texto_cena = cena["texto"]

            def processar_fala(match):
                nome = match.group(1).strip()
                fala = match.group(2).strip()
                voz_id = vozes_selecionadas.get(nome, "narrador")
                prefixo = VOZES_DISPONIVEIS.get(voz_id, {}).get("prefixo", "")
                return f"{prefixo}{fala}"

            texto_processado = re.sub(r"\*\*([^*]+?)\*\*:\s*(.+)", processar_fala, texto_cena)
            texto_final = re.sub(r"\*\*([^*]+)\*\*", r"\1", texto_processado)

            # Áudio TTS
            tts = gTTS(text=texto_final, lang="pt-BR", slow=False)
            f_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_files.append(f_audio.name)
            tts.save(f_audio.name)
            f_audio.close()

            audio_clip = AudioFileClip(f_audio.name)
            duracao = max(float(duracao_cena), audio_clip.duration)

            # Imagem de fundo
            img_url = f"https://picsum.photos/seed/{idx+300}/{largura}/{altura}"
            f_img = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            temp_files.append(f_img.name)
            
            response = requests.get(img_url, timeout=10)
            f_img.write(response.content)
            f_img.close()

            imagem_clip = ImageClip(f_img.name).set_duration(duracao)

            # Legendas
            if estilo_legenda != "nenhuma":
                cor = "white" if estilo_legenda == "branca" else "#fde047"
                texto_curto = texto_final[:80] + "..." if len(texto_final) > 80 else texto_final

                try:
                    txt_clip = TextClip(
                        texto_curto,
                        fontsize=42,
                        color=cor,
                        font="Arial-Bold",
                        method="caption",
                        size=(largura - 120, None)
                    ).set_position(("center", altura - 260)).set_duration(duracao)
                    imagem_clip = CompositeVideoClip([imagem_clip, txt_clip])
                except Exception as text_err:
                    print(f"TextClip Warning: {text_err}")

            imagem_clip = imagem_clip.set_audio(audio_clip)
            clips.append(imagem_clip)

        # Unir Cenas
        video_final = concatenate_videoclips(clips, method="compose")

        f_out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        out_path = f_out.name
        f_out.close()

        video_final.write_videofile(
            out_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(tempfile.gettempdir(), f"temp-audio-{os.getpid()}.m4a"),
            remove_temp=True
        )

        for c in clips:
            c.close()
        video_final.close()

        @after_this_request
        def cleanup(response):
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
            return response

        return send_file(out_path, mimetype="video/mp4", as_attachment=True, download_name="novel_video.mp4")

    except Exception as e:
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
