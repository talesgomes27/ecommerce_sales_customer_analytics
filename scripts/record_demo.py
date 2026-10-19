"""Script de gravação automatizada de demo do simulador Streamlit (6 frames).

Uso:
    uv run python scripts/record_demo.py

Saída:
    docs/assets/demo_simulator.gif
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

# Ignorar proxy de sandbox para comunicação com servidor local
os.environ["NO_PROXY"] = "localhost,127.0.0.1,*"
os.environ["no_proxy"] = "localhost,127.0.0.1,*"

# Configurações
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_GIF = Path("docs/assets/demo_simulator.gif")
FRAMES_DIR = Path("/tmp/streamlit_frames")
FRAME_DURATION_MS = 2500  # 2.5s por frame para leitura confortável (6 frames * 2.5s = 15s)
VIEWPORT = {"width": 1440, "height": 900}

# Seletores
SELECTOR_TITLE = "text=Simulador Estratégico de Precificação"
SELECTOR_DISCOUNT_SLIDER = "div[data-testid='stSlider'] >> nth=0"
SELECTOR_TOGGLE_ML = "text=Principal (ML LightGBM)"
SELECTOR_TOGGLE_HEURISTIC = "text=Comparação (Heurística Calibrada)"


def file_hash(path: Path) -> str:
    """Calcula hash MD5 de um arquivo."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def start_streamlit() -> subprocess.Popen:
    """Inicia o Streamlit em background."""
    print("[1/8] Iniciando Streamlit...")
    env = os.environ.copy()
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "streamlit",
            "run",
            "app.py",
            "--server.headless",
            "true",
            "--server.port",
            "8501",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(6)  # Aguardar boot
    return proc


