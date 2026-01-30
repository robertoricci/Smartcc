import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

# =====================================================
# CONFIG
# =====================================================
st.set_page_config("Corte Certo MDF", layout="wide")
st.title("🪚 Diagrama de Otimização — MDF")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("📐 Dados da Chapa")
CH_L = st.sidebar.number_input("Comprimento (mm)", 2750)
CH_A = st.sidebar.number_input("Largura (mm)", 1850)
ESPESSURA = st.sidebar.number_input("Espessura MDF (mm)", 18)
KERF = st.sidebar.number_input("Espessura do Corte (mm)", 5)

# =====================================================
# PEÇAS
# =====================================================
st.header("📦 Peças")

if "pecas" not in st.session_state:
    st.session_state.pecas = []

with st.form("form"):
    c1, c2, c3, c4 = st.columns(4)
    nome = c1.text_input("Nome", "PRATELEIRA")
    w = c2.number_input("Comprimento", 1)
    h = c3.number_input("Largura", 1)
    q = c4.number_input("Qtd", 1)
    add = st.form_submit_button("Adicionar")

    if add:
        for _ in range(q):
            st.session_state.pecas.append((nome, w, h))

if st.session_state.pecas:
    st.table(st.session_state.pecas)

# =====================================================
# MOTOR DE FAIXAS (CORTE CERTO REAL)
# =====================================================
def gerar_chapas(pecas):
    chapas = []
    restantes = pecas[:]

    while restantes:
        chapa = []
        y = 0

        restantes.sort(key=lambda p: p[2], reverse=True)

        while restantes and y < CH_A:
            altura_faixa = restantes[0][2]
            x = 0
            usados = []

            for nome, w, h in restantes:
                if h <= altura_faixa and x + w <= CH_L:
                    chapa.append({
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                        "nome": nome
                    })
                    x += w + KERF
                    usados.append((nome, w, h))

            for u in usados:
                restantes.remove(u)

            y += altura_faixa + KERF

        chapas.append(chapa)

    return chapas

# =====================================================
# DESENHO — IGUAL CORTE CERTO
# =====================================================
def desenhar_chapa(chapa, idx):
    fig, ax = plt.subplots(figsize=(15, 7))
    margem = 80

    # CHAPA
    ax.add_patch(Rectangle(
        (margem, margem),
        CH_L, CH_A,
        facecolor="#DDDDDD",
        edgecolor="black",
        linewidth=2
    ))

    # FAIXAS
    faixas_y = sorted(set([p["y"] for p in chapa]))
    for y in faixas_y:
        ax.plot(
            [margem, margem + CH_L],
            [y + margem, y + margem],
            linestyle="--",
            color="black",
            linewidth=0.8
        )

    # PEÇAS
    for p in chapa:
        ax.add_patch(Rectangle(
            (p["x"] + margem, p["y"] + margem),
            p["w"], p["h"],
            facecolor="#F28C28",
            edgecolor="black",
            linewidth=1
        ))

        ax.text(
            p["x"] + margem + p["w"] / 2,
            p["y"] + margem + p["h"] / 2,
            f'{p["nome"]}\n{p["w"]} × {p["h"]} mm',
            ha="center",
            va="center",
            fontsize=8,
            weight="bold"
        )

    # CORTES VERTICAIS
    cortes_x = sorted(set([p["x"] + p["w"] for p in chapa]))
    for x in cortes_x:
        ax.plot(
            [x + margem, x + margem],
            [margem, margem + CH_A],
            linestyle="--",
            color="black",
            linewidth=0.8
        )

    # CABEÇALHO
    ax.text(
        margem,
        margem - 35,
        f"Diagrama de Otimização — MDF Branco {ESPESSURA}mm ({CH_L} × {CH_A} mm)",
        fontsize=13,
        weight="bold"
    )

    ax.text(
        margem,
        margem - 15,
        f"Espessura do Corte: {KERF} mm",
        fontsize=9
    )

    ax.set_xlim(0, CH_L + margem * 2)
    ax.set_ylim(0, CH_A + margem * 2)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")

    return fig

# =====================================================
# PDF
# =====================================================
def gerar_pdf(chapas):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for i, chapa in enumerate(chapas):
        fig = desenhar_chapa(chapa, i)
        img = BytesIO()
        fig.savefig(img, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        img.seek(0)

        c.drawImage(img, 30, 90, width=530, preserveAspectRatio=True)
        c.drawString(30, 820, f"Plano de Corte — Chapa {i+1}")
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# =====================================================
# EXECUTAR
# =====================================================
if st.button("🚀 Gerar Plano de Corte"):
    if not st.session_state.pecas:
        st.warning("Cadastre as peças.")
    else:
        chapas = gerar_chapas(st.session_state.pecas)
        st.success(f"📦 Chapas necessárias: {len(chapas)}")

        for i, chapa in enumerate(chapas):
            st.pyplot(desenhar_chapa(chapa, i), use_container_width=True)

        pdf = gerar_pdf(chapas)
        st.download_button(
            "⬇️ Baixar PDF",
            pdf,
            "plano_corte_mdf.pdf",
            "application/pdf"
        )
