"""
Database Models - Corte Certo
Sistema de banco de dados com SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Base para os modelos
Base = declarative_base()

# ============================================================================
# MODELOS
# ============================================================================

class Cliente(Base):
    """Modelo para cadastro de clientes"""
    __tablename__ = 'clientes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    telefone = Column(String(20))
    email = Column(String(100))
    endereco = Column(String(300))
    cpf_cnpj = Column(String(20))
    observacoes = Column(String(500))
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    projetos = relationship("Projeto", back_populates="cliente")
    
    def __repr__(self):
        return f"<Cliente(id={self.id}, nome='{self.nome}')>"


class TipoChapa(Base):
    """Modelo para tipos de chapa MDF"""
    __tablename__ = 'tipos_chapa'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)  # Ex: "MDF Cru 15mm"
    comprimento = Column(Float, nullable=False)  # mm
    largura = Column(Float, nullable=False)  # mm
    espessura = Column(Float, nullable=False)  # mm
    preco = Column(Float, nullable=False)  # R$
    cor = Column(String(50))  # Ex: "Natural", "Branco", "Preto"
    acabamento = Column(String(50))  # Ex: "Cru", "BP", "Laca"
    fornecedor = Column(String(100))
    observacoes = Column(String(300))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<TipoChapa(id={self.id}, nome='{self.nome}')>"
    
    def descricao_completa(self):
        return f"{self.nome} - {int(self.comprimento)}×{int(self.largura)}×{int(self.espessura)}mm - R$ {self.preco:.2f}"


class TipoFita(Base):
    """Modelo para tipos de fita de borda"""
    __tablename__ = 'tipos_fita'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)  # Ex: "Fita Branca 22mm"
    largura = Column(Float, nullable=False)  # mm
    comprimento_rolo = Column(Float, nullable=False)  # metros
    preco_rolo = Column(Float, nullable=False)  # R$
    cor = Column(String(50))  # Ex: "Branco", "Preto", "Amadeirado"
    material = Column(String(50))  # Ex: "PVC", "ABS", "Melamínico"
    fornecedor = Column(String(100))
    observacoes = Column(String(300))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<TipoFita(id={self.id}, nome='{self.nome}')>"
    
    def descricao_completa(self):
        return f"{self.nome} - {int(self.largura)}mm - {self.comprimento_rolo}m/rolo - R$ {self.preco_rolo:.2f}"


class Projeto(Base):
    """Modelo para projetos de corte"""
    __tablename__ = 'projetos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    descricao = Column(String(500))
    kerf = Column(Float, default=3.0)  # mm
    sentido_veio = Column(String(50), default="Horizontal (no comprimento)")
    status = Column(String(50), default="Em Orçamento")  # Em Orçamento, Aprovado, Em Produção, Concluído
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="projetos")
    pecas = relationship("PecaProjeto", back_populates="projeto", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Projeto(id={self.id}, nome='{self.nome}')>"


class PecaProjeto(Base):
    """Modelo para peças do projeto"""
    __tablename__ = 'pecas_projeto'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    projeto_id = Column(Integer, ForeignKey('projetos.id'), nullable=False)
    tipo_chapa_id = Column(Integer, ForeignKey('tipos_chapa.id'), nullable=False)
    tipo_fita_id = Column(Integer, ForeignKey('tipos_fita.id'))  # Pode ser null
    
    nome = Column(String(100), nullable=False)
    comprimento = Column(Float, nullable=False)  # mm
    largura = Column(Float, nullable=False)  # mm
    quantidade = Column(Integer, nullable=False, default=1)
    
    # Fita de borda
    fita_borda_comp1 = Column(Boolean, default=False)
    fita_borda_comp2 = Column(Boolean, default=False)
    fita_borda_larg1 = Column(Boolean, default=False)
    fita_borda_larg2 = Column(Boolean, default=False)
    
    # Veio
    respeitar_veio = Column(Boolean, default=False)
    
    observacoes = Column(String(300))
    
    # Relacionamentos
    projeto = relationship("Projeto", back_populates="pecas")
    tipo_chapa = relationship("TipoChapa")
    tipo_fita = relationship("TipoFita")
    
    def __repr__(self):
        return f"<PecaProjeto(id={self.id}, nome='{self.nome}')>"
    
    def comprimento_fita(self) -> float:
        """Calcula total de fita necessária em mm"""
        total = 0
        if self.fita_borda_comp1:
            total += self.comprimento
        if self.fita_borda_comp2:
            total += self.comprimento
        if self.fita_borda_larg1:
            total += self.largura
        if self.fita_borda_larg2:
            total += self.largura
        return total


# ============================================================================
# FUNÇÕES DE GERENCIAMENTO DO BANCO
# ============================================================================

class DatabaseManager:
    """Gerenciador do banco de dados"""
    
    def __init__(self, db_path='corte_certo.db'):
        """Inicializa o banco de dados"""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Retorna uma nova sessão"""
        return self.Session()
    
    def criar_dados_exemplo(self):
        """Cria dados de exemplo no banco"""
        session = self.get_session()
        
        try:
            # Verificar se já existem dados
            if session.query(TipoChapa).count() > 0:
                return  # Já tem dados
            
            # Tipos de Chapa
            chapas_exemplo = [
                TipoChapa(
                    nome="MDF Cru 15mm",
                    comprimento=2750,
                    largura=1840,
                    espessura=15,
                    preco=180.00,
                    cor="Natural",
                    acabamento="Cru"
                ),
                TipoChapa(
                    nome="MDF Branco 18mm",
                    comprimento=2750,
                    largura=1840,
                    espessura=18,
                    preco=250.00,
                    cor="Branco",
                    acabamento="BP"
                ),
                TipoChapa(
                    nome="MDF Preto 15mm",
                    comprimento=2750,
                    largura=1840,
                    espessura=15,
                    preco=280.00,
                    cor="Preto",
                    acabamento="BP"
                ),
                TipoChapa(
                    nome="MDF Cru 25mm",
                    comprimento=2750,
                    largura=1840,
                    espessura=25,
                    preco=320.00,
                    cor="Natural",
                    acabamento="Cru"
                ),
            ]
            
            # Tipos de Fita
            fitas_exemplo = [
                TipoFita(
                    nome="Fita Branca 22mm",
                    largura=22,
                    comprimento_rolo=50,
                    preco_rolo=25.00,
                    cor="Branco",
                    material="PVC"
                ),
                TipoFita(
                    nome="Fita Preta 22mm",
                    largura=22,
                    comprimento_rolo=50,
                    preco_rolo=28.00,
                    cor="Preto",
                    material="PVC"
                ),
                TipoFita(
                    nome="Fita Amadeirada 35mm",
                    largura=35,
                    comprimento_rolo=50,
                    preco_rolo=45.00,
                    cor="Amadeirado",
                    material="Melamínico"
                ),
                TipoFita(
                    nome="Fita ABS Branca 22mm",
                    largura=22,
                    comprimento_rolo=50,
                    preco_rolo=35.00,
                    cor="Branco",
                    material="ABS"
                ),
            ]
            
            # Cliente exemplo
            cliente_exemplo = Cliente(
                nome="Cliente Exemplo",
                telefone="(11) 98765-4321",
                email="exemplo@email.com",
                endereco="Rua Exemplo, 123 - São Paulo/SP"
            )
            
            session.add_all(chapas_exemplo)
            session.add_all(fitas_exemplo)
            session.add(cliente_exemplo)
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Erro ao criar dados de exemplo: {e}")
        finally:
            session.close()


# Instância global do gerenciador
db_manager = DatabaseManager()