def capture_frames(page: Page, frames_dir: Path) -> list[Path]:
    """Captura frames sequenciais da interação cobrindo topo e os 3 gráficos."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames = []

    print("[2/8] Aguardando título...")
    page.wait_for_selector(SELECTOR_TITLE, timeout=15000)
    time.sleep(2)  # Aguardar render final

    # Garantir que começa no modo Heurística
    try:
        heur_btn = page.locator(SELECTOR_TOGGLE_HEURISTIC).first
        if heur_btn.is_visible():
            heur_btn.click(force=True)
            time.sleep(1.5)
            page.keyboard.press("Escape")
            time.sleep(0.5)
    except Exception as e:
        print(f"[AVISO] Configuração inicial Heurística: {e}")

    # --- FRAME 1: Topo (Heurística, 20% desconto) ---
    print("[3/8] Capturando Frame 1: Topo (Heurística segura, 20% desconto)...")
    frame_path_1 = frames_dir / "frame_01.png"
    page.screenshot(path=str(frame_path_1), full_page=False)
    frames.append(frame_path_1)

    # Ação 1: Mover slider de desconto para 45% (destruição de margem)
    print("[4/8] Movendo slider de desconto para 45%...")
    try:
        slider_bar = page.locator("[data-testid='stSliderTickBar']").first
        slider_bar.scroll_into_view_if_needed()
        box = slider_bar.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] * 0.50, box["y"] - 12)
            time.sleep(2)
        else:
            slider = page.locator("[data-testid='stSlider']").first
            slider_box = slider.bounding_box()
            if slider_box:
                page.mouse.click(
                    slider_box["x"] + slider_box["width"] * 0.50,
                    slider_box["y"] + slider_box["height"] * 0.70,
                )
                time.sleep(2)

        page.keyboard.press("Escape")
        time.sleep(0.5)
    except Exception as e:
        print(f"[AVISO] Não foi possível mover slider: {e}")

    # --- FRAME 2: Topo (45% desconto, margem negativa) ---
    print("[4/8] Capturando Frame 2: Topo (Desconto 45%, margem negativa)...")
    frame_path_2 = frames_dir / "frame_02.png"
    page.screenshot(path=str(frame_path_2), full_page=False)
    frames.append(frame_path_2)

    # Ação 2: Alternar para modo ML
    print("[5/8] Alternando para modo ML...")
    try:
        page.locator(SELECTOR_TOGGLE_ML).first.click(force=True, timeout=10000)
    except Exception as e1:
        print(f"[AVISO] Tentativa 1 falhou ({e1}). Tentando label...")
        try:
            page.locator("label").filter(has_text="Principal").first.click(force=True, timeout=5000)
        except Exception as e2:
            print(f"[AVISO] Tentativa 2 falhou ({e2}). Tentando via JS...")
            try:
                page.evaluate(
                    "() => { const el = Array.from(document.querySelectorAll('label, p')).find(e => e.textContent.includes('Principal (ML LightGBM)')); if (el) el.click(); }"
                )
            except Exception as e3:
                print(f"[AVISO] Não foi possível clicar no toggle ML: {e3}")

    time.sleep(3)  # Streamlit processa inferência ML
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # --- FRAME 3: Topo (Modo ML ativado) ---
    print("[5/8] Capturando Frame 3: Topo (Modo ML ativado)...")
    frame_path_3 = frames_dir / "frame_03.png"
    page.screenshot(path=str(frame_path_3), full_page=False)
    frames.append(frame_path_3)

    # --- FRAME 4: Gráfico 1 (Curva de Sensibilidade & Break-even) ---
    print("[6/8] Capturando Gráfico 1: Curva de Sensibilidade & Break-even...")
    try:
        tab1 = page.locator("text=Curva de Sensibilidade & Break-even").first
        tab1.click(force=True, timeout=5000)
        time.sleep(1)
    except Exception as e:
        print(f"[AVISO] Erro ao selecionar aba 1: {e}")

    # Rolar suavemente para enquadrar os gráficos
    page.mouse.wheel(0, 520)
    time.sleep(2)  # Aguardar render do Plotly

    frame_path_4 = frames_dir / "frame_04.png"
    page.screenshot(path=str(frame_path_4), full_page=False)
    frames.append(frame_path_4)

    # --- FRAME 5: Gráfico 2 (Waterfall DRE) ---
    print("[7/8] Capturando Gráfico 2: Waterfall DRE...")
    try:
        tab2 = page.locator("text=Decomposição DRE (Waterfall)").first
        tab2.scroll_into_view_if_needed()
        tab2.click(force=True, timeout=5000)
        time.sleep(2)  # Aguardar render do Plotly Waterfall
    except Exception as e:
        print(f"[AVISO] Erro ao selecionar aba 2: {e}")

    frame_path_5 = frames_dir / "frame_05.png"
    page.screenshot(path=str(frame_path_5), full_page=False)
    frames.append(frame_path_5)

    # --- FRAME 6: Gráfico 3 / Tabela (Matriz Paramétrica de Simulação) ---
    print("[8/8] Capturando Gráfico 3: Matriz Paramétrica de Simulação...")
    try:
        tab3 = page.locator("text=Matriz Paramétrica de Simulação").first
        tab3.scroll_into_view_if_needed()
        tab3.click(force=True, timeout=5000)
        time.sleep(2)  # Aguardar render da tabela/matriz
    except Exception as e:
        print(f"[AVISO] Erro ao selecionar aba 3: {e}")

    frame_path_6 = frames_dir / "frame_06.png"
    page.screenshot(path=str(frame_path_6), full_page=False)
    frames.append(frame_path_6)

    # Validação dos 6 frames
    if len(frames) == 6:
        hashes = [file_hash(f) for f in frames]
        all_distinct = len(set(hashes)) == len(hashes)
        for i, h in enumerate(hashes, 1):
            print(f"MD5 Frame {i}: {h[:8]}")
        if all_distinct:
            print(
                "[OK] Todos os 6 frames são 100% distintos e capturam a jornada analítica completa!"
            )
        else:
            print("[AVISO] Há frames repetidos na sequência capturada.")

    return frames


def build_gif(frames: list[Path], output: Path, duration_ms: int) -> None:
    """Monta o GIF a partir dos frames."""
    output.parent.mkdir(parents=True, exist_ok=True)
    images = [Image.open(f) for f in frames]

    # Converter para paleta adaptativa mantendo tamanho otimizado (< 1 MB)
    quantized_images = [img.convert("RGB").quantize(colors=128) for img in images]

    quantized_images[0].save(
        output,
        save_all=True,
        append_images=quantized_images[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    size_mb = output.stat().st_size / (1024 * 1024)
    print(
        f"[OK] GIF gerado: {output} ({size_mb:.2f} MB, {len(frames)} frames, {len(frames) * duration_ms / 1000:.1f}s total)"
    )


def main() -> None:
    proc = None
    try:
        proc = start_streamlit()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-web-security", "--no-sandbox"],
            )
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()

            print(f"Navegando para {STREAMLIT_URL}...")
            page.goto(STREAMLIT_URL, wait_until="domcontentloaded")

            frames = capture_frames(page, FRAMES_DIR)
            build_gif(frames, OUTPUT_GIF, FRAME_DURATION_MS)

            browser.close()

    except Exception as e:
        print(f"[ERRO FATAL] {type(e).__name__}: {e}")
        print("O GIF NÃO foi gerado.")
    finally:
        if proc:
            print("Encerrando Streamlit...")
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == "__main__":
    main()
