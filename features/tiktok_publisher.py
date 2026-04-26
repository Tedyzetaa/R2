"""
R2 TACTICAL OS — TIKTOK COMMANDER V2.4 + ALPHA NEURAL
Projeto Manhattan — Motor de Disparo com Inteligência Cognitiva
"""

import threading
import time
import uuid
import re
import os
from datetime import datetime
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO GLOBAL
# ─────────────────────────────────────────────
HEADLESS_MODE     = False          # True após validação final
UPLOAD_TIMEOUT_MS = 120_000
PEAK_HOURS        = ["09:00", "12:00", "18:00", "20:00"]

GHOST_CSS = """
    #react-joyride-portal,
    .react-joyride__overlay,
    .tiktok-modal__mask,
    [class*="InteractiveTutorial"],
    [class*="GuideModal"],
    [data-e2e="guide-modal"] {
        display: none !important;
        pointer-events: none !important;
    }
"""


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def _gerar_titulo(nome_arquivo: str) -> str:
    base = os.path.splitext(os.path.basename(nome_arquivo))[0]
    base = re.sub(r"[_\-]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    return base.title()


def _gerar_hashtags(nome_arquivo: str) -> str:
    base = os.path.splitext(os.path.basename(nome_arquivo))[0]
    palavras = re.split(r"[_\-\s]+", base)
    tags = ["#" + p.lower() for p in palavras if len(p) > 2]
    tags_fixas = ["#viral", "#fyp", "#foryou"]
    return " ".join(dict.fromkeys(tags + tags_fixas))


def _proximo_horario_pico() -> str:
    agora = datetime.now()
    for h in PEAK_HOURS:
        hh, mm = map(int, h.split(":"))
        alvo = agora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if alvo > agora:
            return alvo.strftime("%Y-%m-%dT%H:%M")
    amanha = agora.replace(day=agora.day + 1)
    hh, mm = map(int, PEAK_HOURS[0].split(":"))
    return amanha.replace(hour=hh, minute=mm, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


# ─────────────────────────────────────────────
#  COMMANDER (INTEGRADO AO ALPHA)
# ─────────────────────────────────────────────
class TikTokCommander:
    def __init__(self, profile_dir: str = "tiktok_profile", alpha_engine=None):
        self.profile_dir  = os.path.abspath(profile_dir)
        self.alpha_engine = alpha_engine          # <-- Motor Alpha (opcional)
        self._page        = None                  # <-- Exposto para o Alpha
        self.fila: List[Dict] = []
        self._lock          = threading.Lock()
        self.radar_thread   = threading.Thread(target=self._radar_loop, daemon=True)
        self.radar_thread.start()

    @property
    def page(self):
        """Retorna a página ativa do Playwright para o Alpha Engine."""
        return self._page

    # ── FILA ────────────────────────────────
    def adicionar(
        self,
        video_path: str,
        titulo: Optional[str]    = None,
        descricao: Optional[str] = None,
        hashtags: Optional[str]  = None,
        agendar_para: Optional[str] = None,
    ) -> Dict:
        titulo    = titulo    or _gerar_titulo(video_path)
        hashtags  = hashtags  or _gerar_hashtags(video_path)
        descricao = descricao or titulo
        agendar   = agendar_para or _proximo_horario_pico()

        item = {
            "id":           str(uuid.uuid4())[:8],
            "video_path":   video_path,
            "titulo":       titulo,
            "descricao":    descricao,
            "hashtags":     hashtags,
            "agendar_para": agendar,
            "status":       "aguardando",
            "criado_em":    datetime.now().isoformat(),
            "log":          [],
        }
        with self._lock:
            self.fila.append(item)
        return item

    def get_fila(self) -> List[Dict]:
        with self._lock:
            return list(self.fila)

    def remover(self, item_id: str) -> bool:
        with self._lock:
            antes = len(self.fila)
            self.fila = [i for i in self.fila if i["id"] != item_id]
            return len(self.fila) < antes

    def _atualizar_status(self, item_id: str, status: str, msg: str = ""):
        with self._lock:
            for item in self.fila:
                if item["id"] == item_id:
                    item["status"] = status
                    if msg:
                        item["log"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # ── RADAR ────────────────────────────────
    def _radar_loop(self):
        while True:
            time.sleep(30)
            agora = datetime.now()
            with self._lock:
                candidatos = [
                    i for i in self.fila
                    if i["status"] == "aguardando"
                    and datetime.fromisoformat(i["agendar_para"]) <= agora
                ]
            for item in candidatos:
                self._atualizar_status(item["id"], "disparando", "Radar acionou disparo agendado.")
                threading.Thread(target=self._executar_disparo, args=(item,), daemon=True).start()

    def disparar_agora(self, item_id: str) -> Dict:
        with self._lock:
            item = next((i for i in self.fila if i["id"] == item_id), None)
        if not item:
            return {"ok": False, "erro": "Item não encontrado na fila."}
        if item["status"] in ("disparando", "publicado"):
            return {"ok": False, "erro": f"Status atual impede disparo: {item['status']}"}
        self._atualizar_status(item_id, "disparando", "Disparo manual acionado.")
        threading.Thread(target=self._executar_disparo, args=(item,), daemon=True).start()
        return {"ok": True, "id": item_id}

    # ── MOTOR V2.4 + ALPHA ─────────────────────
    def _executar_disparo(self, item: Dict):
        iid = item["id"]
        log = lambda msg: self._atualizar_status(iid, item["status"], msg)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.profile_dir,
                    headless=HEADLESS_MODE,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                    viewport={"width": 1280, "height": 800},
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                self._page = page   # expõe para o Alpha

                log("Abrindo TikTok Studio...")
                page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                # ── Injetar Ghost CSS (neutraliza overlays) ──
                page.evaluate("""(css) => {
                    var s = document.createElement('style');
                    s.innerHTML = css;
                    document.head.appendChild(s);
                }""", GHOST_CSS)
                log("Ghost CSS injetado — overlays neutralizados.")

                # ── Upload do vídeo ──
                log(f"Iniciando upload: {os.path.basename(item['video_path'])}")
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(item["video_path"])

                # ── Preencher metadados (descrição + hashtags) ──
                descricao_completa = f"{item['descricao']} {item['hashtags']}"
                try:
                    caption = page.locator("[data-e2e='caption-input'], .public-DraftEditor-content, div[contenteditable='true']").first
                    caption.click()
                    caption.fill("")
                    caption.type(descricao_completa, delay=30)
                    log(f"Descrição preenchida: {descricao_completa[:60]}...")
                except Exception as e:
                    log(f"Aviso metadados: {e}")

                # ── SE ALPHA ESTIVER PRESENTE, DELEGA O CICLO NEURAL ──
                if self.alpha_engine:
                    log("🔁 Ativando Alpha Engine para ciclo autônomo (Percepção → Inferência → Ação)")
                    self.alpha_engine.attach(page)
                    resultado = self.alpha_engine.run_until_success(max_cycles=25, delay_between=3.0)
                    if resultado.get("state") == "PUBLISH_SUCCESS":
                        self._atualizar_status(iid, "publicado", "✅ Alpha Engine concluiu a publicação com sucesso.")
                    else:
                        self._atualizar_status(iid, "erro", f"❌ Alpha finalizou com estado: {resultado.get('state')}")
                else:
                    # ── Fallback: vigilância clássica do botão (sem Alpha) ──
                    log("⚠️ Alpha Engine não disponível – usando fallback clássico.")
                    btn_publicar = self._aguardar_botao_publicar_fallback(page, iid)
                    if btn_publicar is None:
                        self._atualizar_status(iid, "erro", "Timeout: botão Publicar não ativou.")
                        browser.close()
                        return
                    # Fallback de clique via JavaScript
                    page.evaluate('''() => {
                        const btn = document.querySelector('button[data-e2e="upload-btn-post"]');
                        if (btn) btn.click();
                    }''')
                    page.wait_for_timeout(15000)
                    self._atualizar_status(iid, "publicado", "✅ Publicação concluída (fallback).")

                browser.close()

        except Exception as exc:
            self._atualizar_status(iid, "erro", f"Exceção: {exc}")

    def _aguardar_botao_publicar_fallback(self, page, iid: str):
        """Sonda o botão a cada 1.5s por até 3 minutos."""
        seletores = [
            "button[data-e2e='upload-btn-post']",
            "button.btn-post",
            "//button[contains(., 'Post') or contains(., 'Publicar')]",
        ]
        deadline = time.time() + 180
        while time.time() < deadline:
            for sel in seletores:
                try:
                    metodo = "xpath" if sel.startswith("//") else "css"
                    btn = page.locator(sel) if metodo == "css" else page.locator(f"xpath={sel}")
                    if btn.count() > 0 and btn.first.is_visible() and btn.first.is_enabled():
                        self._atualizar_status(iid, "disparando", "✔ Botão Publicar ativo (fallback).")
                        return btn.first
                except Exception:
                    pass
            page.wait_for_timeout(1500)
        return None