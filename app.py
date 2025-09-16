# -*- coding: utf-8 -*-
"""
Dashboard Avançado para Análise de Dados da Atenção Primária à Saúde (APS) - v6.2

Este script utiliza Streamlit para criar uma interface interativa e rica em
funcionalidades para gestores da APS.

LOG DE ALTERAÇÕES (v6.2 - Análise Estratégica ESB):
- REFORMULAÇÃO DA ABA 'TIPOS DE CONSULTAS ESB': A aba foi reconstruída com foco
  em insights gerenciais, analisando a performance das unidades em 'Captação de
  Novos Pacientes' vs. 'Continuidade do Cuidado'.
- NOVOS KPIs E GRÁFICOS ESTRATÉGICOS: Adicionados KPIs de performance, um gráfico
  de rosca para o perfil geral do cuidado e gráficos de ranking para destacar
  as unidades com melhor desempenho em cada área.
- ANÁLISE GUIADA POR ABAS: A navegação foi reestruturada em abas que respondem
  a perguntas-chave de um gestor de saúde bucal.
"""

import io
import os
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER O 1º COMANDO STREAMLIT) ---
st.set_page_config(page_title="Dashboard de Gestão APS", layout="wide")

# ==============================================================================
# 1. CONSTANTES E CONFIGURAÇÕES
# ==============================================================================

COL_STATUS_DOC = 'STATUS DOCUMENTO'
COL_TEMPO_SEM_ATUALIZAR = 'TEMPO SEM ATUALIZAR'
COL_UNIDADE = 'UNIDADE DE SAÚDE'
COL_NOME_EQUIPE = 'NOME EQUIPE'
COL_INE = 'INE'
COL_CIDADAO = 'CIDADÃO'
COL_EQUIPE_COMPLETA = 'EQUIPE_COMPLETA'
COL_FAMILIA_VINCULADA = 'TEM FAMÍLIA VÍNCULADA?'
DOM_COL_UNIDADE = 'Estabelecimento'

CONFIG_VISUAL: Dict[str, Any] = {
    'cores_status': {
        '✅ Dentro do Parâmetro': '#28a745',
        '⚠️ Acima do Parâmetro': '#ffc107',
        '🚨 ACIMA DO LIMITE MÁXIMO': '#dc3545'
    },
    'ordem_tempo': ['ATÉ 4 MESES', '5 A 12 MESES', '13 A 24 MESES', 'MAIS DE 2 ANOS'],
    'ordem_cpf': ['COM CPF', 'SEM CPF']
}

# ==============================================================================
# 2. FUNÇÕES UTILITÁRIAS E CARREGAMENTO DE DADOS
# ==============================================================================

def _normalize_text(text: str) -> str:
    if not isinstance(text, str): return ""
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode().upper().strip()

@st.cache_data
def carregar_parametros() -> pd.DataFrame:
    """
    Carrega os parâmetros de todos os municípios. A identificação de equipes EAP
    é feita pelo NÚMERO DE INE para máxima precisão.
    
    !!!! ATENÇÃO !!!!
    É CRÍTICO que você edite a seção `eap_por_ine` abaixo, substituindo
    os INEs de exemplo pelos INEs REAIS das suas equipes EAP.
    """
    PARAMETROS_POR_MUNICIPIO = {
        # --- MUNICÍPIOS COM EQUIPES EAP (CONFIGURAR AQUI) ---
        'ALHANDRA-PB':            {'parametro_esf': 2500, 'limite_esf': 3750, 'eap_por_ine': {
                                      '0009999': {'tipo': '30', 'parametro': 1875, 'limite_maximo': 2813} # SUBSTITUIR PELO INE REAL
                                  }},
        'MACAÍBA-RN':             {'parametro_esf': 2750, 'limite_esf': 4125, 'eap_por_ine': {
                                      '0001234': {'tipo': '20', 'parametro': 1375, 'limite_maximo': 2063}, # SUBSTITUIR PELO INE REAL
                                      '0005678': {'tipo': '30', 'parametro': 1875, 'limite_maximo': 2813}  # SUBSTITUIR PELO INE REAL
                                  }},
        'VALENÇA-RJ':             {'parametro_esf': 2750, 'limite_esf': 4125, 'eap_por_ine': {
                                      '0004321': {'tipo': '20', 'parametro': 1375, 'limite_maximo': 2063} # SUBSTITUIR PELO INE REAL
                                  }},
        
        # --- MUNICÍPIOS APENAS COM EQUIPES ESF ---
        'ÁGUA PRETA-PE':          {'parametro_esf': 2500, 'limite_esf': 3750},
        'ÁGUAS BELAS-PE':         {'parametro_esf': 2500, 'limite_esf': 3750},
        'ALTO DO RODRIGUES-RN':   {'parametro_esf': 2000, 'limite_esf': 3000},
        'APODI-RN':               {'parametro_esf': 2500, 'limite_esf': 3750},
        'ARAPONGA-MG':            {'parametro_esf': 2000, 'limite_esf': 3000},
        'AREIA-PB':               {'parametro_esf': 2500, 'limite_esf': 3750},
        'AÇU-RN':                 {'parametro_esf': 2750, 'limite_esf': 4125},
        'BRUMADO-BA':             {'parametro_esf': 2750, 'limite_esf': 4125},
        'CAAPORÃ-PB':             {'parametro_esf': 2500, 'limite_esf': 3750},
        'CALDAS BRANDÃO-PB':      {'parametro_esf': 2000, 'limite_esf': 3000},
        'CANAÃ-MG':               {'parametro_esf': 2000, 'limite_esf': 3000},
        'CARNAUBAIS-RN':          {'parametro_esf': 2000, 'limite_esf': 3000},
        'CONDE-PB':               {'parametro_esf': 2500, 'limite_esf': 3750},
        'CORDEIRO-RJ':            {'parametro_esf': 2500, 'limite_esf': 3750},
        'FERNANDO PEDROZA-RN':    {'parametro_esf': 2000, 'limite_esf': 3000},
        'GROSSOS-RN':             {'parametro_esf': 2000, 'limite_esf': 3000},
        'GUARABIRA-PB':           {'parametro_esf': 2750, 'limite_esf': 4125},
        'ITABAIANA-PB':           {'parametro_esf': 2500, 'limite_esf': 3750},
        'ITAPOROROCA-PB':         {'parametro_esf': 2000, 'limite_esf': 3000},
        'ITATUBA-PB':             {'parametro_esf': 2000, 'limite_esf': 3000},
        'MOGEIRO-PB':             {'parametro_esf': 2000, 'limite_esf': 3000},
        'PATU-RN':                {'parametro_esf': 2000, 'limite_esf': 3000},
        'PAULA CÂNDIDO-MG':       {'parametro_esf': 2000, 'limite_esf': 3000},
        'PEDRO VELHO-RN':         {'parametro_esf': 2000, 'limite_esf': 3000},
        'PENDÊNCIAS-RN':          {'parametro_esf': 2000, 'limite_esf': 3000},
        'POÇO BRANCO-RN':         {'parametro_esf': 2000, 'limite_esf': 3000},
        'SANTA RITA-PB':          {'parametro_esf': 3000, 'limite_esf': 4500},
        'SÃO JOSÉ DE UBÁ-RJ':     {'parametro_esf': 2000, 'limite_esf': 3000},
        'SÃO MIGUEL DO ANTA-MG':  {'parametro_esf': 2000, 'limite_esf': 3000},
        'TIBAU-RN':               {'parametro_esf': 2000, 'limite_esf': 3000},
        'VIÇOSA-MG':              {'parametro_esf': 2750, 'limite_esf': 4125},
        'VIÇOSA DO CEARÁ-CE':     {'parametro_esf': 2750, 'limite_esf': 4125},
    }
    
    data_list = []
    for municipio_uf, params in PARAMETROS_POR_MUNICIPIO.items():
        try:
            nome, uf = municipio_uf.rsplit('-', 1)
            row = {
                'MUNICIPIO': nome, 'UF': uf,
                'PARAMETRO_ESF': params['parametro_esf'],
                'LIMITE_ESF': params['limite_esf'],
                'EAP_POR_INE': params.get('eap_por_ine', {})
            }
            data_list.append(row)
        except ValueError:
            print(f"Aviso: Chave de município mal formatada e ignorada: {municipio_uf}")
    return pd.DataFrame(data_list)

