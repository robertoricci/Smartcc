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
            
            for cliente in clientes:
                with st.expander(f"🏢 {cliente.nome}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Telefone:** {cliente.telefone or '-'}")
                        st.markdown(f"**Email:** {cliente.email or '-'}")
                        st.markdown(f"**CPF/CNPJ:** {cliente.cpf_cnpj or '-'}")
                        st.markdown(f"**Endereço:** {cliente.endereco or '-'}")
                        if cliente.observacoes:
                            st.markdown(f"**Obs:** {cliente.observacoes}")
                    
                    with col2:
                        if st.button("🗑️ Excluir", key=f"del_cli_{cliente.id}"):
                            session.delete(cliente)
                            session.commit()
                            st.success("Cliente excluído!")
                            st.rerun()
        else:
            st.info("Nenhum cliente cadastrado ainda.")
        
        session.close()
    
    with tab2:
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
                    st.error("Nome é obrigatório!")
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
                    st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
                    st.rerun()

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
                        if st.button("🗑️ Excluir", key=f"del_chapa_{chapa.id}"):
                            chapa.ativo = False
                            session.commit()
                            st.success("Chapa removida!")
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
            
            for fita in fitas:
                with st.expander(f"📏 {fita.descricao_completa()}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Largura:** {int(fita.largura)}mm")
                        st.markdown(f"**Rolo:** {fita.comprimento_rolo}m")
                        st.markdown(f"**Cor:** {fita.cor or '-'}")
                        st.markdown(f"**Material:** {fita.material or '-'}")
                        st.markdown(f"**Fornecedor:** {fita.fornecedor or '-'}")
                        st.markdown(f"**Preço/rolo:** R$ {fita.preco_rolo:.2f}")
                    
                    with col2:
                        if st.button("🗑️ Excluir", key=f"del_fita_{fita.id}"):
                            fita.ativo = False
                            session.commit()
                            st.success("Fita removida!")
                            st.rerun()
        else:
            st.info("Nenhuma fita cadastrada.")
        
        session.close()
    
    with tab2:
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
                    st.error("Nome é obrigatório!")
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
                    st.success(f"✅ Fita '{nome}' cadastrada com sucesso!")
                    st.rerun()

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
        fita_comp1 = fita_comp2 = fita_larg1 = fita_larg2 = False
        
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
            
            # Só mostra bordas se selecionou uma fita (tipo_fita_id não é None)
            if tipo_fita_id is not None:
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
        else:
            st.info("💡 Nenhuma fita cadastrada. Vá em 'Tipos de Fita' para cadastrar.")
            tipo_fita_id = None
        
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
        
        for peca in st.session_state.pecas_otimizador:
            chapa_id = peca['tipo_chapa_id']
            if chapa_id not in pecas_por_chapa:
                tipo_chapa = session.query(TipoChapa).get(chapa_id)
                pecas_por_chapa[chapa_id] = {
                    'tipo': tipo_chapa,
                    'pecas': []
                }
            pecas_por_chapa[chapa_id]['pecas'].append(peca)
        
        # Exibir por grupo
        for chapa_id, grupo in pecas_por_chapa.items():
            tipo_chapa = grupo['tipo']
            pecas = grupo['pecas']
            
            with st.expander(f"📦 {tipo_chapa.nome} - {len(pecas)} peça(s)", expanded=True):
                # Criar DataFrame
                dados_tabela = []
                for idx, p in enumerate(pecas):
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
                
                # Botão para remover peça
                col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 6])
                with col_btn1:
                    if st.button(f"🗑️ Limpar Grupo", key=f"limpar_grupo_{chapa_id}"):
                        st.session_state.pecas_otimizador = [
                            p for p in st.session_state.pecas_otimizador 
                            if p['tipo_chapa_id'] != chapa_id
                        ]
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
    
    # Botão de gerar PDF
    st.divider()
    
    col_pdf1, col_pdf2 = st.columns(2)
    
    with col_pdf1:
        if st.button("📄 GERAR PDF COMPLETO", use_container_width=True, type="primary"):
            with st.spinner("📝 Gerando PDF profissional..."):
                # Preparar dados para PDF
                todas_chapas = []
                for resultado in resultados.values():
                    todas_chapas.extend(resultado['chapas'])
                
                # Configuração para PDF
                config_pdf = preparar_config_pdf(resultados, st.session_state.config_projeto)
                
                gerador_pdf = engine.GeradorPDF(todas_chapas, config=config_pdf)
                pdf_buffer = gerador_pdf.gerar_pdf()
                
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
    
    # Informação sobre documentos
    st.info("""
    📋 **Documentos disponíveis:**
    • **PDF Completo**: Diagramas de corte + Resumo de materiais e custos
    • **Etiquetas**: 9 etiquetas por página A4 para identificação das peças
    """)


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

# ============================================================================
# TELA: PROJETOS
# ============================================================================

def tela_projetos():
    """Tela de gerenciamento de projetos"""
    st.title("📁 Gerenciamento de Projetos")
    st.info("Esta funcionalidade será implementada na próxima etapa...")

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