# malue-shows — encurtador central de links MaLuê
# ===================================================
# Recebe ?o=slug | ?c=slug | ?r=slug | ?cam=slug
# Resolve via Apps Script e redireciona pro destino real.
# O Apps Script registra o acesso (mantém o tracking) e retorna a URL.

import streamlit as st
import requests

# URL pública do Apps Script (mesma do webhook da agenda)
APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyhGtpoLzypPBo2csNL0c_z8k8S51A9nzXhLFGKrAQiB4D7hEec2RL6Wj4bBGWVBnCt/exec"
)

# Tipos suportados (chave de query param -> nome interno)
TIPOS = {
    "o":   "orcamento",
    "c":   "contrato",
    "r":   "rider",
    "cam": "camarim",
}

LABEL_TIPO = {
    "orcamento": "orçamento",
    "contrato":  "contrato",
    "rider":     "rider",
    "camarim":   "camarim",
}

st.set_page_config(page_title="MaLuê", page_icon="🎶", layout="centered")

# CSS minimalista — página de transição rápida
st.markdown(
    """
    <style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stToolbar"]{display:none}
      .block-container{padding-top:80px;padding-bottom:40px;max-width:560px}
      .malue-card{
        background:#fff;border-radius:18px;padding:32px 28px;
        box-shadow:0 8px 32px rgba(0,0,0,.08);text-align:center;
        font-family:-apple-system,system-ui,sans-serif;
      }
      .malue-logo{font-size:44px;font-weight:800;letter-spacing:-.5px;color:#222;margin:0}
      .malue-sub{color:#666;margin:4px 0 24px;font-size:15px}
      .malue-spin{
        width:36px;height:36px;border:3px solid #eee;border-top-color:#222;
        border-radius:50%;animation:spin 1s linear infinite;margin:8px auto;
      }
      @keyframes spin{to{transform:rotate(1turn)}}
      .malue-err{background:#fff4f4;border-left:4px solid #d32;padding:14px 16px;border-radius:8px;text-align:left;color:#622;margin-top:18px}
      .malue-help{color:#888;font-size:13px;margin-top:18px}
      .malue-help a{color:#666}
    </style>
    """,
    unsafe_allow_html=True,
)

params = st.query_params

# Descobre qual tipo + slug foi pedido
tipo_param = None
slug = None
for key, nome in TIPOS.items():
    if key in params:
        tipo_param = nome
        slug = params.get(key)
        break

def render_card(inner_html: str):
    st.markdown(
        f"""
        <div class="malue-card">
          <p class="malue-logo">MaLuê</p>
          <p class="malue-sub">🎶 música ao vivo</p>
          {inner_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

if not tipo_param or not slug:
    render_card(
        """
        <div class="malue-err">
          <strong>Link incompleto.</strong><br>
          Esse endereço não tem informação suficiente pra abrir o documento.
        </div>
        <p class="malue-help">
          Se você veio aqui por um link da MaLuê, peça pra pessoa reenviar.
        </p>
        """
    )
    st.stop()

# Mostra spinner enquanto resolve
spinner_placeholder = st.empty()
with spinner_placeholder.container():
    render_card(
        f"""
        <div class="malue-spin"></div>
        <p class="malue-sub">Abrindo seu {LABEL_TIPO.get(tipo_param, tipo_param)}…</p>
        """
    )

# Chama Apps Script pra resolver o slug
try:
    resp = requests.get(
        APPS_SCRIPT_URL,
        params={"action": "g", "type": tipo_param, "slug": slug},
        timeout=20,
        allow_redirects=False,
    )
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
except Exception:
    spinner_placeholder.empty()
    render_card(
        """
        <div class="malue-err">
          <strong>Não consegui abrir agora.</strong><br>
          Tentei buscar o documento mas algo deu errado.
        </div>
        <p class="malue-help">Tenta de novo em alguns segundos — se persistir, fale com a MaLuê.</p>
        """
    )
    st.stop()

if not data.get("ok") or not data.get("url"):
    spinner_placeholder.empty()
    motivo = data.get("error", "Não encontramos esse documento.")
    render_card(
        f"""
        <div class="malue-err">
          <strong>Documento não encontrado.</strong><br>
          {motivo}
        </div>
        <p class="malue-help">Confira o link ou peça pra MaLuê reenviar.</p>
        """
    )
    st.stop()

# Sucesso — redireciona via JS + meta refresh
dest = data["url"]
spinner_placeholder.empty()
st.markdown(
    f"""
    <meta http-equiv="refresh" content="0;url={dest}">
    <div class="malue-card">
      <p class="malue-logo">MaLuê</p>
      <div class="malue-spin"></div>
      <p class="malue-sub">Abrindo…</p>
      <p class="malue-help">
        Se não abrir em 2s, <a href="{dest}">clique aqui</a>.
      </p>
    </div>
    <script>window.location.replace({dest!r});</script>
    """,
    unsafe_allow_html=True,
)
