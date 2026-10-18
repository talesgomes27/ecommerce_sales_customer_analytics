"""Script de gravação automatizada de demo do simulador Streamlit.

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
FRAME_DURATION_MS = 1400  # 1.4s por frame
VIEWPORT = {"width": 1440, "height": 900}

# Seletores
SELECTOR_TITLE = "text=Simulador Estratégico de Precificação"
SELECTOR_TOGGLE_ML = "text=Principal (ML LightGBM)"
SELECTOR_TOGGLE_HEURISTIC = "text=Comparação (Heurística Calibrada)"


def file_hash(path: Path) -> str:
    """Calcula hash MD5 de um arquivo."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def start_streamlit() -> subprocess.Popen:
    """Inicia o Streamlit em background."""
    print("[1/5] Iniciando Streamlit...")
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
    """Captura frames sequenciais da interação."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames = []

    print("[2/5] Aguardando título...")
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

    # Frame 1: Estado inicial (Heurística, 20% desconto)
    print("[3/5] Capturando frame inicial (Heurística, 20% desconto)...")
    frame_path_1 = frames_dir / "frame_01.png"
    page.screenshot(path=str(frame_path_1), full_page=False)
    frames.append(frame_path_1)

    # Ação 1: Mover slider de desconto para 45% (destruição de margem)
    print("[4/5] Movendo slider de desconto para 45%...")
    try:
        slider_bar = page.locator("[data-testid='stSliderTickBar']").first
        slider_bar.scroll_into_view_if_needed()
        box = slider_bar.bounding_box()
        if box:
            # 45% é exatamente o meio (50%) da barra de 0 a 90; clicamos na linha do slider
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

    frame_path_2 = frames_dir / "frame_02.png"
    page.screenshot(path=str(frame_path_2), full_page=False)
    frames.append(frame_path_2)

    # Ação 2: Alternar para modo ML
    print("[5/5] Alternando para modo ML...")
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
                print(f"[AVISO] Não foi possível clicar no toggle ML após 3 tentativas: {e3}")

    time.sleep(3)  # Streamlit processa a inferência ML
    page.keyboard.press("Escape")
    time.sleep(0.5)

    frame_path_3 = frames_dir / "frame_03.png"
    page.screenshot(path=str(frame_path_3), full_page=False)
    frames.append(frame_path_3)

    # Validação dos 3 frames
    if len(frames) >= 3:
        h1 = file_hash(frames[0])
        h2 = file_hash(frames[1])
        h3 = file_hash(frames[2])
        diff_1_2 = h1 != h2
        diff_2_3 = h2 != h3
        print(f"MD5 Frame 1: {h1[:8]}")
        print(f"MD5 Frame 2: {h2[:8]} (Distinto do 1: {diff_1_2})")
        print(f"MD5 Frame 3: {h3[:8]} (Distinto do 2: {diff_2_3})")
        if not diff_1_2:
            print("[AVISO] Frame 2 idêntico ao Frame 1.")
        if not diff_2_3:
            print("[AVISO] Frame 3 idêntico ao Frame 2.")
        if diff_1_2 and diff_2_3:
            print("[OK] Todos os 3 frames são distintos e capturam a jornada completa!")

    return frames


def build_gif(frames: list[Path], output: Path, duration_ms: int) -> None:
    """Monta o GIF a partir dos frames."""
    output.parent.mkdir(parents=True, exist_ok=True)
    images = [Image.open(f) for f in frames]

    # Converter para paleta adaptativa para manter tamanho < 1MB
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
    print(f"[OK] GIF gerado: {output} ({size_mb:.2f} MB, {len(frames)} frames)")


def main() -> None:
    proc = None
    try:
        proc = start_streamlit()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--disable-web-security", "--no-sandbox"]
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
