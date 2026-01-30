"""
CORTE CERTO - Sistema de Otimização de Cortes de MDF
Aplicação profissional para marcenarias
Autor: Sistema Corte Certo
Versão: 1.0
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple
import copy

# ============================================================================
# CLASSES DE DADOS
# ============================================================================

@dataclass
class Peca:
    """Representa uma peça a ser cortada"""
    nome: str
    comprimento: float  # mm
    largura: float  # mm
    quantidade: int
    
    def area(self) -> float:
        return self.comprimento * self.largura


@dataclass
class PecaPosicionada:
    """Peça com posição definida na chapa"""
    peca: Peca
    x: float
    y: float
    rotacionada: bool = False
    
    @property
    def comprimento_final(self) -> float:
        return self.peca.largura if self.rotacionada else self.peca.comprimento
    
    @property
    def largura_final(self) -> float:
        return self.peca.comprimento if self.rotacionada else self.peca.largura


@dataclass
class Faixa:
    """Faixa horizontal de corte"""
    y_inicio: float
    altura: float
    pecas: List[PecaPosicionada]
    
    def espaco_usado(self, kerf: float) -> float:
        """Calcula o espaço horizontal usado na faixa"""
        if not self.pecas:
            return 0
        total = sum(p.comprimento_final for p in self.pecas)
        total += kerf * (len(self.pecas) - 1) if len(self.pecas) > 1 else 0
        return total


@dataclass
class Chapa:
    """Chapa de MDF com peças posicionadas"""
    numero: int
    comprimento: float
    largura: float
    espessura: float
    kerf: float
    faixas: List[Faixa]
    
    def calcular_utilizacao(self) -> float:
        """Calcula percentual de aproveitamento da chapa"""
        area_total = self.comprimento * self.largura
        area_usada = sum(
            p.peca.comprimento * p.peca.largura
            for faixa in self.faixas
            for p in faixa.pecas
        )
        return (area_usada / area_total) * 100 if area_total > 0 else 0
    
    def calcular_desperdicio(self) -> float:
        """Calcula percentual de desperdício"""
        return 100 - self.calcular_utilizacao()


# ============================================================================
# ALGORITMO DE OTIMIZAÇÃO (STRIP PACKING)
# ============================================================================

class OtimizadorCortes:
    """Algoritmo de otimização baseado em faixas horizontais"""
    
    def __init__(self, comprimento_chapa: float, largura_chapa: float, 
                 espessura: float, kerf: float):
        self.comprimento_chapa = comprimento_chapa
        self.largura_chapa = largura_chapa
        self.espessura = espessura
        self.kerf = kerf
        self.chapas: List[Chapa] = []
    
    def otimizar(self, pecas: List[Peca]) -> List[Chapa]:
        """
        Algoritmo principal de otimização
        Estratégia: Strip Packing com ordenação por largura
        """
        # Expandir peças pela quantidade
        pecas_expandidas = []
        for peca in pecas:
            for i in range(peca.quantidade):
                pecas_expandidas.append(copy.deepcopy(peca))
        
        # Ordenar por largura decrescente (maior primeiro)
        pecas_ordenadas = sorted(
            pecas_expandidas,
            key=lambda p: p.largura,
            reverse=True
        )
        
        # Processar peças
        numero_chapa = 1
        while pecas_ordenadas:
            chapa = self._criar_chapa(numero_chapa, pecas_ordenadas)
            self.chapas.append(chapa)
            numero_chapa += 1
        
        return self.chapas
    
    def _criar_chapa(self, numero: int, pecas_disponiveis: List[Peca]) -> Chapa:
        """Cria uma chapa e tenta alocar o máximo de peças possível"""
        faixas = []
        y_atual = 0
        
        while y_atual < self.largura_chapa and pecas_disponiveis:
            # Criar nova faixa
            faixa = self._criar_faixa(y_atual, pecas_disponiveis)
            
            if not faixa.pecas:
                # Não conseguiu alocar nenhuma peça
                break
            
            faixas.append(faixa)
            y_atual += faixa.altura + self.kerf
        
        return Chapa(
            numero=numero,
            comprimento=self.comprimento_chapa,
            largura=self.largura_chapa,
            espessura=self.espessura,
            kerf=self.kerf,
            faixas=faixas
        )
    
    def _criar_faixa(self, y_inicio: float, pecas_disponiveis: List[Peca]) -> Faixa:
        """Cria uma faixa horizontal e aloca peças"""
        altura_faixa = 0
        pecas_faixa = []
        x_atual = 0
        
        # Encontrar primeira peça que cabe na largura restante
        i = 0
        while i < len(pecas_disponiveis):
            peca = pecas_disponiveis[i]
            
            # Verificar se cabe na largura da chapa
            if y_inicio + peca.largura > self.largura_chapa:
                i += 1
                continue
            
            # Definir altura da faixa (primeira peça)
            if altura_faixa == 0:
                altura_faixa = peca.largura
            
            # Verificar se a peça tem a mesma largura da faixa
            if abs(peca.largura - altura_faixa) < 0.1:
                # Verificar se cabe horizontalmente
                espaco_necessario = peca.comprimento
                if pecas_faixa:
                    espaco_necessario += self.kerf
                
                if x_atual + espaco_necessario <= self.comprimento_chapa:
                    # Alocar peça
                    peca_posicionada = PecaPosicionada(
                        peca=peca,
                        x=x_atual,
                        y=y_inicio,
                        rotacionada=False
                    )
                    pecas_faixa.append(peca_posicionada)
                    x_atual += peca.comprimento + self.kerf
                    
                    # Remover peça da lista
                    pecas_disponiveis.pop(i)
                    continue
            
            i += 1
        
        return Faixa(
            y_inicio=y_inicio,
            altura=altura_faixa,
            pecas=pecas_faixa
        )


# ============================================================================
# GERADOR DE DIAGRAMA TÉCNICO
# ============================================================================

class GeradorDiagrama:
    """Gera diagramas técnicos estilo Corte Certo"""
    
    # Cores padrão (estilo Corte Certo)
    COR_CHAPA = '#E8E8E8'
    COR_PECA = '#FF8C42'
    COR_LINHA = '#333333'
    COR_TEXTO = '#000000'
    COR_LINHA_TRACEJADA = '#666666'
    
    def __init__(self, chapa: Chapa):
        self.chapa = chapa
    
    def gerar_diagrama(self, dpi: int = 150) -> plt.Figure:
        """Gera o diagrama técnico da chapa"""
        # Calcular tamanho da figura proporcional
        aspecto = self.chapa.comprimento / self.chapa.largura
        largura_fig = 12
        altura_fig = largura_fig / aspecto
        
        fig, ax = plt.subplots(figsize=(largura_fig, altura_fig), dpi=dpi)
        
        # Remover eixos e grid (visual técnico limpo)
        ax.set_xlim(0, self.chapa.comprimento)
        ax.set_ylim(0, self.chapa.largura)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Desenhar chapa (fundo cinza)
        chapa_rect = patches.Rectangle(
            (0, 0),
            self.chapa.comprimento,
            self.chapa.largura,
            linewidth=2,
            edgecolor=self.COR_LINHA,
            facecolor=self.COR_CHAPA,
            zorder=1
        )
        ax.add_patch(chapa_rect)
        
        # Desenhar faixas e peças
        for faixa in self.chapa.faixas:
            # Linha tracejada da faixa (horizontal)
            ax.plot(
                [0, self.chapa.comprimento],
                [faixa.y_inicio, faixa.y_inicio],
                color=self.COR_LINHA_TRACEJADA,
                linestyle='--',
                linewidth=0.8,
                alpha=0.6,
                zorder=2
            )
            
            # Desenhar peças
            for peca_pos in faixa.pecas:
                # Retângulo da peça (laranja)
                rect = patches.Rectangle(
                    (peca_pos.x, peca_pos.y),
                    peca_pos.comprimento_final,
                    peca_pos.largura_final,
                    linewidth=1.5,
                    edgecolor=self.COR_LINHA,
                    facecolor=self.COR_PECA,
                    zorder=3
                )
                ax.add_patch(rect)
                
                # Linhas de corte verticais (tracejadas)
                if peca_pos.x > 0:
                    ax.plot(
                        [peca_pos.x, peca_pos.x],
                        [peca_pos.y, peca_pos.y + peca_pos.largura_final],
                        color=self.COR_LINHA_TRACEJADA,
                        linestyle='--',
                        linewidth=0.8,
                        alpha=0.6,
                        zorder=2
                    )
                
                # Texto da peça (nome e dimensões)
                centro_x = peca_pos.x + peca_pos.comprimento_final / 2
                centro_y = peca_pos.y + peca_pos.largura_final / 2
                
                # Nome
                ax.text(
                    centro_x,
                    centro_y + peca_pos.largura_final * 0.15,
                    peca_pos.peca.nome,
                    ha='center',
                    va='center',
                    fontsize=8,
                    fontweight='bold',
                    color=self.COR_TEXTO,
                    zorder=4
                )
                
                # Dimensões
                dimensoes = f"{int(peca_pos.peca.comprimento)} × {int(peca_pos.peca.largura)} mm"
                ax.text(
                    centro_x,
                    centro_y - peca_pos.largura_final * 0.15,
                    dimensoes,
                    ha='center',
                    va='center',
                    fontsize=7,
                    color=self.COR_TEXTO,
                    zorder=4
                )
        
        # Adicionar cabeçalho técnico
        self._adicionar_cabecalho(ax)
        
        plt.tight_layout(pad=0.5)
        return fig
    
    def _adicionar_cabecalho(self, ax):
        """Adiciona cabeçalho técnico ao diagrama"""
        # Título
        titulo = f"DIAGRAMA DE OTIMIZAÇÃO — CHAPA {self.chapa.numero}"
        ax.text(
            self.chapa.comprimento / 2,
            self.chapa.largura * 1.08,
            titulo,
            ha='center',
            va='bottom',
            fontsize=14,
            fontweight='bold',
            color=self.COR_LINHA
        )
        
        # Informações técnicas
        info = (
            f"MDF {int(self.chapa.espessura)}mm  |  "
            f"Chapa: {int(self.chapa.comprimento)} × {int(self.chapa.largura)} mm  |  "
            f"Kerf: {self.chapa.kerf}mm  |  "
            f"Aproveitamento: {self.chapa.calcular_utilizacao():.1f}%"
        )
        ax.text(
            self.chapa.comprimento / 2,
            self.chapa.largura * 1.04,
            info,
            ha='center',
            va='bottom',
            fontsize=9,
            color=self.COR_LINHA
        )


# ============================================================================
# GERADOR DE PDF PROFISSIONAL
# ============================================================================

class GeradorPDF:
    """Gera PDF técnico pronto para impressão"""
    
    def __init__(self, chapas: List[Chapa]):
        self.chapas = chapas
    
    def gerar_pdf(self) -> BytesIO:
        """Gera PDF com todas as chapas (uma por página)"""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        largura_pagina, altura_pagina = A4
        
        for chapa in self.chapas:
            # Gerar diagrama
            gerador = GeradorDiagrama(chapa)
            fig = gerador.gerar_diagrama(dpi=150)
            
            # Converter figura para imagem usando savefig
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            
            # Abrir com PIL e converter para ImageReader
            pil_image = Image.open(img_buffer)
            img_reader = ImageReader(pil_image)
            
            # Calcular dimensões para centralizar na página
            img_width, img_height = pil_image.size
            scale = min(
                (largura_pagina - 50) / img_width,
                (altura_pagina - 100) / img_height
            )
            
            nova_largura = img_width * scale
            nova_altura = img_height * scale
            
            x = (largura_pagina - nova_largura) / 2
            y = (altura_pagina - nova_altura) / 2 + 20
            
            # Desenhar imagem no PDF
            pdf.drawImage(
                img_reader,
                x, y,
                width=nova_largura,
                height=nova_altura,
                preserveAspectRatio=True
            )
            
            # Adicionar rodapé
            pdf.setFont("Helvetica", 8)
            pdf.drawString(
                30,
                20,
                f"Chapa {chapa.numero} de {len(self.chapas)} | "
                f"Corte Certo - Sistema de Otimização de Cortes"
            )
            
            # Próxima página
            pdf.showPage()
            
            # Limpar figura
            plt.close(fig)
            img_buffer.close()
        
        pdf.save()
        buffer.seek(0)
        return buffer


# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

def main():
    st.set_page_config(
        page_title="Corte Certo - Otimizador de MDF",
        page_icon="🪚",
        layout="wide"
    )
    
    # Título principal
    st.title("🪚 CORTE CERTO")
    st.subheader("Sistema Profissional de Otimização de Cortes de MDF")
    
    # ========================================================================
    # SIDEBAR - CONFIGURAÇÕES
    # ========================================================================
    
    with st.sidebar:
        st.header("⚙️ Configurações da Chapa")
        
        comprimento_chapa = st.number_input(
            "Comprimento da chapa (mm)",
            min_value=100,
            max_value=5000,
            value=2750,
            step=50,
            help="Comprimento padrão: 2750mm"
        )
        
        largura_chapa = st.number_input(
            "Largura da chapa (mm)",
            min_value=100,
            max_value=5000,
            value=1840,
            step=50,
            help="Largura padrão: 1840mm"
        )
        
        espessura = st.number_input(
            "Espessura do MDF (mm)",
            min_value=3,
            max_value=50,
            value=15,
            step=1
        )
        
        kerf = st.number_input(
            "Espessura do corte - Kerf (mm)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="Largura da lâmina da serra"
        )
        
        st.divider()
        st.caption("💡 Dica: Use dimensões reais das suas chapas")
    
    # ========================================================================
    # ÁREA PRINCIPAL - CADASTRO DE PEÇAS
    # ========================================================================
    
    st.header("📋 Cadastro de Peças")
    
    # Inicializar session state
    if 'pecas' not in st.session_state:
        st.session_state.pecas = []
    
    # Formulário de cadastro
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            nome = st.text_input("Nome da peça", placeholder="Ex: Lateral Esquerda")
        
        with col2:
            comprimento = st.number_input(
                "Comprimento (mm)",
                min_value=10,
                max_value=int(comprimento_chapa),
                value=800,
                step=10
            )
        
        with col3:
            largura = st.number_input(
                "Largura (mm)",
                min_value=10,
                max_value=int(largura_chapa),
                value=300,
                step=10
            )
        
        with col4:
            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                max_value=100,
                value=1
            )
        
        submitted = st.form_submit_button("➕ Adicionar Peça", use_container_width=True)
        
        if submitted:
            if not nome:
                st.error("❌ Digite o nome da peça!")
            else:
                peca = Peca(
                    nome=nome,
                    comprimento=comprimento,
                    largura=largura,
                    quantidade=quantidade
                )
                st.session_state.pecas.append(peca)
                st.success(f"✅ Peça '{nome}' adicionada com sucesso!")
                st.rerun()
    
    # ========================================================================
    # LISTA DE PEÇAS CADASTRADAS
    # ========================================================================
    
    if st.session_state.pecas:
        st.subheader("📦 Peças Cadastradas")
        
        # Criar DataFrame
        df_pecas = pd.DataFrame([
            {
                "Nome": p.nome,
                "Comprimento (mm)": int(p.comprimento),
                "Largura (mm)": int(p.largura),
                "Quantidade": p.quantidade,
                "Área Total (m²)": round(p.area() * p.quantidade / 1_000_000, 3)
            }
            for p in st.session_state.pecas
        ])
        
        st.dataframe(df_pecas, use_container_width=True, hide_index=True)
        
        # Botões de ação
        col1, col2, col3 = st.columns([2, 2, 6])
        
        with col1:
            if st.button("🗑️ Limpar Todas", use_container_width=True):
                st.session_state.pecas = []
                st.rerun()
        
        with col2:
            total_pecas = sum(p.quantidade for p in st.session_state.pecas)
            st.metric("Total de Peças", total_pecas)
        
        # ====================================================================
        # GERAR PLANO DE CORTE
        # ====================================================================
        
        st.divider()
        
        if st.button("🎯 GERAR PLANO DE CORTE", type="primary", use_container_width=True):
            with st.spinner("🔄 Otimizando cortes..."):
                # Executar otimização
                otimizador = OtimizadorCortes(
                    comprimento_chapa=comprimento_chapa,
                    largura_chapa=largura_chapa,
                    espessura=espessura,
                    kerf=kerf
                )
                
                chapas = otimizador.otimizar(st.session_state.pecas)
                
                # Armazenar resultado
                st.session_state.chapas = chapas
                st.success(f"✅ Otimização concluída! {len(chapas)} chapa(s) necessária(s).")
                st.rerun()
    
    else:
        st.info("👆 Cadastre as peças acima para gerar o plano de corte.")
    
    # ========================================================================
    # EXIBIR RESULTADOS
    # ========================================================================
    
    if 'chapas' in st.session_state and st.session_state.chapas:
        st.header("📊 Resultado da Otimização")
        
        # Estatísticas gerais
        total_chapas = len(st.session_state.chapas)
        aproveitamento_medio = sum(
            c.calcular_utilizacao() for c in st.session_state.chapas
        ) / total_chapas
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Chapas Necessárias", total_chapas)
        
        with col2:
            st.metric("Aproveitamento Médio", f"{aproveitamento_medio:.1f}%")
        
        with col3:
            st.metric("Desperdício Médio", f"{100 - aproveitamento_medio:.1f}%")
        
        st.divider()
        
        # Exibir cada chapa
        for chapa in st.session_state.chapas:
            with st.expander(
                f"📄 Chapa {chapa.numero} - Aproveitamento: {chapa.calcular_utilizacao():.1f}%",
                expanded=True
            ):
                # Gerar e exibir diagrama
                gerador = GeradorDiagrama(chapa)
                fig = gerador.gerar_diagrama(dpi=100)
                st.pyplot(fig)
                plt.close(fig)
                
                # Detalhes da chapa
                st.caption(f"🔹 Total de peças: {sum(len(f.pecas) for f in chapa.faixas)}")
                st.caption(f"🔹 Desperdício: {chapa.calcular_desperdicio():.1f}%")
        
        # ====================================================================
        # GERAR PDF
        # ====================================================================
        
        st.divider()
        
        if st.button("📄 GERAR PDF PARA IMPRESSÃO", use_container_width=True):
            with st.spinner("📝 Gerando PDF profissional..."):
                gerador_pdf = GeradorPDF(st.session_state.chapas)
                pdf_buffer = gerador_pdf.gerar_pdf()
                
                st.download_button(
                    label="⬇️ BAIXAR PDF",
                    data=pdf_buffer,
                    file_name=f"corte_certo_plano_{len(st.session_state.chapas)}_chapas.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ PDF gerado com sucesso!")
    
    # ========================================================================
    # RODAPÉ
    # ========================================================================
    
    st.divider()
    st.caption("🪚 Corte Certo v1.0 - Sistema Profissional de Otimização | "
               "Desenvolvido para Marcenarias")


# ============================================================================
# EXECUTAR APLICAÇÃO
# ============================================================================

if __name__ == "__main__":
    main()