def exportar_excel(df: pd.DataFrame, nome_arquivo: str):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name="Dados")
    st.download_button(
        label="⬇️ Baixar em Excel", data=buffer.getvalue(),
        file_name=nome_arquivo, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def render_alert_panel(message: str, type: str = "info"):
    colors = {"info": "#3281ed", "success": "#23914b", "warning": "#ae8602", "critical": "#cb3b36"}
    st.markdown(f'<div style="background:{colors[type]};padding:13px 15px;border-radius:12px;margin-bottom:10px;color:#fff;">{message}</div>', unsafe_allow_html=True)

# ==============================================================================
# 3. CLASSE PRINCIPAL DO DASHBOARD
# ==============================================================================

class DashboardAPS:
    def __init__(self):
        if "logged_in" not in st.session_state: st.session_state.logged_in = False
        if "view" not in st.session_state: st.session_state.view = "menu"
        self.df_parametros = carregar_parametros()
        self.df_cid_bruto = self.df_cid_filtrado = self.df_dom_bruto = self.df_dom_filtrado = self.df_prod_bruto = self.df_prod_filtrado = self.df_vinculos = None
        self.municipio_selecionado: Optional[str] = None
        self.unidade_selecionada: str = 'Todas'
        self.periodo_selecionado: Optional[Tuple] = None
        self.parametro_oficial = self.limite_oficial = 0
        self.parametros_municipio_atual = {}
        self.grupo_principal: str = COL_UNIDADE

    def _check_credentials(self, username, password) -> bool:
        return username == "admin" and password == "admin"

    def _render_login_page(self):
        login_style = """
        <style>
            section[data-testid="stSidebar"] { display: none; }
            header[data-testid="stHeader"] { display: none; }
            .stApp {
                background: linear-gradient(-45deg, #0b0f19, #131a2d, #0f1420, #2a2a79);
                background-size: 400% 400%;
                animation: gradient 15s ease infinite;
            }
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            [data-testid="stAppViewContainer"] > .main .block-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                padding: 2rem;
            }
            .login-box {
                background: rgba(25, 28, 41, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 2.5rem 3rem;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                max-width: 900px;
                width: 100%;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }
            .login-title { font-size: 2.2rem; font-weight: bold; color: white; text-align: left; }
            .login-title span { color: #529DFF; }
            .login-instruction { color: #A0A0A0; margin-bottom: 1.5rem; text-align: left; }
            div[data-baseweb="input"] > div > input {
                background-color: rgba(0,0,0,0.2) !important;
                color: white !important;
                border-radius: 8px !important;
                border: 1px solid #555 !important;
                transition: border-color 0.3s ease;
            }
            div[data-baseweb="input"] > div > input:focus {
                border-color: #529DFF !important;
                box-shadow: none !important;
            }
            div.stButton > button {
                width: 100%;
                background: linear-gradient(90deg, #2A79E2, #529DFF);
                color: white;
                border: none;
                border-radius: 8px;
                height: 48px;
                margin-top: 1.5rem;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            div.stButton > button:hover {
                transform: scale(1.02);
                box-shadow: 0px 5px 15px rgba(82, 157, 255, 0.4);
            }
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
            }
        </style>"""
        st.markdown(login_style, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([1.3, 1])
            with col1:
                st.markdown('<p class="login-title">Plataforma de Gestão <span>APS</span></p>', unsafe_allow_html=True)
                st.markdown('<p class="login-instruction">Bem-vindo(a). Por favor, insira suas credenciais.</p>', unsafe_allow_html=True)
                with st.form("login_form"):
                    username = st.text_input("Usuário", key="username_input", label_visibility="collapsed", placeholder="Usuário")
                    password = st.text_input("Senha", type="password", key="password_input", label_visibility="collapsed", placeholder="Senha")
                    submitted = st.form_submit_button("Acessar Plataforma")
                    if submitted:
                        if self._check_credentials(username, password):
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
            with col2:
                st.markdown('<div class="logo-container">', unsafe_allow_html=True)
                try:
                    st.image('istp-v-blue.png', width=250)
                except Exception:
                    st.info("Espaço reservado para a logo.")
                    st.warning("Para exibir uma imagem, coloque o arquivo 'istp-v-blue.png' na mesma pasta do script.", icon="⚠️")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    @st.cache_data
    def _ler_planilha_cidadaos(file):
        try:
            df = pd.read_excel(io.BytesIO(file.getvalue()), sheet_name='DETALHADO')
            df.columns = df.columns.str.strip()
            req = [COL_STATUS_DOC, COL_TEMPO_SEM_ATUALIZAR, COL_UNIDADE, COL_NOME_EQUIPE, COL_INE, COL_CIDADAO]
            if not all(c in df.columns for c in req): return None
            df = df[req].dropna(subset=[COL_UNIDADE, COL_NOME_EQUIPE, COL_INE, COL_CIDADAO])
            df[COL_TEMPO_SEM_ATUALIZAR] = df[COL_TEMPO_SEM_ATUALIZAR].str.upper()
            df[COL_STATUS_DOC] = df[COL_STATUS_DOC].str.upper()
            df[COL_INE] = df[COL_INE].astype(str).str.strip()
            df[COL_EQUIPE_COMPLETA] = df[COL_NOME_EQUIPE].str.strip() + ' - ' + df[COL_INE]
            return df
        except Exception as e:
            st.error(f"Erro ao ler planilha de cidadãos: {e}")
            return None

    @staticmethod
    @st.cache_data
    def _ler_planilha_domicilios(file):
        try:
            df = pd.read_excel(io.BytesIO(file.getvalue()), sheet_name='DETALHADO')
            df.columns = df.columns.str.strip()
            req = [DOM_COL_UNIDADE, 'INE', COL_TEMPO_SEM_ATUALIZAR, COL_FAMILIA_VINCULADA]
            if not all(c in df.columns for c in req): return None
            df['INE'] = df['INE'].astype(str)
            df['ESTABELECIMENTO_COMPLETO'] = df[DOM_COL_UNIDADE] + ' - ' + df['INE']
            return df[['ESTABELECIMENTO_COMPLETO', COL_TEMPO_SEM_ATUALIZAR, COL_FAMILIA_VINCULADA]].copy()
        except Exception: return None

    @staticmethod
    @st.cache_data
    def _ler_planilha_produtividade(file):
        try:
            df = pd.read_excel(io.BytesIO(file.getvalue()))
            df.columns = df.columns.str.strip()
            if 'DATA' in df.columns: df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            return df
        except Exception: return None

    def _processar_uploads(self, files: List[any]):
        cid_list, dom_list, prod_list = [], [], []
        for f in files:
            df_cid = self._ler_planilha_cidadaos(f)
            if df_cid is not None: cid_list.append(df_cid); continue
            df_dom = self._ler_planilha_domicilios(f)
            if df_dom is not None: dom_list.append(df_dom); continue
            df_prod = self._ler_planilha_produtividade(f)
            if df_prod is not None and 'EQUIPE' in df_prod.columns: prod_list.append(df_prod)
        if cid_list: self.df_cid_bruto = pd.concat(cid_list, ignore_index=True)
        if dom_list: self.df_dom_bruto = pd.concat(dom_list, ignore_index=True)
        if prod_list: self.df_prod_bruto = pd.concat(prod_list, ignore_index=True)
    
    def _get_parametros_por_ine(self, ine: str) -> dict:
        """Busca os parâmetros de uma equipe pelo seu INE. Retorna os parâmetros de ESF como padrão."""
        eap_map = self.parametros_municipio_atual.get('EAP_POR_INE', {})
        
        if ine in eap_map:
            return eap_map[ine]
        
        return {
            'tipo': 'ESF',
            'parametro': self.parametro_oficial,
            'limite_maximo': self.limite_oficial
        }

    def _calcular_vinculos(self) -> pd.DataFrame:
        """Calcula vínculos, identifica tipo de equipe via INE e formata os dados."""
        vinculos_df = self.df_cid_filtrado.groupby([COL_UNIDADE, COL_EQUIPE_COMPLETA])[COL_CIDADAO].count().reset_index()
        vinculos_df.columns = ['Unidade de Saúde', 'Equipe Original', 'Nº de Pessoas Vinculadas']
        
        vinculos_df['INE'] = vinculos_df['Equipe Original'].str.split(' - ').str[-1].str.strip()
        
        params_series = vinculos_df['INE'].apply(self._get_parametros_por_ine)
        params_df = pd.json_normalize(params_series)
        vinculos_df = vinculos_df.join(params_df)
        
        vinculos_df.rename(columns={
            'tipo': 'Tipo de Equipe',
            'parametro': 'Parametro_Equipe',
            'limite_maximo': 'Limite_Equipe'
        }, inplace=True)

        def get_status(row) -> str:
            if row['Nº de Pessoas Vinculadas'] > row['Limite_Equipe']: return '🚨 ACIMA DO LIMITE MÁXIMO'
            if row['Nº de Pessoas Vinculadas'] > row['Parametro_Equipe']: return '⚠️ Acima do Parâmetro'
            return '✅ Dentro do Parâmetro'
        
        vinculos_df['Status'] = vinculos_df.apply(get_status, axis=1)

        def formatar_nome_exibicao(row):
            tipo_sigla = f"EAP {row['Tipo de Equipe']}" if str(row['Tipo de Equipe']) in ['20', '30'] else 'ESF'
            return f"{tipo_sigla} - {row['Unidade de Saúde']} - {row['INE']}"
        
        vinculos_df['Equipe'] = vinculos_df.apply(formatar_nome_exibicao, axis=1)

        return vinculos_df.sort_values('Nº de Pessoas Vinculadas', ascending=False)

    def _preparar_dados_para_analise(self):
        if self.df_cid_bruto is not None:
            self.df_cid_filtrado = self.df_cid_bruto if self.unidade_selecionada == 'Todas' else self.df_cid_bruto.query(f"`{COL_UNIDADE}` == @self.unidade_selecionada")
            self.grupo_principal = COL_UNIDADE if self.unidade_selecionada == 'Todas' else 'Equipe'
            self.df_vinculos = self._calcular_vinculos()
        if self.df_dom_bruto is not None: self.df_dom_filtrado = self.df_dom_bruto.copy()
        if self.df_prod_bruto is not None:
            if self.periodo_selecionado and len(self.periodo_selecionado) == 2:
                df_temp = self.df_prod_bruto.dropna(subset=['DATA'])
                mask = (df_temp['DATA'].dt.date >= self.periodo_selecionado[0]) & (df_temp['DATA'].dt.date <= self.periodo_selecionado[1])
                self.df_prod_filtrado = df_temp[mask]
            else: self.df_prod_filtrado = self.df_prod_bruto.copy()
            
    def _gerar_grafico_barras_crosstab(self, df: pd.DataFrame, grupo: str, col_categorica: str, ordem: List[str]):
        if grupo not in df.columns:
            st.warning(f"A coluna de agrupamento '{grupo}' não foi encontrada para o gráfico.")
            return None, None
        tab = pd.crosstab(index=df[grupo], columns=df[col_categorica])
        for cat in ordem:
            if cat not in tab.columns: tab[cat] = 0
        tab = tab[ordem]
        tab['Total'] = tab.sum(axis=1)
        tab = tab.sort_values('Total', ascending=False)
        perc_df = tab.drop(columns='Total').div(tab['Total'], axis=0).fillna(0) * 100
        melted_df = perc_df.reset_index().melt(id_vars=grupo, var_name=col_categorica, value_name='Percentual')
        fig = px.bar(melted_df, y=grupo, x='Percentual', color=col_categorica, orientation='h', text=melted_df['Percentual'].map(lambda x: f"{x:.1f}%"), category_orders={col_categorica: ordem})
        fig.update_layout(height=max(400, len(perc_df) * 45), yaxis={'categoryorder': 'total ascending'}, legend_title_text=col_categorica, xaxis_title="Percentual (%)")
        return fig, tab

    def render_controls(self):
        """Renderiza o painel de controles expansível no topo da página."""
        with st.expander("🕹️ Controles de Análise e Filtros", expanded=True):
            files = st.file_uploader(
                "1. Envie suas planilhas (.xlsx)", type=["xlsx"], accept_multiple_files=True,
                help="Pode enviar relatórios de Cidadãos, Domicílios e Produtividade juntos."
            )

            if st.button("Sair / Logout", use_container_width=True, type="primary"):
                st.session_state.logged_in = False
                st.session_state.view = "menu"
                st.rerun()

            if not files:
                st.info("Aguardando o envio de arquivos para iniciar a análise.")
                return

            self._processar_uploads(files)

            if self.df_cid_bruto is None and self.df_dom_bruto is None and self.df_prod_bruto is None:
                st.error("Nenhuma planilha válida foi reconhecida. Verifique o formato e as colunas dos arquivos.")
                return

            municipios = sorted(self.df_parametros['MUNICIPIO'].unique())
            map_norm = {_normalize_text(m): m for m in municipios}
            
            municipio_inferido = next((map_norm[token] for f in files if (token := _normalize_text(os.path.basename(f.name).split('_')[0])) in map_norm), None)
            self.municipio_selecionado = municipio_inferido or municipios[0]
            st.query_params["municipio"] = self.municipio_selecionado
            
            pars = self.df_parametros.query("MUNICIPIO == @self.municipio_selecionado").iloc[0]
            self.parametros_municipio_atual = pars.to_dict()
            self.parametro_oficial, self.limite_oficial = pars['PARAMETRO_ESF'], pars['LIMITE_ESF']
            
            st.markdown(f"**Município:** `{self.municipio_selecionado}`")
            st.info(f"Parâmetro Padrão ESF: {self.parametro_oficial} | Limite Padrão ESF: {self.limite_oficial}")
            st.markdown("---")
            
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                if self.df_cid_bruto is not None:
                    unidades = ['Todas'] + sorted(self.df_cid_bruto[COL_UNIDADE].unique())
                    self.unidade_selecionada = st.selectbox("2. Filtrar por Unidade", unidades)
            
            with filter_col2:
                if self.df_prod_bruto is not None and 'DATA' in self.df_prod_bruto.columns:
                    df_data = self.df_prod_bruto.dropna(subset=['DATA'])
                    if not df_data.empty:
                        min_date, max_date = df_data['DATA'].min().date(), df_data['DATA'].max().date()
                        self.periodo_selecionado = st.date_input("3. Filtrar Período (Produção)", (min_date, max_date))

    def _render_aba_resumo(self):
        st.subheader("⭐ Painel Gerencial de Indicadores")
        if self.df_vinculos is None: 
            st.info("Envie uma planilha de cidadãos para visualizar este painel.")
            return

        st.markdown("##### 📊 Visão Geral")
        total_cidadaos = self.df_cid_filtrado[COL_CIDADAO].nunique()
        total_equipes = self.df_vinculos['Equipe Original'].nunique()
        acima_limite = self.df_vinculos[self.df_vinculos['Status'] == '🚨 ACIMA DO LIMITE MÁXIMO'].shape[0]

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total de Cidadãos", f"{total_cidadaos:,}".replace(",", "."))
        kpi2.metric("Total de Equipes", f"{total_equipes}")
        kpi3.metric("Média Cidadãos/Equipe", f"{total_cidadaos / total_equipes if total_equipes > 0 else 0:,.1f}".replace(",", "."))
        kpi4.metric("Equipes Críticas (Acima do Limite)", f"{acima_limite}", delta=f"{acima_limite / total_equipes if total_equipes > 0 else 0:.1%}", delta_color="inverse")
        st.divider()

        st.markdown("##### 🔍 Qualidade dos Dados Cadastrais")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Situação do CPF**")
            cpf_counts = self.df_cid_filtrado[COL_STATUS_DOC].value_counts()
            fig_cpf = px.pie(cpf_counts, values=cpf_counts.values, names=cpf_counts.index, hole=0.4, title="Cidadãos com e sem CPF")
            fig_cpf.update_traces(textinfo='percent+label', pull=[0.05, 0])
            st.plotly_chart(fig_cpf, use_container_width=True)
        with col2:
            st.markdown("**Atualização Cadastral**")
            tempo_counts = self.df_cid_filtrado[COL_TEMPO_SEM_ATUALIZAR].value_counts().reindex(CONFIG_VISUAL['ordem_tempo'])
            fig_tempo = px.bar(tempo_counts, x=tempo_counts.index, y=tempo_counts.values, text_auto=True, title="Distribuição por Tempo de Atualização")
            fig_tempo.update_layout(yaxis_title="Nº de Cidadãos", xaxis_title="Tempo Sem Atualizar")
            st.plotly_chart(fig_tempo, use_container_width=True)
        st.divider()

        st.markdown("##### 🎯 Pontos de Atenção")
        tab1, tab2 = st.tabs(["Equipes Mais Sobrecarregadas", "Equipes com Cadastros Desatualizados"])
        with tab1:
            top_sobrecarregadas = self.df_vinculos.head(10)
            fig = px.bar(
                top_sobrecarregadas.sort_values('Nº de Pessoas Vinculadas', ascending=True),
                x='Nº de Pessoas Vinculadas', y='Equipe', text='Nº de Pessoas Vinculadas',
                orientation='h', title="Top 10 Equipes com Mais Pessoas Vinculadas"
            )
            fig.add_vline(self.limite_oficial, line_dash="dash", annotation_text="Limite ESF", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            cadastros_desatualizados = self.df_cid_filtrado[self.df_cid_filtrado[COL_TEMPO_SEM_ATUALIZAR].isin(['13 A 24 MESES', 'MAIS DE 2 ANOS'])]
            contagem_desatualizados = cadastros_desatualizados.groupby(COL_EQUIPE_COMPLETA).size().reset_index(name='Nº Desatualizados')
            
            df_merged = pd.merge(self.df_vinculos, contagem_desatualizados, left_on='Equipe Original', right_on=COL_EQUIPE_COMPLETA, how='left').fillna(0)
            df_merged['% Desatualizados'] = (df_merged['Nº Desatualizados'] / df_merged['Nº de Pessoas Vinculadas']) * 100
            
            top_desatualizados = df_merged.sort_values('% Desatualizados', ascending=False).head(10)
            
            fig = px.bar(
                top_desatualizados.sort_values('% Desatualizados', ascending=True),
                x='% Desatualizados', y='Equipe', text=top_desatualizados['% Desatualizados'].map('{:.1f}%'.format),
                orientation='h', title="Top 10 Equipes com Maior % de Cadastros Desatualizados (> 1 ano)"
            )
            st.plotly_chart(fig, use_container_width=True)
        st.divider()
            
        if self.unidade_selecionada == 'Todas':
            st.markdown("##### 🏥 Resumo por Unidade de Saúde")
            resumo_unidades = self.df_vinculos.groupby('Unidade de Saúde').agg(
                N_Equipes=('Equipe Original', 'nunique'),
                N_Cidadaos=('Nº de Pessoas Vinculadas', 'sum')
            ).reset_index()
            resumo_unidades['Media_Cidadaos_Equipe'] = resumo_unidades['N_Cidadaos'] / resumo_unidades['N_Equipes']
            st.dataframe(resumo_unidades.sort_values("N_Cidadaos", ascending=False), use_container_width=True)
        st.divider()

        if self.df_prod_filtrado is not None and not self.df_prod_filtrado.empty:
            st.markdown("##### 🩺 Resumo da Produção")
            total_atendimentos = self.df_prod_filtrado['TOTAL GERAL'].sum()
            profissionais_unicos = self.df_prod_filtrado['PROFISSIONAL'].nunique()

            kpi_prod1, kpi_prod2, kpi_prod3 = st.columns(3)
            kpi_prod1.metric("Total de Atendimentos no Período", f"{int(total_atendimentos):,}".replace(",", "."))
            kpi_prod2.metric("Profissionais Atendendo", profissionais_unicos)
            kpi_prod3.metric("Média de Atendimentos por Profissional", f"{total_atendimentos/profissionais_unicos if profissionais_unicos > 0 else 0:.1f}")
            
            if 'TIPO DE ATENDIMENTO' in self.df_prod_filtrado.columns:
                atend_counts = self.df_prod_filtrado['TIPO DE ATENDIMENTO'].value_counts()
                fig_atend = px.pie(atend_counts, values=atend_counts.values, names=atend_counts.index, title="Distribuição por Tipo de Atendimento")
                st.plotly_chart(fig_atend, use_container_width=True)

    def _render_aba_vinculo(self):
        st.header("Análise de Vínculos por Equipe")
        if self.df_vinculos is None: return
        
        df_vinculos_enriquecido = self.df_vinculos.copy()
        
        df_vinculos_enriquecido['Excedente'] = (df_vinculos_enriquecido['Nº de Pessoas Vinculadas'] - df_vinculos_enriquecido['Limite_Equipe']).clip(lower=0)
        df_vinculos_enriquecido['% Acima do Limite'] = ((df_vinculos_enriquecido['Excedente'] / df_vinculos_enriquecido['Limite_Equipe']) * 100).apply(lambda x: f"{x:.1f}%" if x > 0 else "N/A")
        
        fig = px.bar(
            df_vinculos_enriquecido.sort_values('Nº de Pessoas Vinculadas'),
            x='Nº de Pessoas Vinculadas', y='Equipe',
            color='Status', orientation='h', text='Nº de Pessoas Vinculadas',
            color_discrete_map=CONFIG_VISUAL['cores_status'],
            hover_name='Equipe Original'
        )
        fig.add_vline(self.parametro_oficial, line_dash="dash", annotation_text="Parâmetro ESF", line_color="#FFC107")
        fig.add_vline(self.limite_oficial, line_dash="dash", annotation_text="Limite Máximo ESF", line_color="#DC3545")
        
        fig.update_layout(height=max(400, len(self.df_vinculos) * 28), 
                          title='Distribuição de Pessoas Vinculadas por Equipe', yaxis_title=None,
                          xaxis_title="Nº de Pessoas Vinculadas", legend_title="Status", 
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_traces(textposition='auto')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("##### Tabela de Dados Detalhada")
        cols_to_show = ['Equipe', 'Nº de Pessoas Vinculadas', 'Tipo de Equipe', 'Status', 'Excedente', '% Acima do Limite', 'Unidade de Saúde']
        st.dataframe(df_vinculos_enriquecido[cols_to_show], use_container_width=True, height=400)
        exportar_excel(df_vinculos_enriquecido[cols_to_show], f"analise_vinculos_detalhada_{self.municipio_selecionado}.xlsx")

    def _render_aba_tempo_cid(self):
        st.header("Análise de Tempo de Atualização (Cidadãos)")
        if self.df_cid_filtrado is None: return
        df_para_crosstab = self.df_cid_filtrado.copy()
        grupo = COL_UNIDADE
        if self.unidade_selecionada != 'Todas' and self.df_vinculos is not None:
            mapa_nomes = pd.Series(self.df_vinculos['Equipe'].values, index=self.df_vinculos['Equipe Original']).to_dict()
            df_para_crosstab['Equipe'] = df_para_crosstab[COL_EQUIPE_COMPLETA].map(mapa_nomes)
            grupo = 'Equipe'

        fig, tab = self._gerar_grafico_barras_crosstab(df_para_crosstab, grupo, COL_TEMPO_SEM_ATUALIZAR, CONFIG_VISUAL['ordem_tempo'])
        if fig and tab is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tab, use_container_width=True)
            exportar_excel(tab.reset_index(), f"tempo_atualizacao_cid_{self.municipio_selecionado}.xlsx")

    def _render_aba_cpf(self):
        st.header("Cadastros com/sem CPF")
        if self.df_cid_filtrado is None: return
        df_para_crosstab = self.df_cid_filtrado.copy()
        grupo = COL_UNIDADE
        if self.unidade_selecionada != 'Todas' and self.df_vinculos is not None:
            mapa_nomes = pd.Series(self.df_vinculos['Equipe'].values, index=self.df_vinculos['Equipe Original']).to_dict()
            df_para_crosstab['Equipe'] = df_para_crosstab[COL_EQUIPE_COMPLETA].map(mapa_nomes)
            grupo = 'Equipe'

        fig, tab = self._gerar_grafico_barras_crosstab(df_para_crosstab, grupo, COL_STATUS_DOC, CONFIG_VISUAL['ordem_cpf'])
        if fig and tab is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tab, use_container_width=True)
            exportar_excel(tab.reset_index(), f"cadastros_cpf_{self.municipio_selecionado}.xlsx")

    def _render_aba_domicilios(self):
        st.header("Análise de Tempo de Atualização (🏠 Domicílios)")
        if self.df_dom_filtrado is None: return
        col_filtro = st.selectbox("Filtrar por família vinculada?", ["Todos", "Sim", "Não"])
        df = self.df_dom_filtrado[self.df_dom_filtrado[COL_FAMILIA_VINCULADA].str.upper() == col_filtro.upper()] if col_filtro != "Todos" else self.df_dom_filtrado.copy()
        grupo_dom = 'ESTABELECIMENTO_COMPLETO'
        fig, tab = self._gerar_grafico_barras_crosstab(df, grupo_dom, COL_TEMPO_SEM_ATUALIZAR, CONFIG_VISUAL['ordem_tempo'])
        if fig and tab is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tab, use_container_width=True)
            exportar_excel(tab.reset_index(), f"tempo_atualizacao_dom_{self.municipio_selecionado}.xlsx")

    def _render_aba_familia_vinculada(self):
        st.header("Família Vinculada (🏠 Domicílios)")
        if self.df_dom_filtrado is None: return
        grupo_dom, ordem = 'ESTABELECIMENTO_COMPLETO', list(self.df_dom_filtrado[COL_FAMILIA_VINCULADA].dropna().unique())
        fig, tab = self._gerar_grafico_barras_crosstab(self.df_dom_filtrado, grupo_dom, COL_FAMILIA_VINCULADA, ordem)
        if fig and tab is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tab, use_container_width=True)
            exportar_excel(tab.reset_index(), f"familia_vinculada_{self.municipio_selecionado}.xlsx")
    
    def _render_aba_producao_consolidada(self):
        st.header("Análise de Produção Consolidada")
        if self.df_prod_filtrado is None or self.df_prod_filtrado.empty:
            st.info("Envie uma planilha de produtividade e/ou ajuste o filtro de data para visualizar esta seção.")
            return
        if 'TOTAL GERAL' not in self.df_prod_filtrado.columns:
            st.error("A planilha de produtividade precisa ter uma coluna 'TOTAL GERAL'.")
            return
        
        st.markdown("##### Filtros da Análise")
        df = self.df_prod_filtrado.copy()
        c1, c2, c3 = st.columns(3)
        unidade = c1.selectbox("Unidade de Saúde", ["Todas"] + sorted(df["ESTABELECIMENTO"].dropna().unique()), key="prod_unidade")
        equipe = c2.selectbox("Equipe", ["Todas"] + sorted(df["EQUIPE"].dropna().unique()), key="prod_equipe")
        cargo = c3.selectbox("Cargo (CBO)", ["Todas"] + sorted(df["DESCRIÇÃO DO CBO"].dropna().unique()), key="prod_cbo")
        df_filt = df.copy()
        if unidade != "Todas": df_filt = df_filt[df_filt["ESTABELECIMENTO"] == unidade]
        if equipe != "Todas": df_filt = df_filt[df_filt["EQUIPE"] == equipe]
        if cargo != "Todas": df_filt = df_filt[df_filt["DESCRIÇÃO DO CBO"] == cargo]
        st.markdown("---")
        
        tab_geral, tab_detalhes = st.tabs(["📊 Visão Geral e Rankings", "🏢 Análise Detalhada por Unidade"])
        with tab_geral:
            if df_filt.empty: 
                st.warning("Nenhum dado encontrado para os filtros selecionados.")
                return
            
            total_atendimentos = df_filt['TOTAL GERAL'].sum()
            profissionais_unicos = df_filt['PROFISSIONAL'].nunique()
            media_por_profissional = total_atendimentos / profissionais_unicos if profissionais_unicos > 0 else 0
            top_profissional_series = df_filt.groupby('PROFISSIONAL')['TOTAL GERAL'].sum().nlargest(1)
            top_cargo_series = df_filt.groupby('DESCRIÇÃO DO CBO')['TOTAL GERAL'].sum().nlargest(1)
            
            st.markdown("##### KPIs de Produtividade")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total de Atendimentos", f"{int(total_atendimentos)}")
            kpi2.metric("Média por Profissional", f"{media_por_profissional:.1f}")
            if not top_profissional_series.empty:
                kpi3.metric("🏆 Profissional Destaque", top_profissional_series.index[0], f"{int(top_profissional_series.iloc[0])} atendimentos")
            if not top_cargo_series.empty:
                kpi4.metric("🚀 Cargo Destaque", top_cargo_series.index[0], f"{int(top_cargo_series.iloc[0])} atendimentos")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### Distribuição Hierárquica da Produção")
            df_filt['PROFISSIONAL'] = df_filt['PROFISSIONAL'].fillna('Não Informado')
            fig = px.treemap(df_filt, path=[px.Constant("Total"), 'ESTABELECIMENTO', 'EQUIPE', 'DESCRIÇÃO DO CBO', 'PROFISSIONAL'], values='TOTAL GERAL', color_continuous_scale='Blues', color='TOTAL GERAL', hover_data={'TOTAL GERAL':':.0f'})
            fig.update_traces(hovertemplate='<b>%{label}</b><br>Produção: %{value}<br>Pai: %{parent}<extra></extra>')
            fig.update_layout(margin = dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            col_rank1, col_rank2 = st.columns(2)
            with col_rank1:
                st.markdown("##### 🏆 Top 5 Profissionais Mais Produtivos")
                top_5_profissionais = df_filt.groupby('PROFISSIONAL')['TOTAL GERAL'].sum().nlargest(5).reset_index()
                st.dataframe(top_5_profissionais, use_container_width=True, hide_index=True)
                exportar_excel(top_5_profissionais, "top_5_profissionais.xlsx")
            with col_rank2:
                st.markdown("##### 🚀 Top 5 Equipes Mais Produtivas")
                top_5_equipes = df_filt.groupby('EQUIPE')['TOTAL GERAL'].sum().nlargest(5).reset_index()
                st.dataframe(top_5_equipes, use_container_width=True, hide_index=True)
                exportar_excel(top_5_equipes, "top_5_equipes.xlsx")

        with tab_detalhes:
            st.info("Esta aba contém a visão detalhada de produção para uma análise granular.")
            if df_filt.empty: 
                st.warning("Nenhum dado encontrado para os filtros selecionados.")
                return
            
            for unidade_nome, unidade_df in df_filt.groupby("ESTABELECIMENTO"):
                total_unidade = unidade_df.loc[~unidade_df["DESCRIÇÃO DO CBO"].isin(["AGENTE COMUNITÁRIO DE SAÚDE", "TÉCNICO EM AGENTE COMUNITÁRIO DE SAÚDE"]), "TOTAL GERAL"].sum()
                st.markdown(f"""<div style="width:100%; display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; margin-top:20px; padding: 10px; background-color: #262730; border-radius: 8px;"><div style="font-size:1.2rem; font-weight:bold; color:#fafafa; display:flex; align-items:center;"><span style="font-size:1.3rem; margin-right:10px;">🏥</span> {unidade_nome}</div><div style="font-size: 1.1rem; font-weight: bold; color:#f8f9fa; display: flex; align-items: center;">Total de produção na unidade:<span style="background: #212c23; color: #2ecc71; border-radius: 4px; padding:2px 12px; font-size: 1rem; font-weight: bold; margin-left: 10px;">{int(total_unidade) if pd.notnull(total_unidade) else "-"}</span></div></div>""", unsafe_allow_html=True)
                with st.expander("Ver detalhes da produção desta unidade"):
                    grafico_cbo_empilhado = unidade_df.groupby(["DESCRIÇÃO DO CBO", "EQUIPE"])["TOTAL GERAL"].sum().reset_index()
                    ordem_cbo = grafico_cbo_empilhado.groupby("DESCRIÇÃO DO CBO")["TOTAL GERAL"].sum().sort_values(ascending=False).index.tolist()
                    fig_bar = px.bar(grafico_cbo_empilhado, y="DESCRIÇÃO DO CBO", x="TOTAL GERAL", color="EQUIPE", orientation="h", title="Produção por Cargo (Empilhado por Equipe)", text="TOTAL GERAL")
                    fig_bar.update_layout(barmode="stack", yaxis={'categoryorder':'array', 'categoryarray': ordem_cbo})
                    st.plotly_chart(fig_bar, use_container_width=True)
                    for equipe_nome, equipe_df in unidade_df.groupby("EQUIPE"):
                        st.subheader(f"Equipe: {equipe_nome}")
                        ordem_cbo_equipe = equipe_df.groupby("DESCRIÇÃO DO CBO")["TOTAL GERAL"].sum().sort_values(ascending=False).index.tolist()
                        for cbo_nome in ordem_cbo_equipe:
                            st.markdown(f"**Cargo:** {cbo_nome}")
                            cbo_df = equipe_df[equipe_df["DESCRIÇÃO DO CBO"] == cbo_nome]
                            profs = cbo_df.groupby("PROFISSIONAL")["TOTAL GERAL"].sum().reset_index().sort_values("TOTAL GERAL", ascending=False)
                            st.dataframe(profs, use_container_width=True, hide_index=True)

    def _render_aba_tipo_atendimento_esf(self):
        st.header("Análise Estratégica de Tipos de Atendimento")
        if self.df_prod_filtrado is None or 'TIPO DE ATENDIMENTO' not in self.df_prod_filtrado.columns:
            st.info("Envie uma planilha de produtividade com a coluna 'TIPO DE ATENDIMENTO' e ajuste o filtro de data para visualizar esta seção.")
            return

        df = self.df_prod_filtrado.copy()
        df.rename(columns={'ESTABELECIMENTO': 'Unidade de Saúde'}, inplace=True)
        
        mapa_categorias = {
            'CONSULTA AGENDADA': 'Cuidado Programado',
            'CONSULTA AGENDADA PROGRAMADA / CUIDADO CONTINUADO': 'Cuidado Programado',
            'CONSULTA NO DIA': 'Demanda Espontânea',
            'ATENDIMENTO DE URGÊNCIA': 'Demanda Espontânea',
            'ESCUTA INICIAL / ORIENTAÇÃO': 'Outros'
        }
        df['Categoria Atendimento'] = df['TIPO DE ATENDIMENTO'].map(mapa_categorias)
        
        st.markdown("##### 📊 Visão Geral: Programado vs. Demanda Espontânea")
        total_atendimentos = len(df)
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total de Atendimentos", f"{total_atendimentos:,}".replace(",", "."))
        
        if total_atendimentos > 0:
            categoria_counts = df['Categoria Atendimento'].value_counts()
            programado_perc = categoria_counts.get('Cuidado Programado', 0) / total_atendimentos
            demanda_perc = categoria_counts.get('Demanda Espontânea', 0) / total_atendimentos
            
            kpi2.metric("🗓️ % Cuidado Programado", f"{programado_perc:.1%}")
            kpi3.metric("🏃 % Demanda Espontânea", f"{demanda_perc:.1%}")

            fig_treemap = px.treemap(df.dropna(subset=['Categoria Atendimento', 'TIPO DE ATENDIMENTO']),
                                     path=[px.Constant("Todos Atendimentos"), 'Categoria Atendimento', 'TIPO DE ATENDIMENTO'],
                                     title="Composição dos Atendimentos Realizados no Período")
            fig_treemap.update_traces(root_color="lightgrey")
            fig_treemap.update_layout(margin = dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig_treemap, use_container_width=True)
        st.divider()

        st.markdown("##### 🏥 Análise Estratégica por Unidades de Saúde")
        tab1, tab2, tab3, tab4 = st.tabs(["⭐ Scorecard Gerencial", "📊 Perfil Comparativo", "🔥 Focos de Demanda Espontânea", "🗓️ Destaques em Cuidado Programado"])

        crosstab_unidades = pd.crosstab(df['Unidade de Saúde'], df['Categoria Atendimento'])
        crosstab_unidades.columns.name = None
        crosstab_unidades = crosstab_unidades.reindex(columns=['Cuidado Programado', 'Demanda Espontânea', 'Outros'], fill_value=0)

        with tab1:
            st.markdown("**Classificação de performance das unidades baseada no perfil de atendimento.**")
            scorecard = crosstab_unidades.copy()
            scorecard['Total'] = scorecard.sum(axis=1)
            scorecard['% Programado'] = (scorecard['Cuidado Programado'] / scorecard['Total']) * 100
            scorecard['% Demanda'] = (scorecard['Demanda Espontânea'] / scorecard['Total']) * 100
            scorecard['Índice Eficiência (Prog/Demanda)'] = scorecard['Cuidado Programado'] / scorecard['Demanda Espontânea']

            scorecard_display = scorecard[['% Programado', '% Demanda', 'Índice Eficiência (Prog/Demanda)']].sort_values('Índice Eficiência (Prog/Demanda)', ascending=False).fillna(0)
            
            st.dataframe(scorecard_display.style
                         .background_gradient(cmap='Greens', subset=['% Programado', 'Índice Eficiência (Prog/Demanda)'])
                         .background_gradient(cmap='Reds_r', subset=['% Demanda'])
                         .format("{:.1f}%", subset=['% Programado', '% Demanda'])
                         .format("{:.2f}", subset=['Índice Eficiência (Prog/Demanda)']),
                         use_container_width=True)

        with tab2:
            st.markdown("**Como cada Unidade de Saúde distribui seus atendimentos?**")
            tabela_perc = (crosstab_unidades.div(crosstab_unidades.sum(axis=1), axis=0) * 100).fillna(0)
            tabela_perc = tabela_perc.sort_values('Cuidado Programado', ascending=True)
            
            fig_comp = px.bar(tabela_perc, x=tabela_perc.index, y=['Cuidado Programado', 'Demanda Espontânea', 'Outros'],
                              title="Perfil de Atendimento por Unidade de Saúde (%)",
                              labels={'x': '', 'value': 'Percentual de Atendimentos (%)'},
                              text_auto='.1f', barmode='stack', height=max(400, len(tabela_perc)*25))
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Insights Automáticos
            best_unit_programado = tabela_perc.idxmax()['Cuidado Programado']
            worst_unit_programado = tabela_perc.idxmin()['Cuidado Programado']
            st.success(f"**🏆 Destaque em Cuidado Programado:** A unidade **{best_unit_programado}** apresenta o maior percentual de atendimentos planejados ({tabela_perc.loc[best_unit_programado, 'Cuidado Programado']:.1f}%).")
            st.warning(f"**⚠️ Ponto de Atenção:** A unidade **{worst_unit_programado}** possui o maior foco em Demanda Espontânea ({tabela_perc.loc[worst_unit_programado, 'Demanda Espontânea']:.1f}%).")

        with tab3:
            st.markdown("**Quais unidades estão sob maior pressão de atendimentos não planejados?**")
            df_demanda = df[df['Categoria Atendimento'] == 'Demanda Espontânea']
            tabela_demanda = pd.crosstab(df_demanda['Unidade de Saúde'], df_demanda['TIPO DE ATENDIMENTO'])
            tabela_demanda = tabela_demanda.sort_values(['ATENDIMENTO DE URGÊNCIA', 'CONSULTA NO DIA'], ascending=False).head(15)
            
            fig_demanda = px.bar(tabela_demanda, y=tabela_demanda.index, x=['ATENDIMENTO DE URGÊNCIA', 'CONSULTA NO DIA'],
                                title="Top 15 Unidades por Volume de Demanda Espontânea", barmode='group', text_auto=True, orientation='h')
            fig_demanda.update_layout(yaxis={'categoryorder':'total ascending'}, height=max(400, len(tabela_demanda)*40))
            st.plotly_chart(fig_demanda, use_container_width=True)

        with tab4:
            st.markdown("**Quais unidades se destacam no cuidado continuado e agendado?**")
            df_programado = df[df['Categoria Atendimento'] == 'Cuidado Programado']
            tabela_programado = pd.crosstab(df_programado['Unidade de Saúde'], df_programado['TIPO DE ATENDIMENTO'])
            tabela_programado['Total Programado'] = tabela_programado.sum(axis=1)
            tabela_programado = tabela_programado.sort_values('Total Programado', ascending=False).head(15)
            
            fig_programado = px.bar(tabela_programado.drop(columns='Total Programado'), y=tabela_programado.index, x=['CONSULTA AGENDADA', 'CONSULTA AGENDADA PROGRAMADA / CUIDADO CONTINUADO'],
                                    title="Top 15 Unidades por Volume de Cuidado Programado", barmode='stack', text_auto=True, orientation='h')
            fig_programado.update_layout(yaxis={'categoryorder':'total ascending'}, height=max(400, len(tabela_programado)*40))
            st.plotly_chart(fig_programado, use_container_width=True)

        with st.expander("Clique para ver a tabela detalhada de atendimentos"):
            tabela_final = pd.crosstab(df['Unidade de Saúde'], df['TIPO DE ATENDIMENTO'])
            tabela_final["Total Geral"] = tabela_final.sum(axis=1)
            st.dataframe(tabela_final.sort_values("Total Geral", ascending=False), use_container_width=True)
            exportar_excel(tabela_final.reset_index(), f"tipo_atendimento_{self.municipio_selecionado}.xlsx")


    def _render_aba_tipos_consultas_esb(self):
        st.header("Tipos de Consultas ESB")
        if self.df_prod_filtrado is None: st.info("Envie uma planilha de produtividade para esta análise."); return
        col_tipo_consulta = next((c for c in self.df_prod_filtrado.columns if _normalize_text(c) == "TIPO DE CONSULTA"), None)
        if not col_tipo_consulta: st.warning("Coluna 'TIPO DE CONSULTA' não encontrada na planilha."); return
        df, categorias = self.df_prod_filtrado, ["Consulta de manutenção em odontologia", "Consulta de retorno em odontologia", "Não informado", "Primeira consulta odontológica programática "]
        tabela = pd.pivot_table(df, values="PROFISSIONAL", index=["ESTABELECIMENTO"], columns=[col_tipo_consulta], aggfunc="count", fill_value=0)
        for cat in categorias:
            if cat not in tabela.columns: tabela[cat] = 0
        tabela = tabela[categorias]
        tabela["Total Unidade"] = tabela.sum(axis=1)
        total_geral = tabela[categorias].sum().to_frame().T
        total_geral.index, total_geral["Total Unidade"] = ["Total Geral"], total_geral.sum(axis=1)
        tabela_final = pd.concat([tabela, total_geral])
        st.dataframe(tabela_final, use_container_width=True)
        exportar_excel(tabela_final.reset_index(), f"consultas_esb_{self.municipio_selecionado}.xlsx")

    def _render_menu_page(self):
        menu_style = """
        <style>
            .main-title { text-align: center; font-size: 2.5rem; font-weight: bold; color: white; margin-bottom: 2rem; }
            .main-title span { color: #2A79E2; }
            .menu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            div.stButton > button { background-color: #262730; border: 1px solid #333; border-radius: 12px; color: #FAFAFA; font-size: 1rem; font-weight: bold; height: 120px; width: 100%; transition: all 0.2s ease-in-out; }
            div.stButton > button:hover { border-color: #2A79E2; color: #2A79E2; background-color: #2D2E37; }
        </style>"""
        st.markdown(menu_style, unsafe_allow_html=True)
        st.markdown('<p class="main-title">PRINCIPAIS <span>RELATÓRIOS</span></p>', unsafe_allow_html=True)
        reports = []
        if self.df_cid_bruto is not None: reports.extend([("⭐ Painel Resumo", "resumo"), ("📈 Vínculo", "vinculo"), ("⏳ Atualização", "tempo_cid"), ("📇 CPF", "cpf")])
        if self.df_dom_bruto is not None: reports.extend([("🏠 Domicílios", "domicilios"), ("🏘️ Família Vinculada", "familia_vinculada")])
        if self.df_prod_bruto is not None: reports.extend([("📊 Produção Consolidada", "producao"), ("📑 Tipo de Atendimento ESF", "tipo_atendimento"), ("🦷 Tipos de Consultas ESB", "consultas_esb")])
        if not reports: return
        cols = st.columns(3)
        for i, (label, view_name) in enumerate(reports):
            if cols[i % 3].button(label, key=f"btn_{view_name}", use_container_width=True):
                st.session_state.view = view_name
                st.rerun()

    def render_dashboard_content(self):
        view = st.session_state.get("view", "menu")
        if view != "menu" and st.button("⬅️ Voltar ao Menu Principal"):
            st.session_state.view = "menu"
            st.rerun()

        view_map = {
            "menu": self._render_menu_page,
            "resumo": self._render_aba_resumo, "vinculo": self._render_aba_vinculo,
            "tempo_cid": self._render_aba_tempo_cid, "cpf": self._render_aba_cpf,
            "domicilios": self._render_aba_domicilios, "familia_vinculada": self._render_aba_familia_vinculada,
            "producao": self._render_aba_producao_consolidada, "tipo_atendimento": self._render_aba_tipo_atendimento_esf,
            "consultas_esb": self._render_aba_tipos_consultas_esb,
        }
        render_function = view_map.get(view, lambda: st.error("Página não encontrada."))
        render_function()

    def run(self):
        """Método principal que executa o aplicativo."""
        if not st.session_state.get("logged_in"):
            self._render_login_page()
        else:
            st.markdown("<style> section[data-testid='stSidebar'] {display: none;} </style>", unsafe_allow_html=True)
            
            st.title(f"Gestão APS | {self.municipio_selecionado or 'Sem município'}")
            
            self.render_controls()
            
            has_data = self.df_cid_bruto is not None or self.df_dom_bruto is not None or self.df_prod_bruto is not None
            if has_data:
                self._preparar_dados_para_analise()
                self.render_dashboard_content()
            else:
                st.info("⬆️ **Bem-vindo(a)!** Por favor, envie uma ou mais planilhas no painel de controles acima para iniciar a análise.")

if __name__ == "__main__":
    app = DashboardAPS()
    app.run()