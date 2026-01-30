"""
CORTE CERTO - Sistema Profissional de Otimização de Cortes de MDF
Versão 2.0 - Com Cadastros e Banco de Dados
"""

import streamlit as st
import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

# Adicionar diretório ao path para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

# Importar database
from database import db_manager, Cliente, TipoChapa, TipoFita, Projeto, PecaProjeto

# Importar módulos do sistema antigo
import importlib.util
spec = importlib.util.spec_from_file_location("corte_certo_engine", "corte_certo.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Corte Certo Pro - Sistema Profissional",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================================

# Criar dados de exemplo na primeira execução
db_manager.criar_dados_exemplo()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def init_session_state():
    """Inicializa variáveis de sessão"""
    if 'menu_atual' not in st.session_state:
        st.session_state.menu_atual = 'Otimizador'
    if 'projeto_atual' not in st.session_state:
        st.session_state.projeto_atual = None

# ============================================================================
# MENU LATERAL
# ============================================================================

def menu_lateral():
    """Menu lateral de navegação"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/FF8C42/FFFFFF?text=CORTE+CERTO+PRO", 
                 use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("### 📋 Menu Principal")
        
        menus = {
            '🎯 Otimizador de Cortes': 'Otimizador',
            '👤 Clientes': 'Clientes',
            '📦 Tipos de Chapa': 'Chapas',
            '📏 Tipos de Fita': 'Fitas',
            '📁 Projetos': 'Projetos'
        }
        
        for label, value in menus.items():
            if st.button(label, use_container_width=True, 
                        type='primary' if st.session_state.menu_atual == value else 'secondary'):
                st.session_state.menu_atual = value
                st.rerun()
        
        st.markdown("---")
        st.caption("🪚 Corte Certo Pro v2.0")
        st.caption("Sistema Profissional de Marcenaria")

# ============================================================================
# TELA: CADASTRO DE CLIENTES
# ============================================================================

def tela_clientes():
    """Tela de cadastro e gerenciamento de clientes"""
    st.title("👤 Cadastro de Clientes")
    
    tab1, tab2 = st.tabs(["📋 Lista de Clientes", "➕ Novo Cliente"])
    
    with tab1:
        session = db_manager.get_session()
        clientes = session.query(Cliente).order_by(Cliente.nome).all()
        
        if clientes:
            st.subheader(f"Total: {len(clientes)} cliente(s)")
            
            # Seleção e botões de ação ACIMA
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                cliente_id = st.selectbox(
                    "Selecione um cliente:",
                    options=[c.id for c in clientes],
                    format_func=lambda x: next(c.nome for c in clientes if c.id == x),
                    key="select_cliente"
                )
            
            with col2:
                if st.button("✏️ Editar", key="btn_edit_cli", use_container_width=True):
                    st.session_state.editing_cliente_id = cliente_id
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key="btn_del_cli", use_container_width=True):
                    st.session_state.deleting_cliente_id = cliente_id
                    st.rerun()
            
            st.markdown("---")
            
            # Grid EMBAIXO
            dados_grid = []
            for cliente in clientes:
                dados_grid.append({
                    'ID': cliente.id,
                    'Nome': cliente.nome,
                    'Telefone': cliente.telefone or '-',
                    'Email': cliente.email or '-',
                    'CPF/CNPJ': cliente.cpf_cnpj or '-',
                    'Endereço': cliente.endereco or '-',
                })
            
            df = pd.DataFrame(dados_grid)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum cliente cadastrado ainda.")
        
        session.close()
    
    with tab2:
        # Mostrar mensagem de sucesso se houver
        if 'msg_sucesso_cliente' in st.session_state:
            st.success(st.session_state.msg_sucesso_cliente)
            st.balloons()
            del st.session_state.msg_sucesso_cliente
        
        with st.form("form_cliente"):
            st.subheader("Dados do Cliente")
            
            nome = st.text_input("Nome *", placeholder="Ex: João Silva")
            
            col1, col2 = st.columns(2)
            with col1:
                telefone = st.text_input("Telefone", placeholder="(11) 98765-4321")
                cpf_cnpj = st.text_input("CPF/CNPJ", placeholder="000.000.000-00")
            
            with col2:
                email = st.text_input("Email", placeholder="cliente@email.com")
                endereco = st.text_input("Endereço", placeholder="Rua, nº - Cidade/UF")
            
            observacoes = st.text_area("Observações", placeholder="Informações adicionais...")
            
            submit = st.form_submit_button("💾 Salvar Cliente", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    session = db_manager.get_session()
                    novo_cliente = Cliente(
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        endereco=endereco,
                        cpf_cnpj=cpf_cnpj,
                        observacoes=observacoes
                    )
                    session.add(novo_cliente)
                    session.commit()
                    session.close()
                    st.session_state.msg_sucesso_cliente = f"✅ Cliente '{nome}' cadastrado com sucesso!"
                    st.rerun()
    
    # Modals
    if 'editing_cliente_id' in st.session_state:
        modal_editar_cliente()
    
    if 'deleting_cliente_id' in st.session_state:
        modal_excluir_cliente()


@st.dialog("✏️ Editar Cliente")
def modal_editar_cliente():
    """Modal para editar cliente"""
    session = db_manager.get_session()
    cliente = session.query(Cliente).get(st.session_state.editing_cliente_id)
    
    if cliente:
        with st.form("form_edit_cliente"):
            nome = st.text_input("Nome *", value=cliente.nome)
            
            col1, col2 = st.columns(2)
            with col1:
                telefone = st.text_input("Telefone", value=cliente.telefone or "")
                cpf_cnpj = st.text_input("CPF/CNPJ", value=cliente.cpf_cnpj or "")
            
            with col2:
                email = st.text_input("Email", value=cliente.email or "")
                endereco = st.text_input("Endereço", value=cliente.endereco or "")
            
            observacoes = st.text_area("Observações", value=cliente.observacoes or "")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")
            
            with col_btn2:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    cliente.nome = nome
                    cliente.telefone = telefone
                    cliente.email = email
                    cliente.endereco = endereco
                    cliente.cpf_cnpj = cpf_cnpj
                    cliente.observacoes = observacoes
                    session.commit()
                    session.close()
                    del st.session_state.editing_cliente_id
                    st.success("✅ Cliente atualizado com sucesso!")
                    st.rerun()
            
            if cancel:
                session.close()
                del st.session_state.editing_cliente_id
                st.rerun()
    else:
        session.close()


@st.dialog("🗑️ Excluir Cliente")
def modal_excluir_cliente():
    """Modal para confirmar exclusão de cliente"""
    session = db_manager.get_session()
    cliente = session.query(Cliente).get(st.session_state.deleting_cliente_id)
    
    if cliente:
        st.warning(f"⚠️ Tem certeza que deseja excluir o cliente **{cliente.nome}**?")
        st.write("Esta ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sim, excluir", key="confirm_del", use_container_width=True, type="primary"):
                session.delete(cliente)
                session.commit()
                session.close()
                del st.session_state.deleting_cliente_id
                st.success("✅ Cliente excluído com sucesso!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar", key="cancel_del", use_container_width=True):
                session.close()
                del st.session_state.deleting_cliente_id
                st.rerun()
    else:
        session.close()

# ============================================================================
# TELA: CADASTRO DE CHAPAS
# ============================================================================

def tela_chapas():
    """Tela de cadastro de tipos de chapa"""
    st.title("📦 Cadastro de Tipos de Chapa MDF")
    
    tab1, tab2 = st.tabs(["📋 Chapas Cadastradas", "➕ Nova Chapa"])
    
    with tab1:
        session = db_manager.get_session()
        chapas = session.query(TipoChapa).filter_by(ativo=True).order_by(TipoChapa.nome).all()
        
        if chapas:
            st.subheader(f"Total: {len(chapas)} tipo(s) de chapa")
            
            # Seleção e botões ACIMA
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                chapa_id = st.selectbox(
                    "Selecione uma chapa:",
                    options=[c.id for c in chapas],
                    format_func=lambda x: next(c.nome for c in chapas if c.id == x),
                    key="select_chapa"
                )
            
            with col2:
                if st.button("✏️ Editar", key="btn_edit_chapa", use_container_width=True):
                    st.session_state.editing_chapa_id = chapa_id
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key="btn_del_chapa", use_container_width=True):
                    st.session_state.deleting_chapa_id = chapa_id
                    st.rerun()
            
            st.markdown("---")
            
            # Grid EMBAIXO
            dados_grid = []
            for chapa in chapas:
                dados_grid.append({
                    'ID': chapa.id,
                    'Nome': chapa.nome,
                    'Dimensões (mm)': f"{int(chapa.comprimento)}×{int(chapa.largura)}×{int(chapa.espessura)}",
                    'Cor': chapa.cor or '-',
                    'Acabamento': chapa.acabamento or '-',
                    'Preço (R$)': f"R$ {chapa.preco:.2f}",
                    'Fornecedor': chapa.fornecedor or '-',
                })
            
            df = pd.DataFrame(dados_grid)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma chapa cadastrada.")
        
        session.close()
    
    with tab2:
        # Mostrar mensagem de sucesso se houver
        if 'msg_sucesso_chapa' in st.session_state:
            st.success(st.session_state.msg_sucesso_chapa)
            st.balloons()
            del st.session_state.msg_sucesso_chapa
        
        with st.form("form_chapa"):
            st.subheader("Dados da Chapa")
            
            nome = st.text_input("Nome/Descrição *", placeholder="Ex: MDF Branco 15mm")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                comprimento = st.number_input("Comprimento (mm) *", min_value=100, max_value=5000, value=2750, step=50)
            with col2:
                largura = st.number_input("Largura (mm) *", min_value=100, max_value=5000, value=1840, step=50)
            with col3:
                espessura = st.number_input("Espessura (mm) *", min_value=3, max_value=50, value=15, step=1)
            
            col4, col5 = st.columns(2)
            with col4:
                cor = st.text_input("Cor", placeholder="Ex: Branco, Preto, Natural")
                fornecedor = st.text_input("Fornecedor", placeholder="Ex: Duratex, Berneck")
            
            with col5:
                acabamento = st.text_input("Acabamento", placeholder="Ex: BP, Cru, Laca")
                preco = st.number_input("Preço (R$) *", min_value=0.0, max_value=10000.0, value=180.0, step=10.0)
            
            observacoes = st.text_area("Observações")
            
            submit = st.form_submit_button("💾 Salvar Chapa", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    session = db_manager.get_session()
                    nova_chapa = TipoChapa(
                        nome=nome,
                        comprimento=comprimento,
                        largura=largura,
                        espessura=espessura,
                        preco=preco,
                        cor=cor,
                        acabamento=acabamento,
                        fornecedor=fornecedor,
                        observacoes=observacoes
                    )
                    session.add(nova_chapa)
                    session.commit()
                    session.close()
                    st.session_state.msg_sucesso_chapa = f"✅ Chapa '{nome}' cadastrada com sucesso!"
                    st.rerun()
                    st.rerun()
    
    # Modals
    if 'editing_chapa_id' in st.session_state:
        modal_editar_chapa()
    
    if 'deleting_chapa_id' in st.session_state:
        modal_excluir_chapa()


@st.dialog("✏️ Editar Chapa")
def modal_editar_chapa():
    """Modal para editar chapa"""
    session = db_manager.get_session()
    chapa = session.query(TipoChapa).get(st.session_state.editing_chapa_id)
    
    if chapa:
        with st.form("form_edit_chapa"):
            nome = st.text_input("Nome/Descrição *", value=chapa.nome)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                comprimento = st.number_input("Comprimento (mm) *", min_value=100, max_value=5000, 
                                            value=int(chapa.comprimento), step=50)
            with col2:
                largura = st.number_input("Largura (mm) *", min_value=100, max_value=5000, 
                                        value=int(chapa.largura), step=50)
            with col3:
                espessura = st.number_input("Espessura (mm) *", min_value=3, max_value=50, 
                                          value=int(chapa.espessura), step=1)
            
            col4, col5 = st.columns(2)
            with col4:
                cor = st.text_input("Cor", value=chapa.cor or "")
                fornecedor = st.text_input("Fornecedor", value=chapa.fornecedor or "")
            
            with col5:
                acabamento = st.text_input("Acabamento", value=chapa.acabamento or "")
                preco = st.number_input("Preço (R$) *", min_value=0.0, max_value=10000.0, 
                                       value=float(chapa.preco), step=10.0)
            
            observacoes = st.text_area("Observações", value=chapa.observacoes or "")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")
            
            with col_btn2:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    chapa.nome = nome
                    chapa.comprimento = comprimento
                    chapa.largura = largura
                    chapa.espessura = espessura
                    chapa.preco = preco
                    chapa.cor = cor
                    chapa.acabamento = acabamento
                    chapa.fornecedor = fornecedor
                    chapa.observacoes = observacoes
                    session.commit()
                    session.close()
                    del st.session_state.editing_chapa_id
                    st.success("✅ Chapa atualizada com sucesso!")
                    st.rerun()
            
            if cancel:
                session.close()
                del st.session_state.editing_chapa_id
                st.rerun()
    else:
        session.close()


@st.dialog("🗑️ Excluir Chapa")
def modal_excluir_chapa():
    """Modal para confirmar exclusão de chapa"""
    session = db_manager.get_session()
    chapa = session.query(TipoChapa).get(st.session_state.deleting_chapa_id)
    
    if chapa:
        st.warning(f"⚠️ Tem certeza que deseja excluir a chapa **{chapa.nome}**?")
        st.write("Esta ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sim, excluir", key="confirm_del_chapa", use_container_width=True, type="primary"):
                chapa.ativo = False
                session.commit()
                session.close()
                del st.session_state.deleting_chapa_id
                st.success("✅ Chapa excluída com sucesso!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar", key="cancel_del_chapa", use_container_width=True):
                session.close()
                del st.session_state.deleting_chapa_id
                st.rerun()
    else:
        session.close()
    """Tela de cadastro de tipos de chapa"""
    st.title("📦 Cadastro de Tipos de Chapa MDF")
    
    tab1, tab2 = st.tabs(["📋 Chapas Cadastradas", "➕ Nova Chapa"])
    
    with tab1:
        session = db_manager.get_session()
        chapas = session.query(TipoChapa).filter_by(ativo=True).order_by(TipoChapa.nome).all()
        
        if chapas:
            st.subheader(f"Total: {len(chapas)} tipo(s) de chapa")
            
            for chapa in chapas:
                with st.expander(f"📦 {chapa.descricao_completa()}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Dimensões:** {int(chapa.comprimento)} × {int(chapa.largura)} × {int(chapa.espessura)} mm")
                        st.markdown(f"**Cor:** {chapa.cor or '-'}")
                        st.markdown(f"**Acabamento:** {chapa.acabamento or '-'}")
                        st.markdown(f"**Fornecedor:** {chapa.fornecedor or '-'}")
                        st.markdown(f"**Preço:** R$ {chapa.preco:.2f}")
                    
                    with col2:
                        # Botão Editar
                        if st.button("✏️ Editar", key=f"edit_chapa_{chapa.id}", use_container_width=True):
                            st.session_state.editing_chapa = chapa.id
                            st.rerun()
                        
                        # Botão Excluir
                        if st.button("🗑️ Excluir", key=f"del_chapa_{chapa.id}", use_container_width=True, type="secondary"):
                            st.session_state.deleting_chapa = chapa.id
                            st.rerun()
            
            # Modal de Edição
            if 'editing_chapa' in st.session_state and st.session_state.editing_chapa:
                chapa_edit = session.query(TipoChapa).get(st.session_state.editing_chapa)
                
                if chapa_edit:
                    with st.container():
                        st.markdown("---")
                        st.subheader(f"✏️ Editando: {chapa_edit.nome}")
                        
                        with st.form(f"form_edit_chapa_{chapa_edit.id}"):
                            nome = st.text_input("Nome/Descrição *", value=chapa_edit.nome)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                comprimento = st.number_input("Comprimento (mm) *", min_value=100, max_value=5000, 
                                                            value=int(chapa_edit.comprimento), step=50)
                            with col2:
                                largura = st.number_input("Largura (mm) *", min_value=100, max_value=5000, 
                                                        value=int(chapa_edit.largura), step=50)
                            with col3:
                                espessura = st.number_input("Espessura (mm) *", min_value=3, max_value=50, 
                                                          value=int(chapa_edit.espessura), step=1)
                            
                            col4, col5 = st.columns(2)
                            with col4:
                                cor = st.text_input("Cor", value=chapa_edit.cor or "")
                                fornecedor = st.text_input("Fornecedor", value=chapa_edit.fornecedor or "")
                            
                            with col5:
                                acabamento = st.text_input("Acabamento", value=chapa_edit.acabamento or "")
                                preco = st.number_input("Preço (R$) *", min_value=0.0, max_value=10000.0, 
                                                       value=float(chapa_edit.preco), step=10.0)
                            
                            observacoes = st.text_area("Observações", value=chapa_edit.observacoes or "")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                submit = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")
                            
                            with col_btn2:
                                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            
                            if submit:
                                if not nome:
                                    st.error("Nome é obrigatório!")
                                else:
                                    chapa_edit.nome = nome
                                    chapa_edit.comprimento = comprimento
                                    chapa_edit.largura = largura
                                    chapa_edit.espessura = espessura
                                    chapa_edit.preco = preco
                                    chapa_edit.cor = cor
                                    chapa_edit.acabamento = acabamento
                                    chapa_edit.fornecedor = fornecedor
                                    chapa_edit.observacoes = observacoes
                                    session.commit()
                                    del st.session_state.editing_chapa
                                    st.success("✅ Chapa atualizada com sucesso!")
                                    st.rerun()
                            
                            if cancel:
                                del st.session_state.editing_chapa
                                st.rerun()
            
            # Modal de Confirmação de Exclusão
            if 'deleting_chapa' in st.session_state and st.session_state.deleting_chapa:
                chapa_del = session.query(TipoChapa).get(st.session_state.deleting_chapa)
                
                if chapa_del:
                    st.markdown("---")
                    st.warning(f"⚠️ Tem certeza que deseja excluir a chapa **{chapa_del.nome}**?")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✅ Sim, excluir", key="confirm_del_chapa", use_container_width=True, type="primary"):
                            chapa_del.ativo = False
                            session.commit()
                            del st.session_state.deleting_chapa
                            st.success("Chapa removida!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("❌ Cancelar", key="cancel_del_chapa", use_container_width=True):
                            del st.session_state.deleting_chapa
                            st.rerun()
        else:
            st.info("Nenhuma chapa cadastrada.")
        
        session.close()
    
    with tab2:
        with st.form("form_chapa"):
            st.subheader("Dados da Chapa")
            
            nome = st.text_input("Nome/Descrição *", placeholder="Ex: MDF Branco 15mm")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                comprimento = st.number_input("Comprimento (mm) *", min_value=100, max_value=5000, value=2750, step=50)
            with col2:
                largura = st.number_input("Largura (mm) *", min_value=100, max_value=5000, value=1840, step=50)
            with col3:
                espessura = st.number_input("Espessura (mm) *", min_value=3, max_value=50, value=15, step=1)
            
            col4, col5 = st.columns(2)
            with col4:
                cor = st.text_input("Cor", placeholder="Ex: Branco, Preto, Natural")
                fornecedor = st.text_input("Fornecedor", placeholder="Ex: Duratex, Berneck")
            
            with col5:
                acabamento = st.text_input("Acabamento", placeholder="Ex: BP, Cru, Laca")
                preco = st.number_input("Preço (R$) *", min_value=0.0, max_value=10000.0, value=180.0, step=10.0)
            
            observacoes = st.text_area("Observações")
            
            submit = st.form_submit_button("💾 Salvar Chapa", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("Nome é obrigatório!")
                else:
                    session = db_manager.get_session()
                    nova_chapa = TipoChapa(
                        nome=nome,
                        comprimento=comprimento,
                        largura=largura,
                        espessura=espessura,
                        preco=preco,
                        cor=cor,
                        acabamento=acabamento,
                        fornecedor=fornecedor,
                        observacoes=observacoes
                    )
                    session.add(nova_chapa)
                    session.commit()
                    session.close()
                    st.success(f"✅ Chapa '{nome}' cadastrada com sucesso!")
                    st.rerun()

# ============================================================================
# TELA: CADASTRO DE FITAS
# ============================================================================

def tela_fitas():
    """Tela de cadastro de tipos de fita de borda"""
    st.title("📏 Cadastro de Tipos de Fita de Borda")
    
    tab1, tab2 = st.tabs(["📋 Fitas Cadastradas", "➕ Nova Fita"])
    
    with tab1:
        session = db_manager.get_session()
        fitas = session.query(TipoFita).filter_by(ativo=True).order_by(TipoFita.nome).all()
        
        if fitas:
            st.subheader(f"Total: {len(fitas)} tipo(s) de fita")
            
            # Seleção e botões ACIMA
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                fita_id = st.selectbox(
                    "Selecione uma fita:",
                    options=[f.id for f in fitas],
                    format_func=lambda x: next(f.nome for f in fitas if f.id == x),
                    key="select_fita_list"
                )
            
            with col2:
                if st.button("✏️ Editar", key="btn_edit_fita", use_container_width=True):
                    st.session_state.editing_fita_id = fita_id
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key="btn_del_fita", use_container_width=True):
                    st.session_state.deleting_fita_id = fita_id
                    st.rerun()
            
            st.markdown("---")
            
            # Grid EMBAIXO
            dados_grid = []
            for fita in fitas:
                dados_grid.append({
                    'ID': fita.id,
                    'Nome': fita.nome,
                    'Largura (mm)': int(fita.largura),
                    'Rolo (m)': int(fita.comprimento_rolo),
                    'Preço/Rolo': f"R$ {fita.preco_rolo:.2f}",
                    'Cor': fita.cor or '-',
                    'Material': fita.material or '-',
                    'Fornecedor': fita.fornecedor or '-',
                })
            
            df = pd.DataFrame(dados_grid)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma fita cadastrada.")
        
        session.close()
    
    with tab2:
        # Mostrar mensagem de sucesso se houver
        if 'msg_sucesso_fita' in st.session_state:
            st.success(st.session_state.msg_sucesso_fita)
            st.balloons()
            del st.session_state.msg_sucesso_fita
        
        with st.form("form_fita"):
            st.subheader("Dados da Fita")
            
            nome = st.text_input("Nome/Descrição *", placeholder="Ex: Fita Branca 22mm")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                largura = st.number_input("Largura (mm) *", min_value=10, max_value=100, value=22, step=1)
            with col2:
                comprimento_rolo = st.number_input("Comprimento/rolo (m) *", min_value=10, max_value=200, value=50, step=10)
            with col3:
                preco_rolo = st.number_input("Preço/rolo (R$) *", min_value=0.0, max_value=1000.0, value=25.0, step=5.0)
            
            col4, col5 = st.columns(2)
            with col4:
                cor = st.text_input("Cor", placeholder="Ex: Branco, Preto, Amadeirado")
                fornecedor = st.text_input("Fornecedor")
            
            with col5:
                material = st.text_input("Material", placeholder="Ex: PVC, ABS, Melamínico")
            
            observacoes = st.text_area("Observações")
            
            submit = st.form_submit_button("💾 Salvar Fita", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    session = db_manager.get_session()
                    nova_fita = TipoFita(
                        nome=nome,
                        largura=largura,
                        comprimento_rolo=comprimento_rolo,
                        preco_rolo=preco_rolo,
                        cor=cor,
                        material=material,
                        fornecedor=fornecedor,
                        observacoes=observacoes
                    )
                    session.add(nova_fita)
                    session.commit()
                    session.close()
                    st.session_state.msg_sucesso_fita = f"✅ Fita '{nome}' cadastrada com sucesso!"
                    st.rerun()
    
    # Modals
    if 'editing_fita_id' in st.session_state:
        modal_editar_fita()
    
    if 'deleting_fita_id' in st.session_state:
        modal_excluir_fita()


@st.dialog("✏️ Editar Fita")
def modal_editar_fita():
    """Modal para editar fita"""
    session = db_manager.get_session()
    fita = session.query(TipoFita).get(st.session_state.editing_fita_id)
    
    if fita:
        with st.form("form_edit_fita"):
            nome = st.text_input("Nome/Descrição *", value=fita.nome)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                largura = st.number_input("Largura (mm) *", min_value=10, max_value=100, 
                                        value=int(fita.largura), step=1)
            with col2:
                comprimento_rolo = st.number_input("Comprimento/rolo (m) *", min_value=10, max_value=200, 
                                                  value=int(fita.comprimento_rolo), step=10)
            with col3:
                preco_rolo = st.number_input("Preço/rolo (R$) *", min_value=0.0, max_value=1000.0, 
                                            value=float(fita.preco_rolo), step=5.0)
            
            col4, col5 = st.columns(2)
            with col4:
                cor = st.text_input("Cor", value=fita.cor or "")
                fornecedor = st.text_input("Fornecedor", value=fita.fornecedor or "")
            
            with col5:
                material = st.text_input("Material", value=fita.material or "")
            
            observacoes = st.text_area("Observações", value=fita.observacoes or "")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")
            
            with col_btn2:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submit:
                if not nome:
                    st.error("❌ Nome é obrigatório!")
                else:
                    fita.nome = nome
                    fita.largura = largura
                    fita.comprimento_rolo = comprimento_rolo
                    fita.preco_rolo = preco_rolo
                    fita.cor = cor
                    fita.material = material
                    fita.fornecedor = fornecedor
                    fita.observacoes = observacoes
                    session.commit()
                    session.close()
                    del st.session_state.editing_fita_id
                    st.success("✅ Fita atualizada com sucesso!")
                    st.rerun()
            
            if cancel:
                session.close()
                del st.session_state.editing_fita_id
                st.rerun()
    else:
        session.close()


@st.dialog("🗑️ Excluir Fita")
def modal_excluir_fita():
    """Modal para confirmar exclusão de fita"""
    session = db_manager.get_session()
    fita = session.query(TipoFita).get(st.session_state.deleting_fita_id)
    
    if fita:
        st.warning(f"⚠️ Tem certeza que deseja excluir a fita **{fita.nome}**?")
        st.write("Esta ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sim, excluir", key="confirm_del_fita", use_container_width=True, type="primary"):
                fita.ativo = False
                session.commit()
                session.close()
                del st.session_state.deleting_fita_id
                st.success("✅ Fita excluída com sucesso!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar", key="cancel_del_fita", use_container_width=True):
                session.close()
                del st.session_state.deleting_fita_id
                st.rerun()
    else:
        session.close()

# ============================================================================
# TELA: OTIMIZADOR (COMPLETO E INTEGRADO)
# ============================================================================

def tela_otimizador():
    """Tela principal de otimização integrada com cadastros"""
    st.title("🎯 Otimizador de Cortes Profissional")
    
    # Verificar se há chapas e fitas cadastradas
    session = db_manager.get_session()
    chapas_disponiveis = session.query(TipoChapa).filter_by(ativo=True).all()
    fitas_disponiveis = session.query(TipoFita).filter_by(ativo=True).all()
    clientes_disponiveis = session.query(Cliente).all()
    session.close()
    
    if not chapas_disponiveis:
        st.error("⚠️ Nenhum tipo de chapa cadastrado! Cadastre chapas antes de usar o otimizador.")
        if st.button("📦 Ir para Cadastro de Chapas"):
            st.session_state.menu_atual = 'Chapas'
            st.rerun()
        return
    
    # ====================================================================
    # SIDEBAR - CONFIGURAÇÕES DO PROJETO
    # ====================================================================
    
    with st.sidebar:
        st.header("⚙️ Configurações do Projeto")
        
        # Seleção de cliente
        if clientes_disponiveis:
            opcoes_clientes = {f"{c.nome}": c.id for c in clientes_disponiveis}
            opcoes_clientes["[Sem Cliente]"] = None
            
            cliente_selecionado = st.selectbox(
                "Cliente",
                options=list(opcoes_clientes.keys()),
                index=0
            )
            cliente_id = opcoes_clientes[cliente_selecionado]
        else:
            st.info("Nenhum cliente cadastrado")
            cliente_id = None
        
        nome_projeto = st.text_input("Nome do Projeto", placeholder="Ex: Armário Cozinha")
        
        st.divider()
        
        st.header("🔧 Parâmetros Gerais")
        
        kerf = st.number_input(
            "Espessura do corte - Kerf (mm)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="Largura da lâmina da serra"
        )
        
        sentido_veio = st.selectbox(
            "Sentido do veio da chapa",
            options=["Horizontal (no comprimento)", "Vertical (na largura)", "Sem veio (MDF)"],
            index=0,
            help="Define a direção das fibras/veio na chapa"
        )
        
        st.divider()
        st.caption("💡 Configure o projeto e adicione peças")
    
    # ====================================================================
    # ÁREA PRINCIPAL - CADASTRO DE PEÇAS
    # ====================================================================
    
    # Inicializar session state para peças
    if 'pecas_otimizador' not in st.session_state:
        st.session_state.pecas_otimizador = []
    
    # Inicializar valores padrão para manter seleções
    if 'ultima_chapa_id' not in st.session_state:
        st.session_state.ultima_chapa_id = chapas_disponiveis[0].id if chapas_disponiveis else None
    if 'ultima_fita_id' not in st.session_state:
        st.session_state.ultima_fita_id = None
    
    st.header("📋 Cadastro de Peças do Projeto")
    
    # Formulário de cadastro
    with st.form("form_peca_otimizador", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            nome_peca = st.text_input("Nome da peça", placeholder="Ex: Lateral Esquerda")
        
        with col2:
            comprimento = st.number_input("Comprimento (mm)", min_value=10, value=800, step=10)
        
        with col3:
            largura = st.number_input("Largura (mm)", min_value=10, value=300, step=10)
        
        with col4:
            quantidade = st.number_input("Qtd", min_value=1, value=1, step=1)
        
        # Seleção de tipo de chapa - Manter última seleção
        st.markdown("##### 📦 Tipo de Chapa")
        opcoes_chapas = {c.descricao_completa(): c.id for c in chapas_disponiveis}
        
        # Encontrar índice da última chapa selecionada
        lista_chapas = list(opcoes_chapas.keys())
        indice_chapa = 0
        for i, (desc, chapa_id) in enumerate(opcoes_chapas.items()):
            if chapa_id == st.session_state.ultima_chapa_id:
                indice_chapa = i
                break
        
        chapa_selecionada = st.selectbox(
            "Selecione o tipo de chapa para esta peça",
            options=lista_chapas,
            index=indice_chapa,
            key="select_chapa"
        )
        tipo_chapa_id = opcoes_chapas[chapa_selecionada]
        
        # Seleção de tipo de fita (sempre habilitada) - Manter última seleção
        st.markdown("##### 📏 Fita de Borda (Opcional)")
        
        tipo_fita_id = None
        
        if fitas_disponiveis:
            # Adicionar opção "Sem fita"
            opcoes_fitas = {"[Sem Fita de Borda]": None}
            for f in fitas_disponiveis:
                opcoes_fitas[f.descricao_completa()] = f.id
            
            # Encontrar índice da última fita selecionada
            lista_fitas = list(opcoes_fitas.keys())
            indice_fita = 0
            for i, (desc, fita_id) in enumerate(opcoes_fitas.items()):
                if fita_id == st.session_state.ultima_fita_id:
                    indice_fita = i
                    break
            
            fita_selecionada = st.selectbox(
                "Tipo de fita (deixe em 'Sem Fita' se não usar)",
                options=lista_fitas,
                index=indice_fita,
                key="select_fita"
            )
            tipo_fita_id = opcoes_fitas[fita_selecionada]
            
            # SEMPRE mostrar bordas - sempre habilitadas
            st.caption("Selecione as bordas que receberão fita:")
            
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            
            with col_b1:
                fita_comp1 = st.checkbox("🔼 Superior", key="fita_comp1_otim")
            with col_b2:
                fita_comp2 = st.checkbox("🔽 Inferior", key="fita_comp2_otim")
            with col_b3:
                fita_larg1 = st.checkbox("◀️ Esquerda", key="fita_larg1_otim")
            with col_b4:
                fita_larg2 = st.checkbox("▶️ Direita", key="fita_larg2_otim")
            
            # Se não tem fita selecionada, zerar bordas ao salvar
            if tipo_fita_id is None:
                fita_comp1 = fita_comp2 = fita_larg1 = fita_larg2 = False
        else:
            st.info("💡 Nenhuma fita cadastrada. Vá em 'Tipos de Fita' para cadastrar.")
            tipo_fita_id = None
            fita_comp1 = fita_comp2 = fita_larg1 = fita_larg2 = False
        
        # Veio
        st.markdown("##### 🌾 Orientação do Veio")
        respeitar_veio = st.checkbox(
            "Respeitar sentido do veio (não rotacionar esta peça)",
            key="veio_otim"
        )
        
        # Botão submit
        submit_peca = st.form_submit_button("➕ Adicionar Peça ao Projeto", use_container_width=True)
        
        if submit_peca:
            if not nome_peca:
                st.error("❌ Digite o nome da peça!")
            else:
                # Criar objeto de peça com IDs dos cadastros
                peca_data = {
                    'nome': nome_peca,
                    'comprimento': comprimento,
                    'largura': largura,
                    'quantidade': quantidade,
                    'tipo_chapa_id': tipo_chapa_id,
                    'tipo_fita_id': tipo_fita_id,
                    'fita_borda_comp1': fita_comp1,
                    'fita_borda_comp2': fita_comp2,
                    'fita_borda_larg1': fita_larg1,
                    'fita_borda_larg2': fita_larg2,
                    'respeitar_veio': respeitar_veio
                }
                
                st.session_state.pecas_otimizador.append(peca_data)
                
                # Salvar última seleção de chapa e fita
                st.session_state.ultima_chapa_id = tipo_chapa_id
                st.session_state.ultima_fita_id = tipo_fita_id
                
                st.success(f"✅ Peça '{nome_peca}' adicionada!")
                st.rerun()
    
    # ====================================================================
    # EXIBIR PEÇAS CADASTRADAS
    # ====================================================================
    
    if st.session_state.pecas_otimizador:
        st.subheader("📦 Peças do Projeto")
        
        # Agrupar por tipo de chapa
        session = db_manager.get_session()
        pecas_por_chapa = {}
        
        for idx, peca in enumerate(st.session_state.pecas_otimizador):
            chapa_id = peca['tipo_chapa_id']
            if chapa_id not in pecas_por_chapa:
                tipo_chapa = session.query(TipoChapa).get(chapa_id)
                pecas_por_chapa[chapa_id] = {
                    'tipo': tipo_chapa,
                    'pecas': []
                }
            pecas_por_chapa[chapa_id]['pecas'].append((idx, peca))  # Guardar índice original
        
        # Exibir por grupo
        for chapa_id, grupo in pecas_por_chapa.items():
            tipo_chapa = grupo['tipo']
            pecas_com_idx = grupo['pecas']
            
            with st.expander(f"📦 {tipo_chapa.nome} - {len(pecas_com_idx)} peça(s)", expanded=True):
                # Criar DataFrame
                dados_tabela = []
                indices_pecas = []
                
                for idx, p in pecas_com_idx:
                    indices_pecas.append(idx)
                    
                    # Buscar tipo de fita se houver
                    tipo_fita_nome = "-"
                    if p['tipo_fita_id']:
                        tipo_fita = session.query(TipoFita).get(p['tipo_fita_id'])
                        tipo_fita_nome = tipo_fita.nome if tipo_fita else "-"
                    
                    # Formatar fitas
                    bordas = []
                    if p['fita_borda_comp1']:
                        bordas.append("▲")
                    if p['fita_borda_comp2']:
                        bordas.append("▼")
                    if p['fita_borda_larg1']:
                        bordas.append("◀")
                    if p['fita_borda_larg2']:
                        bordas.append("▶")
                    fitas_str = " ".join(bordas) if bordas else "-"
                    
                    dados_tabela.append({
                        'Nome': p['nome'],
                        'Comp. (mm)': int(p['comprimento']),
                        'Larg. (mm)': int(p['largura']),
                        'Qtd': p['quantidade'],
                        'Tipo Chapa': tipo_chapa.nome,
                        'Tipo Fita': tipo_fita_nome,
                        'Bordas': fitas_str,
                        'Veio': '🌾' if p['respeitar_veio'] else '-'
                    })
                
                df = pd.DataFrame(dados_tabela)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Seletor e botões para excluir
                st.markdown("---")
                col_sel, col_btn1, col_btn2 = st.columns([4, 1, 1])
                
                with col_sel:
                    # Criar opções de seleção
                    opcoes_pecas = {}
                    for i, (idx, p) in enumerate(pecas_com_idx):
                        label = f"{p['nome']} ({int(p['comprimento'])}×{int(p['largura'])}mm) - Qtd: {p['quantidade']}"
                        opcoes_pecas[label] = idx
                    
                    if opcoes_pecas:
                        peca_selecionada = st.selectbox(
                            "Selecione uma peça:",
                            options=list(opcoes_pecas.keys()),
                            key=f"select_peca_{chapa_id}"
                        )
                        idx_selecionado = opcoes_pecas[peca_selecionada]
                
                with col_btn1:
                    if st.button("🗑️ Excluir", key=f"excluir_peca_{chapa_id}", use_container_width=True):
                        # Remover peça selecionada
                        st.session_state.pecas_otimizador.pop(idx_selecionado)
                        st.success("✅ Peça excluída!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ Grupo", key=f"limpar_grupo_{chapa_id}", use_container_width=True):
                        # Remover todas do grupo
                        st.session_state.pecas_otimizador = [
                            p for i, p in enumerate(st.session_state.pecas_otimizador) 
                            if i not in indices_pecas
                        ]
                        st.success("✅ Grupo excluído!")
                        st.rerun()
        
        session.close()
        
        # Botões de ação
        st.divider()
        col_a1, col_a2 = st.columns([1, 1])
        
        with col_a1:
            if st.button("🗑️ Limpar Todas as Peças", use_container_width=True):
                st.session_state.pecas_otimizador = []
                st.rerun()
        
        with col_a2:
            total_pecas = sum(p['quantidade'] for p in st.session_state.pecas_otimizador)
            st.metric("Total de Peças", total_pecas)
        
        # ====================================================================
        # GERAR OTIMIZAÇÃO
        # ====================================================================
        
        st.divider()
        
        if st.button("🎯 GERAR PLANO DE CORTE OTIMIZADO", type="primary", use_container_width=True):
            with st.spinner("🔄 Otimizando cortes por tipo de material..."):
                # Processar otimização por tipo de chapa
                resultados_por_tipo = processar_otimizacao_por_tipo(
                    st.session_state.pecas_otimizador,
                    kerf,
                    sentido_veio
                )
                
                # Armazenar resultados
                st.session_state.resultados_otimizacao = resultados_por_tipo
                st.session_state.config_projeto = {
                    'nome': nome_projeto,
                    'cliente_id': cliente_id,
                    'kerf': kerf,
                    'sentido_veio': sentido_veio
                }
                
                st.success(f"✅ Otimização concluída! {len(resultados_por_tipo)} tipo(s) de material.")
                st.rerun()
    
    else:
        st.info("👆 Adicione peças ao projeto usando o formulário acima.")
    
    # ====================================================================
    # EXIBIR RESULTADOS DA OTIMIZAÇÃO
    # ====================================================================
    
    if 'resultados_otimizacao' in st.session_state and st.session_state.resultados_otimizacao:
        exibir_resultados_otimizacao()


def processar_otimizacao_por_tipo(pecas_data, kerf, sentido_veio):
    """Processa otimização separada por tipo de chapa"""
    session = db_manager.get_session()
    
    # Agrupar peças por tipo de chapa
    pecas_por_tipo = {}
    
    for peca_data in pecas_data:
        tipo_chapa_id = peca_data['tipo_chapa_id']
        
        if tipo_chapa_id not in pecas_por_tipo:
            pecas_por_tipo[tipo_chapa_id] = []
        
        # Converter para objeto Peca do engine
        for _ in range(peca_data['quantidade']):
            peca_obj = engine.Peca(
                nome=peca_data['nome'],
                comprimento=peca_data['comprimento'],
                largura=peca_data['largura'],
                quantidade=1,  # Já expandido
                fita_borda_comp1=peca_data['fita_borda_comp1'],
                fita_borda_comp2=peca_data['fita_borda_comp2'],
                fita_borda_larg1=peca_data['fita_borda_larg1'],
                fita_borda_larg2=peca_data['fita_borda_larg2'],
                respeitar_veio=peca_data['respeitar_veio']
            )
            pecas_por_tipo[tipo_chapa_id].append((peca_obj, peca_data['tipo_fita_id']))
    
    # Otimizar cada tipo separadamente
    resultados = {}
    
    for tipo_chapa_id, pecas_com_fita in pecas_por_tipo.items():
        tipo_chapa = session.query(TipoChapa).get(tipo_chapa_id)
        
        # Extrair apenas objetos Peca
        pecas_lista = [p[0] for p in pecas_com_fita]
        
        # Criar otimizador
        otimizador = engine.OtimizadorCortes(
            comprimento_chapa=tipo_chapa.comprimento,
            largura_chapa=tipo_chapa.largura,
            espessura=tipo_chapa.espessura,
            kerf=kerf,
            sentido_veio=sentido_veio
        )
        
        # Otimizar
        chapas = otimizador.otimizar(pecas_lista)
        
        # Calcular custos de fita por tipo
        custos_fita_por_tipo = {}
        total_fita_por_tipo = {}
        
        for peca_obj, tipo_fita_id in pecas_com_fita:
            if tipo_fita_id:
                fita_mm = peca_obj.comprimento_fita()
                if tipo_fita_id not in total_fita_por_tipo:
                    total_fita_por_tipo[tipo_fita_id] = 0
                total_fita_por_tipo[tipo_fita_id] += fita_mm
        
        # Calcular custos de fita
        for tipo_fita_id, total_mm in total_fita_por_tipo.items():
            tipo_fita = session.query(TipoFita).get(tipo_fita_id)
            total_m = total_mm / 1000
            rolos = -(-total_m // tipo_fita.comprimento_rolo)  # Arredonda para cima
            custo = rolos * tipo_fita.preco_rolo
            
            custos_fita_por_tipo[tipo_fita_id] = {
                'tipo_fita': tipo_fita,
                'total_metros': total_m,
                'rolos': int(rolos),
                'custo': custo
            }
        
        resultados[tipo_chapa_id] = {
            'tipo_chapa': tipo_chapa,
            'chapas': chapas,
            'custos_fita': custos_fita_por_tipo
        }
    
    session.close()
    return resultados


def exibir_resultados_otimizacao():
    """Exibe os resultados da otimização"""
    st.header("📊 Resultados da Otimização")
    
    resultados = st.session_state.resultados_otimizacao
    
    # Calcular totais gerais
    total_chapas_geral = sum(len(r['chapas']) for r in resultados.values())
    custo_total_chapas = sum(
        len(r['chapas']) * r['tipo_chapa'].preco 
        for r in resultados.values()
    )
    custo_total_fitas = sum(
        sum(cf['custo'] for cf in r['custos_fita'].values())
        for r in resultados.values()
    )
    custo_total_projeto = custo_total_chapas + custo_total_fitas
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Chapas", total_chapas_geral)
    
    with col2:
        st.metric("Custo Chapas", f"R$ {custo_total_chapas:.2f}")
    
    with col3:
        st.metric("Custo Fitas", f"R$ {custo_total_fitas:.2f}")
    
    with col4:
        st.metric("CUSTO TOTAL", f"R$ {custo_total_projeto:.2f}")
    
    st.divider()
    
    # Exibir cada tipo de material
    for tipo_chapa_id, resultado in resultados.items():
        tipo_chapa = resultado['tipo_chapa']
        chapas = resultado['chapas']
        custos_fita = resultado['custos_fita']
        
        custo_chapas_tipo = len(chapas) * tipo_chapa.preco
        custo_fitas_tipo = sum(cf['custo'] for cf in custos_fita.values())
        custo_total_tipo = custo_chapas_tipo + custo_fitas_tipo
        
        aproveitamento_medio = sum(c.calcular_utilizacao() for c in chapas) / len(chapas) if chapas else 0
        
        with st.expander(
            f"📦 {tipo_chapa.nome} - {len(chapas)} chapa(s) - Custo: R$ {custo_total_tipo:.2f}",
            expanded=True
        ):
            # Informações do tipo
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.markdown(f"**Dimensão:** {int(tipo_chapa.comprimento)}×{int(tipo_chapa.largura)}×{int(tipo_chapa.espessura)}mm")
                st.markdown(f"**Preço/chapa:** R$ {tipo_chapa.preco:.2f}")
            
            with col_info2:
                st.markdown(f"**Quantidade:** {len(chapas)} chapas")
                st.markdown(f"**Custo chapas:** R$ {custo_chapas_tipo:.2f}")
            
            with col_info3:
                st.markdown(f"**Aproveitamento:** {aproveitamento_medio:.1f}%")
                st.markdown(f"**Desperdício:** {100 - aproveitamento_medio:.1f}%")
            
            # Fitas usadas
            if custos_fita:
                st.markdown("##### 📏 Fitas de Borda Utilizadas")
                for fita_info in custos_fita.values():
                    tipo_fita = fita_info['tipo_fita']
                    st.markdown(
                        f"• **{tipo_fita.nome}**: {fita_info['total_metros']:.2f}m "
                        f"({fita_info['rolos']} rolos) - R$ {fita_info['custo']:.2f}"
                    )
            
            st.divider()
            
            # Diagramas das chapas
            for chapa in chapas:
                st.markdown(f"**Chapa {chapa.numero} - Aproveitamento: {chapa.calcular_utilizacao():.1f}%**")
                
                gerador = engine.GeradorDiagrama(chapa)
                fig = gerador.gerar_diagrama(dpi=100)
                st.pyplot(fig)
                plt.close(fig)
                
                # Detalhes
                total_pecas_chapa = sum(len(f.pecas) for f in chapa.faixas)
                st.caption(f"🔹 {total_pecas_chapa} peças | 🔹 Desperdício: {chapa.calcular_desperdicio():.1f}%")
                
                st.markdown("---")
    
    # ====================================================================
    # RESUMO FINAL E PDF
    # ====================================================================
    
    st.header("💰 Resumo Final do Projeto")
    
    # Resumo por tipo de material
    for tipo_chapa_id, resultado in resultados.items():
        tipo_chapa = resultado['tipo_chapa']
        chapas = resultado['chapas']
        custos_fita = resultado['custos_fita']
        
        custo_chapas = len(chapas) * tipo_chapa.preco
        custo_fitas = sum(cf['custo'] for cf in custos_fita.values())
        
        st.markdown(f"**{tipo_chapa.nome}:**")
        st.markdown(f"• {len(chapas)} chapas × R$ {tipo_chapa.preco:.2f} = R$ {custo_chapas:.2f}")
        
        if custos_fita:
            for fita_info in custos_fita.values():
                st.markdown(f"• Fita {fita_info['tipo_fita'].nome}: R$ {fita_info['custo']:.2f}")
    
    st.success(f"""
    📊 **RESUMO GERAL:**
    • {total_chapas_geral} chapas de MDF
    • Custo total de materiais: **R$ {custo_total_projeto:.2f}**
    """)
    
    # Botões de ação
    st.divider()
    
    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    
    with col_pdf1:
        if st.button("📄 GERAR PDF COMPLETO", use_container_width=True, type="primary"):
            with st.spinner("📝 Gerando PDF profissional..."):
                # Passar resultados completos com separação por tipo
                pdf_buffer = gerar_pdf_por_tipo(resultados, st.session_state.config_projeto)
                
                st.download_button(
                    label="⬇️ BAIXAR PLANO DE CORTE COMPLETO",
                    data=pdf_buffer,
                    file_name=f"corte_certo_{st.session_state.config_projeto.get('nome', 'projeto')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ PDF gerado com sucesso!")
    
    with col_pdf2:
        if st.button("🏷️ GERAR ETIQUETAS DAS PEÇAS", use_container_width=True):
            with st.spinner("🏷️ Gerando etiquetas..."):
                # Preparar dados para etiquetas
                todas_chapas = []
                for resultado in resultados.values():
                    todas_chapas.extend(resultado['chapas'])
                
                gerador_etiquetas = engine.GeradorEtiquetas(todas_chapas)
                etiquetas_buffer = gerador_etiquetas.gerar_etiquetas_pdf()
                
                total_pecas_etiquetas = sum(
                    len(f.pecas) for chapa in todas_chapas for f in chapa.faixas
                )
                
                st.download_button(
                    label="⬇️ BAIXAR ETIQUETAS",
                    data=etiquetas_buffer,
                    file_name=f"etiquetas_{st.session_state.config_projeto.get('nome', 'projeto')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success(f"✅ {total_pecas_etiquetas} etiquetas geradas com sucesso!")
    
    with col_pdf3:
        if st.button("💾 SALVAR PROJETO", use_container_width=True, type="secondary"):
            salvar_projeto_completo(
                st.session_state.config_projeto,
                st.session_state.pecas_otimizador,
                resultados,
                custo_total_projeto
            )
                
            st.download_button(
                    label="⬇️ BAIXAR ETIQUETAS",
                    data=etiquetas_buffer,
                    file_name=f"etiquetas_{st.session_state.config_projeto.get('nome', 'projeto')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            st.success(f"✅ {total_pecas_etiquetas} etiquetas geradas com sucesso!")
    
    # Informação sobre documentos
    st.info("""
    📋 **Documentos disponíveis:**
    • **PDF Completo**: Diagramas de corte + Resumo de materiais e custos
    • **Etiquetas**: 9 etiquetas por página A4 para identificação das peças
    """)


def salvar_projeto_completo(config_projeto, pecas_data, resultados, custo_total):
    """Salva projeto completo no banco de dados"""
    session = db_manager.get_session()
    
    try:
        # Buscar cliente se informado
        cliente_id = config_projeto.get('cliente_id')
        
        # Criar projeto
        novo_projeto = Projeto(
            nome=config_projeto.get('nome', 'Projeto Sem Nome'),
            cliente_id=cliente_id,
            kerf=config_projeto['kerf'],
            sentido_veio=config_projeto['sentido_veio'],
            custo_total=custo_total,
            observacoes=config_projeto.get('observacoes', '')
        )
        
        session.add(novo_projeto)
        session.flush()  # Para obter o ID do projeto
        
        # Salvar cada peça do projeto
        for peca_data in pecas_data:
            peca_projeto = PecaProjeto(
                projeto_id=novo_projeto.id,
                nome=peca_data['nome'],
                comprimento=peca_data['comprimento'],
                largura=peca_data['largura'],
                quantidade=peca_data['quantidade'],
                tipo_chapa_id=peca_data['tipo_chapa_id'],
                tipo_fita_id=peca_data['tipo_fita_id'],
                fita_borda_comp1=peca_data['fita_borda_comp1'],
                fita_borda_comp2=peca_data['fita_borda_comp2'],
                fita_borda_larg1=peca_data['fita_borda_larg1'],
                fita_borda_larg2=peca_data['fita_borda_larg2'],
                respeitar_veio=peca_data['respeitar_veio']
            )
            session.add(peca_projeto)
        
        session.commit()
        
        st.success(f"✅ Projeto '{novo_projeto.nome}' salvo com sucesso!")
        st.balloons()
        
    except Exception as e:
        session.rollback()
        st.error(f"❌ Erro ao salvar projeto: {str(e)}")
    finally:
        session.close()


def preparar_config_pdf(resultados, config_projeto):
    """Prepara configuração para geração do PDF"""
    # Pegar primeira chapa como referência (pode ser melhorado)
    primeira_chapa = list(resultados.values())[0]['tipo_chapa']
    
    config = {
        'comprimento_chapa': primeira_chapa.comprimento,
        'largura_chapa': primeira_chapa.largura,
        'espessura': primeira_chapa.espessura,
        'kerf': config_projeto['kerf'],
        'preco_chapa': primeira_chapa.preco,
        'sentido_veio': config_projeto['sentido_veio'],
        'nome_projeto': config_projeto.get('nome', 'Projeto'),
        # Fitas (média)
        'largura_rolo_fita': 22,
        'comprimento_rolo_fita': 50,
        'preco_rolo_fita': 25
    }
    
    return config


def gerar_pdf_por_tipo(resultados, config_projeto):
    """Gera PDF separado por tipo de chapa com custos individuais e total"""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    from io import BytesIO
    import matplotlib.pyplot as plt
    
    buffer = BytesIO()
    pdf = pdf_canvas.Canvas(buffer, pagesize=A4)
    largura_pagina, altura_pagina = A4
    
    # Calcular totais gerais
    total_chapas_geral = sum(len(r['chapas']) for r in resultados.values())
    custo_total_chapas = sum(len(r['chapas']) * r['tipo_chapa'].preco for r in resultados.values())
    custo_total_fitas = sum(sum(cf['custo'] for cf in r['custos_fita'].values()) for r in resultados.values())
    custo_total_projeto = custo_total_chapas + custo_total_fitas
    
    # ====================================================================
    # PROCESSAR CADA TIPO DE CHAPA
    # ====================================================================
    
    for tipo_chapa_id, resultado in resultados.items():
        tipo_chapa = resultado['tipo_chapa']
        chapas = resultado['chapas']
        custos_fita = resultado['custos_fita']
        
        # ================================================================
        # DIAGRAMAS DAS CHAPAS + LISTA DE PEÇAS
        # ================================================================
        
        for chapa in chapas:
            # Gerar diagrama
            gerador = engine.GeradorDiagrama(chapa)
            fig = gerador.gerar_diagrama(dpi=150)
            
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            
            pil_image = Image.open(img_buffer)
            img_reader = ImageReader(pil_image)
            
            # Título da página
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, altura_pagina - 40, f"{tipo_chapa.nome} - Chapa {chapa.numero}")
            
            # Dimensões da imagem
            img_width, img_height = pil_image.size
            scale = min(
                (largura_pagina - 100) / img_width,
                ((altura_pagina - 300) / img_height)
            )
            
            nova_largura = img_width * scale
            nova_altura = img_height * scale
            
            x_img = (largura_pagina - nova_largura) / 2
            y_img = altura_pagina - 80 - nova_altura
            
            # Desenhar diagrama
            pdf.drawImage(img_reader, x_img, y_img, width=nova_largura, height=nova_altura, preserveAspectRatio=True)
            
            # Lista de peças desta chapa
            y = y_img - 30
            
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(50, y, "Peças desta chapa:")
            y -= 18
            
            pdf.setFont("Helvetica", 9)
            
            # Coletar todas as peças
            pecas_chapa = []
            for faixa in chapa.faixas:
                for peca_pos in faixa.pecas:
                    pecas_chapa.append(peca_pos.peca)
            
            # Agrupar peças iguais
            pecas_agrupadas = {}
            for peca in pecas_chapa:
                chave = f"{peca.nome}_{peca.comprimento}_{peca.largura}"
                if chave not in pecas_agrupadas:
                    pecas_agrupadas[chave] = {'peca': peca, 'qtd': 0}
                pecas_agrupadas[chave]['qtd'] += 1
            
            # Listar peças
            for info in pecas_agrupadas.values():
                peca = info['peca']
                qtd = info['qtd']
                
                # Formatar fitas
                bordas = []
                if peca.fita_borda_comp1:
                    bordas.append("▲")
                if peca.fita_borda_comp2:
                    bordas.append("▼")
                if peca.fita_borda_larg1:
                    bordas.append("◀")
                if peca.fita_borda_larg2:
                    bordas.append("▶")
                fitas_str = " ".join(bordas) if bordas else "-"
                
                texto = f"• {peca.nome} ({int(peca.comprimento)}×{int(peca.largura)}mm) - Qtd: {qtd}"
                if fitas_str != "-":
                    texto += f" - Fita: {fitas_str}"
                
                pdf.drawString(60, y, texto)
                y -= 15
            
            # Aproveitamento
            y -= 10
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(50, y, f"Aproveitamento: {chapa.calcular_utilizacao():.1f}% | Desperdício: {chapa.calcular_desperdicio():.1f}%")
            
            pdf.showPage()
            plt.close(fig)
            img_buffer.close()
        
        # ================================================================
        # RESUMO DE CUSTOS DESTE TIPO DE CHAPA
        # ================================================================
        
        custo_chapas_tipo = len(chapas) * tipo_chapa.preco
        custo_fitas_tipo = sum(cf['custo'] for cf in custos_fita.values())
        custo_total_tipo = custo_chapas_tipo + custo_fitas_tipo
        
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(largura_pagina / 2, altura_pagina - 50, 
                            f"RESUMO DE CUSTOS - {tipo_chapa.nome}")
        
        y = altura_pagina - 100
        
        # Informações da chapa
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, y, f"Dimensão da chapa: {int(tipo_chapa.comprimento)}×{int(tipo_chapa.largura)}×{int(tipo_chapa.espessura)}mm")
        y -= 25
        
        # Custo das chapas
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, y, "CHAPAS:")
        y -= 22
        
        pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y, f"Quantidade: {len(chapas)} chapas")
        y -= 18
        pdf.drawString(60, y, f"Preço unitário: R$ {tipo_chapa.preco:.2f}")
        y -= 18
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(60, y, f"Custo total chapas: R$ {custo_chapas_tipo:.2f}")
        y -= 35
        
        # Custo das fitas
        if custos_fita:
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawString(50, y, "FITAS DE BORDA:")
            y -= 22
            
            pdf.setFont("Helvetica", 11)
            for fita_info in custos_fita.values():
                tipo_fita = fita_info['tipo_fita']
                pdf.drawString(60, y, f"• {tipo_fita.nome}:")
                y -= 18
                pdf.drawString(70, y, f"Total necessário: {fita_info['total_metros']:.2f} metros")
                y -= 18
                pdf.drawString(70, y, f"Rolos: {fita_info['rolos']} rolos de {tipo_fita.comprimento_rolo}m")
                y -= 18
                pdf.drawString(70, y, f"Preço por rolo: R$ {tipo_fita.preco_rolo:.2f}")
                y -= 18
                
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(70, y, f"Custo total fitas: R$ {fita_info['custo']:.2f}")
                pdf.setFont("Helvetica", 11)
                y -= 25
        
        # Total deste tipo
        y -= 10
        pdf.setFillColorRGB(0.9, 0.9, 0.9)
        pdf.rect(40, y - 35, largura_pagina - 80, 45, fill=1, stroke=1)
        
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(50, y - 15, f"CUSTO TOTAL - {tipo_chapa.nome}:")
        pdf.drawString(400, y - 15, f"R$ {custo_total_tipo:.2f}")
        
        pdf.showPage()
    
    # ====================================================================
    # PÁGINA FINAL - RESUMO TOTAL
    # ====================================================================
    
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(largura_pagina / 2, altura_pagina - 50, "RESUMO GERAL DO PROJETO")
    
    y = altura_pagina - 100
    
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Projeto: {config_projeto.get('nome', 'Sem nome')}")
    y -= 20
    pdf.drawString(50, y, f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}")
    y -= 40
    
    # Resumo por tipo
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "CUSTOS POR TIPO DE MATERIAL:")
    y -= 30
    
    for tipo_chapa_id, resultado in resultados.items():
        tipo_chapa = resultado['tipo_chapa']
        chapas = resultado['chapas']
        custos_fita = resultado['custos_fita']
        
        custo_chapas = len(chapas) * tipo_chapa.preco
        custo_fitas = sum(cf['custo'] for cf in custos_fita.values())
        custo_total_material = custo_chapas + custo_fitas
        
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"• {tipo_chapa.nome}")
        y -= 20
        
        pdf.setFont("Helvetica", 10)
        pdf.drawString(70, y, f"{len(chapas)} chapas × R$ {tipo_chapa.preco:.2f} = R$ {custo_chapas:.2f}")
        y -= 16
        
        if custos_fita:
            total_fitas_material = sum(cf['custo'] for cf in custos_fita.values())
            pdf.drawString(70, y, f"Fitas de borda = R$ {total_fitas_material:.2f}")
            y -= 16
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(70, y, f"Subtotal: R$ {custo_total_material:.2f}")
        y -= 30
    
    # Total geral
    y -= 20
    pdf.setFillColorRGB(0.85, 0.85, 0.85)
    pdf.rect(40, y - 60, largura_pagina - 80, 75, fill=1, stroke=1)
    
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y - 15, "Total de Chapas:")
    pdf.drawString(450, y - 15, f"{total_chapas_geral}")
    
    y -= 25
    pdf.drawString(50, y - 15, "Custo Chapas:")
    pdf.drawString(400, y - 15, f"R$ {custo_total_chapas:.2f}")
    
    y -= 25
    pdf.drawString(50, y - 15, "Custo Fitas:")
    pdf.drawString(400, y - 15, f"R$ {custo_total_fitas:.2f}")
    
    y -= 35
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y - 15, "CUSTO TOTAL:")
    pdf.drawString(380, y - 15, f"R$ {custo_total_projeto:.2f}")
    
    # Rodapé
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(largura_pagina / 2, 30, 
                         f"Corte Certo Pro - Sistema de Otimização | Gerado em {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}")
    
    pdf.save()
    buffer.seek(0)
    return buffer

# ============================================================================
# TELA: PROJETOS
# ============================================================================

def tela_projetos():
    """Tela de gerenciamento de projetos"""
    st.title("📁 Gerenciamento de Projetos")
    
    session = db_manager.get_session()
    projetos = session.query(Projeto).order_by(Projeto.data_criacao.desc()).all()
    
    if not projetos:
        st.info("📋 Nenhum projeto salvo ainda. Crie um projeto no Otimizador e clique em '💾 Salvar Projeto'.")
        session.close()
        return
    
    st.subheader(f"Total: {len(projetos)} projeto(s) salvo(s)")
    
    # Listar projetos
    for projeto in projetos:
        # Buscar cliente se houver
        cliente_nome = "Sem cliente"
        if projeto.cliente_id:
            cliente = session.query(Cliente).get(projeto.cliente_id)
            if cliente:
                cliente_nome = cliente.nome
        
        # Contar peças
        total_pecas = sum(p.quantidade for p in projeto.pecas)
        
        with st.expander(
            f"📂 {projeto.nome} - {cliente_nome} | R$ {projeto.custo_total:.2f} | {total_pecas} peças",
            expanded=False
        ):
            # Informações do projeto
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown(f"**Cliente:** {cliente_nome}")
                st.markdown(f"**Data:** {projeto.data_criacao.strftime('%d/%m/%Y às %H:%M')}")
                st.markdown(f"**Kerf:** {projeto.kerf}mm")
            
            with col_info2:
                st.markdown(f"**Custo Total:** R$ {projeto.custo_total:.2f}")
                st.markdown(f"**Total de Peças:** {total_pecas}")
                st.markdown(f"**Sentido Veio:** {projeto.sentido_veio}")
            
            if projeto.observacoes:
                st.markdown(f"**Observações:** {projeto.observacoes}")
            
            st.markdown("---")
            
            # Agrupar peças por tipo de chapa
            pecas_por_chapa = {}
            for peca in projeto.pecas:
                chapa_id = peca.tipo_chapa_id
                if chapa_id not in pecas_por_chapa:
                    tipo_chapa = session.query(TipoChapa).get(chapa_id)
                    pecas_por_chapa[chapa_id] = {
                        'tipo': tipo_chapa,
                        'pecas': []
                    }
                pecas_por_chapa[chapa_id]['pecas'].append(peca)
            
            # Exibir peças por grupo
            for chapa_id, grupo in pecas_por_chapa.items():
                tipo_chapa = grupo['tipo']
                pecas_grupo = grupo['pecas']
                
                st.markdown(f"**📦 {tipo_chapa.nome}:**")
                
                # Criar tabela de peças
                dados_tabela = []
                for peca in pecas_grupo:
                    # Buscar tipo de fita
                    tipo_fita_nome = "-"
                    if peca.tipo_fita_id:
                        tipo_fita = session.query(TipoFita).get(peca.tipo_fita_id)
                        if tipo_fita:
                            tipo_fita_nome = tipo_fita.nome
                    
                    # Formatar bordas
                    bordas = []
                    if peca.fita_borda_comp1:
                        bordas.append("▲")
                    if peca.fita_borda_comp2:
                        bordas.append("▼")
                    if peca.fita_borda_larg1:
                        bordas.append("◀")
                    if peca.fita_borda_larg2:
                        bordas.append("▶")
                    fitas_str = " ".join(bordas) if bordas else "-"
                    
                    dados_tabela.append({
                        'Nome': peca.nome,
                        'Comp. (mm)': int(peca.comprimento),
                        'Larg. (mm)': int(peca.largura),
                        'Qtd': peca.quantidade,
                        'Tipo Fita': tipo_fita_nome,
                        'Bordas': fitas_str,
                        'Veio': '🌾' if peca.respeitar_veio else '-'
                    })
                
                df = pd.DataFrame(dados_tabela)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("")
            
            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
            
            with col_btn1:
                if st.button("🔄 Recarregar", key=f"reload_{projeto.id}", use_container_width=True):
                    # Recarregar projeto no otimizador
                    st.session_state.pecas_otimizador = []
                    for peca in projeto.pecas:
                        peca_data = {
                            'nome': peca.nome,
                            'comprimento': peca.comprimento,
                            'largura': peca.largura,
                            'quantidade': peca.quantidade,
                            'tipo_chapa_id': peca.tipo_chapa_id,
                            'tipo_fita_id': peca.tipo_fita_id,
                            'fita_borda_comp1': peca.fita_borda_comp1,
                            'fita_borda_comp2': peca.fita_borda_comp2,
                            'fita_borda_larg1': peca.fita_borda_larg1,
                            'fita_borda_larg2': peca.fita_borda_larg2,
                            'respeitar_veio': peca.respeitar_veio
                        }
                        st.session_state.pecas_otimizador.append(peca_data)
                    
                    st.session_state.config_projeto = {
                        'nome': projeto.nome,
                        'cliente_id': projeto.cliente_id,
                        'kerf': projeto.kerf,
                        'sentido_veio': projeto.sentido_veio,
                        'observacoes': projeto.observacoes
                    }
                    
                    st.session_state.menu_atual = 'Otimizador'
                    st.success(f"✅ Projeto '{projeto.nome}' recarregado no otimizador!")
                    st.rerun()
            
            with col_btn2:
                if st.button("🗑️ Excluir", key=f"del_proj_{projeto.id}", use_container_width=True):
                    st.session_state.deleting_projeto_id = projeto.id
                    st.rerun()
    
    session.close()
    
    # Modal de exclusão
    if 'deleting_projeto_id' in st.session_state:
        modal_excluir_projeto()


@st.dialog("🗑️ Excluir Projeto")
def modal_excluir_projeto():
    """Modal para confirmar exclusão de projeto"""
    session = db_manager.get_session()
    projeto = session.query(Projeto).get(st.session_state.deleting_projeto_id)
    
    if projeto:
        st.warning(f"⚠️ Tem certeza que deseja excluir o projeto **{projeto.nome}**?")
        st.write("Esta ação não pode ser desfeita. Todas as peças do projeto serão removidas.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sim, excluir", key="confirm_del_proj", use_container_width=True, type="primary"):
                # Excluir peças primeiro (cascade deveria fazer isso, mas por segurança)
                for peca in projeto.pecas:
                    session.delete(peca)
                
                session.delete(projeto)
                session.commit()
                session.close()
                del st.session_state.deleting_projeto_id
                st.success("✅ Projeto excluído com sucesso!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar", key="cancel_del_proj", use_container_width=True):
                session.close()
                del st.session_state.deleting_projeto_id
                st.rerun()
    else:
        session.close()

# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    init_session_state()
    menu_lateral()
    
    # Roteamento de telas
    if st.session_state.menu_atual == 'Otimizador':
        tela_otimizador()
    elif st.session_state.menu_atual == 'Clientes':
        tela_clientes()
    elif st.session_state.menu_atual == 'Chapas':
        tela_chapas()
    elif st.session_state.menu_atual == 'Fitas':
        tela_fitas()
    elif st.session_state.menu_atual == 'Projetos':
        tela_projetos()

if __name__ == "__main__":
    main()