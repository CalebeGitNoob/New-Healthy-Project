import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import date, datetime

# =====================================================
# CONFIGURAÇÃO GERAL DO APP
# =====================================================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Cores usadas no design original
BG = "#F7F4EE"
CARD = "#FFFFFF"
TEXT = "#2D2925"
GREEN = "#648B6A"
GRAY = "#9B9388"
BORDER = "#E5DED4"
VERMELHO = "#B3564B"
AMARELO = "#C9A227"

ARQUIVO_DADOS = "dados_nutri.json"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

NIVEIS_ATIVIDADE = {
    "Sedentário (pouco ou nenhum exercício)": 1.2,
    "Leve (exercício 1 a 3x/semana)": 1.375,
    "Moderado (exercício 3 a 5x/semana)": 1.55,
    "Intenso (exercício 6 a 7x/semana)": 1.725,
    "Muito intenso (exercício diário + trabalho físico)": 1.9,
}

OBJETIVOS = {
    "Perder peso": -500,
    "Manter peso": 0,
    "Ganhar peso": 500,
}

# Estrutura de dados de UMA conta (um usuário)
CONTA_PADRAO = {
    "perfil": None,
    "refeicoes": {},        # "AAAA-MM-DD" -> [ {id, nome, calorias, horario}, ... ]
    "pesos": [],             # [ {data, peso}, ... ] ordenado por data crescente
    "proximo_id_refeicao": 1,
}

# Estrutura do arquivo inteiro: pode conter várias contas
DADOS_PADRAO = {
    "contas": {},            # "id_da_conta" -> CONTA_PADRAO
    "conta_ativa": None,     # id da conta atualmente logada (ou None se deslogado)
    "proximo_id_conta": 1,
}


# =====================================================
# 1. REGRA DE NEGÓCIO (Lógica de Dados)
# =====================================================
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return json.loads(json.dumps(DADOS_PADRAO))
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DADOS_PADRAO))

    # Garante que todas as chaves existam (compatibilidade com versões antigas)
    for chave, valor in DADOS_PADRAO.items():
        if chave not in dados:
            dados[chave] = json.loads(json.dumps(valor))

    # Garante que cada conta tenha todas as chaves esperadas
    for conta in dados["contas"].values():
        for chave, valor in CONTA_PADRAO.items():
            if chave not in conta:
                conta[chave] = json.loads(json.dumps(valor))

    return dados


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def chave_data(d: date) -> str:
    return d.isoformat()


def formatar_data_pt(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def formatar_data_curta(d: date) -> str:
    return d.strftime("%d/%m/%Y")


# --- Contas (login / logout / cadastro) ---
def criar_conta(dados):
    """Cria uma nova conta vazia, marca como ativa e retorna seu id."""
    conta_id = str(dados["proximo_id_conta"])
    dados["contas"][conta_id] = json.loads(json.dumps(CONTA_PADRAO))
    dados["proximo_id_conta"] += 1
    dados["conta_ativa"] = conta_id
    salvar_dados(dados)
    return conta_id


def entrar_conta(dados, conta_id):
    dados["conta_ativa"] = conta_id
    salvar_dados(dados)


def sair_conta(dados):
    """Faz logout sem apagar nenhum dado."""
    dados["conta_ativa"] = None
    salvar_dados(dados)


def excluir_conta(dados, conta_id):
    if conta_id in dados["contas"]:
        del dados["contas"][conta_id]
    if dados.get("conta_ativa") == conta_id:
        dados["conta_ativa"] = None
    salvar_dados(dados)


def listar_contas_cadastradas(dados):
    """Retorna [(id, nome), ...] apenas das contas com cadastro completo."""
    return [
        (conta_id, conta["perfil"]["nome"])
        for conta_id, conta in dados["contas"].items()
        if conta.get("perfil")
    ]


# --- Refeições (operam sobre uma conta específica) ---
def adicionar_refeicao(conta, dados, data_str, nome, calorias, horario=None):
    if horario is None:
        horario = datetime.now().strftime("%H:%M")
    lista = conta["refeicoes"].setdefault(data_str, [])
    lista.append({
        "id": conta["proximo_id_refeicao"],
        "nome": nome,
        "calorias": calorias,
        "horario": horario,
    })
    conta["proximo_id_refeicao"] += 1
    salvar_dados(dados)


def excluir_refeicao(conta, dados, data_str, id_refeicao):
    lista = conta["refeicoes"].get(data_str, [])
    conta["refeicoes"][data_str] = [r for r in lista if r["id"] != id_refeicao]
    salvar_dados(dados)


def excluir_todas_refeicoes_do_dia(conta, dados, data_str):
    conta["refeicoes"][data_str] = []
    salvar_dados(dados)


def editar_refeicao(conta, dados, data_str, id_refeicao, nome, calorias):
    lista = conta["refeicoes"].get(data_str, [])
    for r in lista:
        if r["id"] == id_refeicao:
            r["nome"] = nome
            r["calorias"] = calorias
            break
    salvar_dados(dados)


def listar_refeicoes(conta, data_str):
    return conta["refeicoes"].get(data_str, [])


def total_calorias(conta, data_str):
    return sum(r["calorias"] for r in listar_refeicoes(conta, data_str))


# --- Peso (operam sobre uma conta específica) ---
def adicionar_peso(conta, dados, data_str, peso):
    conta["pesos"] = [p for p in conta["pesos"] if p["data"] != data_str]
    conta["pesos"].append({"data": data_str, "peso": peso})
    conta["pesos"].sort(key=lambda p: p["data"])
    if conta["perfil"] is not None:
        conta["perfil"]["peso"] = peso
    salvar_dados(dados)


def excluir_peso(conta, dados, data_str):
    conta["pesos"] = [p for p in conta["pesos"] if p["data"] != data_str]
    salvar_dados(dados)


def peso_atual(conta):
    if conta["pesos"]:
        return conta["pesos"][-1]["peso"]
    if conta["perfil"]:
        return conta["perfil"].get("peso", 0)
    return 0


# --- Cálculos de saúde ---
def calcular_imc(peso, altura_cm):
    altura_m = altura_cm / 100
    if altura_m <= 0:
        return 0
    return peso / (altura_m ** 2)


def classificar_imc(imc):
    if imc < 18.5:
        return "Abaixo do peso", AMARELO
    elif imc < 25:
        return "Peso normal", GREEN
    elif imc < 30:
        return "Sobrepeso", AMARELO
    elif imc < 35:
        return "Obesidade grau I", VERMELHO
    elif imc < 40:
        return "Obesidade grau II", VERMELHO
    return "Obesidade grau III", VERMELHO


def calcular_tmb(peso, altura, idade, sexo):
    """Taxa Metabólica Basal (fórmula de Mifflin-St Jeor)."""
    homem = 10 * peso + 6.25 * altura - 5 * idade + 5
    mulher = 10 * peso + 6.25 * altura - 5 * idade - 161
    if sexo == "Masculino":
        return homem
    elif sexo == "Feminino":
        return mulher
    return (homem + mulher) / 2


def calcular_meta_calorica(perfil):
    tmb = calcular_tmb(perfil["peso"], perfil["altura"], perfil["idade"], perfil["sexo"])
    fator = NIVEIS_ATIVIDADE.get(perfil.get("nivel_atividade"), 1.2)
    tdee = tmb * fator
    ajuste = OBJETIVOS.get(perfil.get("objetivo"), 0)
    meta = tdee + ajuste
    return max(round(meta), 1200)  # nunca sugere menos de 1200 kcal, por segurança


# =====================================================
# 2. INTERFACE GRÁFICA (Visual)
# =====================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meu Nutri")
        self.geometry("390x844")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self.acao_sair_app)

        self.dados = carregar_dados()
        self.conta = None
        self.conta_id = None
        self.data_selecionada = date.today()

        conta_ativa_id = self.dados.get("conta_ativa")
        conta_valida = (
            conta_ativa_id
            and conta_ativa_id in self.dados["contas"]
            and self.dados["contas"][conta_ativa_id].get("perfil")
        )

        if conta_valida:
            self.conta_id = conta_ativa_id
            self.conta = self.dados["contas"][conta_ativa_id]
            self.tela_inicial()
        else:
            self.tela_login()

    # -------------------------------------------------
    # Utilitários de construção de tela
    # -------------------------------------------------
    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    def criar_titulo(self, texto, subtitulo=None, pady_topo=55):
        ctk.CTkLabel(
            self, text=texto, font=("Arial", 24, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack(anchor="w", padx=25, pady=(pady_topo, 8))

        if subtitulo:
            ctk.CTkLabel(
                self, text=subtitulo, font=("Arial", 11), text_color=GRAY,
                fg_color="transparent", wraplength=330, justify="left"
            ).pack(anchor="w", padx=25, pady=(0, 20))

    def criar_barra_topo(self, titulo, mostrar_voltar=False, comando_voltar=None,
                          mostrar_fechar=False, comando_fechar=None, pady_topo=45):
        """Barra superior com título e, opcionalmente, botão de voltar e/ou fechar."""
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=15, pady=(pady_topo, 0))

        if mostrar_voltar:
            ctk.CTkButton(
                barra, text="←", width=36, height=36, fg_color=CARD,
                hover_color="#EFEAE1", text_color=TEXT, corner_radius=8,
                command=comando_voltar
            ).pack(side="left")

        ctk.CTkLabel(
            barra, text=titulo, font=("Arial", 20, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack(side="left", padx=(10 if mostrar_voltar else 10, 10), expand=True, fill="x")

        if mostrar_fechar:
            ctk.CTkButton(
                barra, text="✕", width=36, height=36, fg_color=CARD,
                hover_color="#F3E6E3", text_color=VERMELHO, corner_radius=8,
                command=comando_fechar
            ).pack(side="right")

    def criar_campo(self, texto, variavel, exemplo="", container=None):
        pai = container if container is not None else self
        ctk.CTkLabel(
            pai, text=texto, font=("Arial", 10, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack(anchor="w", padx=25, pady=(8, 6))

        entry = ctk.CTkEntry(
            pai, textvariable=variavel, font=("Arial", 14),
            fg_color=CARD, text_color=TEXT, border_color=BORDER,
            border_width=1, corner_radius=8, height=42
        )
        entry.pack(fill="x", padx=25)

        if exemplo:
            ctk.CTkLabel(
                pai, text=exemplo, font=("Arial", 9),
                text_color=GRAY, fg_color="transparent"
            ).pack(anchor="w", padx=25, pady=(3, 0))

        return entry

    def criar_menu(self, texto, variavel, opcoes, container=None):
        pai = container if container is not None else self
        ctk.CTkLabel(
            pai, text=texto, font=("Arial", 10, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack(anchor="w", padx=25, pady=(14, 6))

        menu = ctk.CTkOptionMenu(
            pai, variable=variavel, values=opcoes,
            fg_color=CARD, button_color=GREEN, button_hover_color=GREEN,
            text_color=TEXT, corner_radius=8, height=42,
            dropdown_fg_color=CARD, dropdown_text_color=TEXT
        )
        menu.pack(fill="x", padx=25)
        return menu

    def criar_botao(self, texto, comando, cor=GREEN, container=None, pady=25):
        pai = container if container is not None else self
        ctk.CTkButton(
            pai, text=texto, command=comando, font=("Arial", 12, "bold"),
            fg_color=cor, hover_color=cor, text_color="white",
            corner_radius=8, height=44
        ).pack(fill="x", padx=25, pady=pady)

    def criar_botao_secundario(self, texto, comando, container=None, pady=(0, 25)):
        """Botão de contorno, usado para ações secundárias como 'Cancelar'."""
        pai = container if container is not None else self
        ctk.CTkButton(
            pai, text=texto, command=comando, font=("Arial", 12, "bold"),
            fg_color="transparent", hover_color="#EFEAE1", text_color=TEXT,
            border_color=BORDER, border_width=1,
            corner_radius=8, height=44
        ).pack(fill="x", padx=25, pady=pady)

    def criar_nav(self):
        nav = ctk.CTkFrame(self, fg_color=CARD, height=70, corner_radius=0)
        nav.pack(side="bottom", fill="x")

        botoes = [
            ("Início", "🏠", self.tela_inicial),
            ("Refeições", "🍽", self.tela_refeicoes),
            ("Peso", "⚖", self.tela_peso),
            ("Perfil", "👤", self.tela_perfil),
        ]
        for texto, icone, comando in botoes:
            ctk.CTkButton(
                nav, text=f"{icone}\n{texto}", font=("Arial", 9), fg_color=CARD,
                hover_color="#EFEAE1", text_color=TEXT, corner_radius=0,
                command=comando
            ).pack(side="left", expand=True, fill="y", pady=6)

    def saudacao(self):
        hora = datetime.now().hour
        if hora < 12:
            return "Bom dia"
        elif hora < 18:
            return "Boa tarde"
        return "Boa noite"

    def acao_sair_app(self):
        resposta = messagebox.askyesno("Sair", "Deseja realmente fechar o Meu Nutri?")
        if resposta:
            self.destroy()

    # -------------------------------------------------
    # TELA 0 - LOGIN / SELEÇÃO DE CONTA
    # -------------------------------------------------
    def tela_login(self):
        self.limpar_tela()
        contas = listar_contas_cadastradas(self.dados)

        ctk.CTkLabel(
            self, text="🌿", font=("Arial", 42), text_color=GREEN,
            fg_color="transparent"
        ).pack(pady=(70 if not contas else 55, 10))

        ctk.CTkLabel(
            self, text="Meu Nutri", font=("Arial", 30, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack()

        if contas:
            ctk.CTkLabel(
                self, text="Escolha uma conta para entrar", font=("Arial", 12),
                text_color=GRAY, fg_color="transparent"
            ).pack(pady=(10, 20))

            scroll = ctk.CTkScrollableFrame(
                self, fg_color="transparent", scrollbar_button_color=BORDER,
                scrollbar_button_hover_color=GRAY
            )
            scroll.pack(fill="both", expand=True, padx=20)

            for conta_id, nome in contas:
                linha = ctk.CTkFrame(scroll, fg_color=CARD, border_color=BORDER,
                                      border_width=1, corner_radius=10)
                linha.pack(fill="x", pady=5)

                ctk.CTkButton(
                    linha, text=f"👤  {nome}", font=("Arial", 13), fg_color="transparent",
                    hover_color="#EFEAE1", text_color=TEXT, anchor="w",
                    command=lambda cid=conta_id: self.acao_entrar_conta(cid)
                ).pack(side="left", fill="both", expand=True, padx=(6, 0), pady=12)

                ctk.CTkButton(
                    linha, text="🗑", width=32, height=28, fg_color="transparent",
                    hover_color="#F3E6E3", text_color=VERMELHO, corner_radius=6,
                    command=lambda cid=conta_id, n=nome: self.acao_excluir_conta_login(cid, n)
                ).pack(side="right", padx=8)

            self.criar_botao("+ Criar nova conta", self.tela_boas_vindas, pady=(15, 25))
        else:
            ctk.CTkLabel(
                self, text="Vamos criar sua conta.", font=("Arial", 12),
                text_color=GRAY, fg_color="transparent"
            ).pack(pady=(10, 45))
            self.criar_botao("Criar minha conta", self.tela_boas_vindas)

    def acao_entrar_conta(self, conta_id):
        entrar_conta(self.dados, conta_id)
        self.conta_id = conta_id
        self.conta = self.dados["contas"][conta_id]
        self.tela_inicial()

    def acao_excluir_conta_login(self, conta_id, nome):
        resposta = messagebox.askyesno(
            "Excluir conta",
            f"Deseja excluir permanentemente a conta de {nome}?\n"
            "Todos os dados dela (refeições e histórico de peso) serão apagados."
        )
        if not resposta:
            return
        excluir_conta(self.dados, conta_id)
        self.tela_login()

    # -------------------------------------------------
    # TELA 1 - BOAS VINDAS (nome da nova conta)
    # -------------------------------------------------
    def tela_boas_vindas(self):
        self.limpar_tela()
        tem_contas = bool(listar_contas_cadastradas(self.dados))

        if tem_contas:
            self.criar_barra_topo("Nova conta", mostrar_voltar=True,
                                   comando_voltar=self.tela_login, pady_topo=45)
            pady_logo = (15, 10)
        else:
            pady_logo = (70, 10)

        ctk.CTkLabel(
            self, text="🌿", font=("Arial", 42), text_color=GREEN,
            fg_color="transparent"
        ).pack(pady=pady_logo)

        ctk.CTkLabel(
            self, text="Meu Nutri", font=("Arial", 30, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack()

        ctk.CTkLabel(
            self, text="Vamos personalizar sua experiência.", font=("Arial", 12),
            text_color=GRAY, fg_color="transparent"
        ).pack(pady=(10, 45))

        self.nome_var = ctk.StringVar()
        self.criar_campo("Como podemos chamar você?", self.nome_var, "Digite seu primeiro nome")
        self.criar_botao("Continuar", self.salvar_nome)

    def salvar_nome(self):
        nome = self.nome_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Digite seu nome para continuar.")
            return
        self._nome_temp = nome
        self.conta_id = criar_conta(self.dados)
        self.conta = self.dados["contas"][self.conta_id]
        self.tela_dados()

    # -------------------------------------------------
    # TELA 2 - DADOS DO USUÁRIO (cadastro inicial e edição)
    # -------------------------------------------------
    def tela_dados(self, editando=False):
        self.limpar_tela()
        perfil = self.conta["perfil"]
        nome = perfil["nome"] if editando and perfil else getattr(self, "_nome_temp", "")

        if editando:
            self.criar_barra_topo("Editar dados", mostrar_voltar=True,
                                   comando_voltar=self.tela_perfil, pady_topo=45)
        else:
            self.criar_barra_topo(f"Olá, {nome}! 👋", mostrar_voltar=False, pady_topo=45)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                         scrollbar_button_color=BORDER,
                                         scrollbar_button_hover_color=GRAY)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Precisamos de alguns dados para calcular sua meta calórica e IMC.",
            font=("Arial", 11), text_color=GRAY, fg_color="transparent",
            wraplength=330, justify="left"
        ).pack(anchor="w", padx=25, pady=(10, 15))

        self.peso_var = ctk.StringVar(value=str(perfil["peso"]).replace(".", ",") if editando and perfil else "")
        self.altura_var = ctk.StringVar(value=str(perfil["altura"]) if editando and perfil else "")
        self.idade_var = ctk.StringVar(value=str(perfil["idade"]) if editando and perfil else "")
        self.sexo_var = ctk.StringVar(value=perfil["sexo"] if editando and perfil else "Selecione")
        self.nivel_var = ctk.StringVar(
            value=perfil.get("nivel_atividade") if editando and perfil else "Selecione"
        )
        self.objetivo_var = ctk.StringVar(
            value=perfil.get("objetivo") if editando and perfil else "Selecione"
        )

        self.criar_campo("Peso (kg)", self.peso_var, "Ex.: 77,5", container=scroll)
        self.criar_campo("Altura (cm)", self.altura_var, "Ex.: 175", container=scroll)
        self.criar_campo("Idade", self.idade_var, "Ex.: 25", container=scroll)
        self.criar_menu("Sexo", self.sexo_var,
                         ["Selecione", "Feminino", "Masculino", "Outro", "Prefiro não informar"],
                         container=scroll)
        self.criar_menu("Nível de atividade física", self.nivel_var,
                         ["Selecione"] + list(NIVEIS_ATIVIDADE.keys()), container=scroll)
        self.criar_menu("Objetivo", self.objetivo_var,
                         ["Selecione"] + list(OBJETIVOS.keys()), container=scroll)

        self.criar_botao(
            "Salvar" if editando else "Começar",
            lambda: self.salvar_dados(editando), container=scroll, pady=(25, 10)
        )

        if editando:
            self.criar_botao_secundario("Cancelar", self.tela_perfil, container=scroll)

    def salvar_dados(self, editando=False):
        peso_txt = self.peso_var.get().strip().replace(",", ".")
        altura_txt = self.altura_var.get().strip().replace(",", ".")
        idade_txt = self.idade_var.get().strip()
        sexo = self.sexo_var.get()
        nivel = self.nivel_var.get()
        objetivo = self.objetivo_var.get()

        try:
            peso_num = float(peso_txt)
            altura_num = float(altura_txt)
            idade_num = int(idade_txt)
            if peso_num <= 0 or altura_num <= 0 or idade_num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Dados inválidos", "Confira peso, altura e idade e tente novamente.")
            return

        if sexo == "Selecione" or nivel == "Selecione" or objetivo == "Selecione":
            messagebox.showwarning("Atenção", "Preencha sexo, nível de atividade e objetivo.")
            return

        nome = self.conta["perfil"]["nome"] if editando and self.conta["perfil"] else self._nome_temp

        self.conta["perfil"] = {
            "nome": nome,
            "peso": peso_num,
            "altura": altura_num,
            "idade": idade_num,
            "sexo": sexo,
            "nivel_atividade": nivel,
            "objetivo": objetivo,
        }

        hoje = chave_data(date.today())
        ja_tem_peso_hoje = any(p["data"] == hoje for p in self.conta["pesos"])
        if not ja_tem_peso_hoje:
            adicionar_peso(self.conta, self.dados, hoje, peso_num)
        else:
            salvar_dados(self.dados)

        messagebox.showinfo("Tudo certo!", "Seus dados foram salvos.")
        self.tela_inicial()

    # -------------------------------------------------
    # TELA 3 - INICIAL
    # -------------------------------------------------
    def tela_inicial(self):
        self.limpar_tela()
        perfil = self.conta["perfil"]
        hoje_str = chave_data(date.today())

        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=GRAY)
        corpo.pack(fill="both", expand=True, pady=(0, 0))

        topo = ctk.CTkFrame(corpo, fg_color="transparent")
        topo.pack(fill="x", padx=25, pady=(30, 5))

        ctk.CTkLabel(
            topo, text=f"{self.saudacao()}, {perfil['nome']}! 🌿", font=("Arial", 22, "bold"),
            text_color=TEXT, fg_color="transparent"
        ).pack(side="left")

        ctk.CTkButton(
            topo, text="✕", width=32, height=32, fg_color="transparent",
            hover_color="#F3E6E3", text_color=VERMELHO, corner_radius=8,
            command=self.acao_sair_app
        ).pack(side="right")

        ctk.CTkButton(
            topo, text="🚪", width=32, height=32, fg_color="transparent",
            hover_color="#EFEAE1", text_color=TEXT, corner_radius=8,
            command=self.acao_sair_conta
        ).pack(side="right", padx=(0, 6))

        ctk.CTkLabel(
            corpo, text=formatar_data_pt(date.today()), font=("Arial", 10),
            text_color=GRAY, fg_color="transparent"
        ).pack(anchor="w", padx=25)

        # --- Card de calorias com meta e barra de progresso ---
        consumidas = total_calorias(self.conta, hoje_str)
        meta = calcular_meta_calorica(perfil)
        restante = meta - consumidas

        card1 = ctk.CTkFrame(corpo, fg_color=CARD, border_color=BORDER,
                              border_width=1, corner_radius=12)
        card1.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(card1, text="CALORIAS HOJE", font=("Arial", 9, "bold"),
                     text_color=GRAY, fg_color="transparent").pack(pady=(20, 5))

        ctk.CTkLabel(card1, text=f"{consumidas} / {meta} kcal", font=("Arial", 30, "bold"),
                     text_color=TEXT, fg_color="transparent").pack()

        barra = ctk.CTkProgressBar(card1, fg_color=BORDER, progress_color=GREEN, height=10)
        barra.set(min(consumidas / meta, 1) if meta else 0)
        barra.pack(fill="x", padx=25, pady=(12, 8))

        texto_restante = f"Ainda restam {restante} kcal hoje" if restante >= 0 else \
            f"{abs(restante)} kcal acima da meta"
        cor_restante = GREEN if restante >= 0 else VERMELHO
        ctk.CTkLabel(card1, text=texto_restante, font=("Arial", 10),
                     text_color=cor_restante, fg_color="transparent").pack(pady=(0, 20))

        # --- Card de peso e IMC ---
        peso_hoje = peso_atual(self.conta)
        imc = calcular_imc(peso_hoje, perfil["altura"])
        classificacao, cor_imc = classificar_imc(imc)

        card2 = ctk.CTkFrame(corpo, fg_color=CARD, border_color=BORDER,
                              border_width=1, corner_radius=12)
        card2.pack(fill="x", padx=20, pady=5)

        linha = ctk.CTkFrame(card2, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=20)

        col1 = ctk.CTkFrame(linha, fg_color="transparent")
        col1.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col1, text="PESO", font=("Arial", 9, "bold"),
                     text_color=GRAY, fg_color="transparent").pack(anchor="w")
        ctk.CTkLabel(col1, text=f"{peso_hoje:.1f} kg".replace(".", ","),
                     font=("Arial", 26, "bold"), text_color=TEXT, fg_color="transparent").pack(anchor="w")

        col2 = ctk.CTkFrame(linha, fg_color="transparent")
        col2.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col2, text="IMC", font=("Arial", 9, "bold"),
                     text_color=GRAY, fg_color="transparent").pack(anchor="w")
        ctk.CTkLabel(col2, text=f"{imc:.1f}".replace(".", ","),
                     font=("Arial", 26, "bold"), text_color=TEXT, fg_color="transparent").pack(anchor="w")

        ctk.CTkLabel(card2, text=classificacao, font=("Arial", 10, "bold"),
                     text_color=cor_imc, fg_color="transparent").pack(pady=(0, 18))

        # --- Adicionar refeição rápida ---
        ctk.CTkLabel(corpo, text="Adicionar refeição", font=("Arial", 14, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(anchor="w", padx=25, pady=(20, 8))

        linha_add = ctk.CTkFrame(corpo, fg_color="transparent")
        linha_add.pack(fill="x", padx=20)

        self.entrada_refeicao = ctk.CTkEntry(
            linha_add, placeholder_text="Nome da refeição...", fg_color=CARD,
            text_color=TEXT, border_color=BORDER, corner_radius=8, height=40
        )
        self.entrada_refeicao.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.entrada_calorias = ctk.CTkEntry(
            linha_add, placeholder_text="kcal", width=80, fg_color=CARD,
            text_color=TEXT, border_color=BORDER, corner_radius=8, height=40
        )
        self.entrada_calorias.pack(side="left")
        self.entrada_calorias.bind("<Return>", lambda e: self.acao_salvar_refeicao())

        ctk.CTkButton(
            corpo, text="Salvar refeição", command=self.acao_salvar_refeicao,
            fg_color=GREEN, hover_color=GREEN, text_color="white",
            corner_radius=8, height=40
        ).pack(fill="x", padx=20, pady=10)

        # --- Lista de refeições de hoje ---
        cabecalho_lista = ctk.CTkFrame(corpo, fg_color="transparent")
        cabecalho_lista.pack(fill="x", padx=25, pady=(15, 8))

        ctk.CTkLabel(cabecalho_lista, text="Refeições de hoje", font=("Arial", 14, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(side="left")

        if listar_refeicoes(self.conta, hoje_str):
            ctk.CTkButton(
                cabecalho_lista, text="Limpar dia", width=90, height=26,
                fg_color="transparent", hover_color="#F3E6E3", text_color=VERMELHO,
                border_color=VERMELHO, border_width=1, corner_radius=6, font=("Arial", 10),
                command=lambda: self.acao_limpar_refeicoes_dia(hoje_str)
            ).pack(side="right")

        self.lista_refeicoes_frame = ctk.CTkFrame(corpo, fg_color="transparent")
        self.lista_refeicoes_frame.pack(fill="x", padx=20, pady=(0, 15))
        self.desenhar_lista_refeicoes(self.lista_refeicoes_frame, hoje_str)

        self.criar_nav()

    def desenhar_lista_refeicoes(self, container, data_str):
        for widget in container.winfo_children():
            widget.destroy()

        refeicoes = listar_refeicoes(self.conta, data_str)
        if not refeicoes:
            ctk.CTkLabel(
                container, text="Nenhuma refeição registrada ainda.", font=("Arial", 10),
                text_color=GRAY, fg_color="transparent"
            ).pack(pady=10)
            return

        for r in sorted(refeicoes, key=lambda x: x["horario"]):
            linha = ctk.CTkFrame(container, fg_color=CARD, border_color=BORDER,
                                  border_width=1, corner_radius=10)
            linha.pack(fill="x", pady=4)

            texto = f"{r['nome']}  ·  {r['horario']}"
            ctk.CTkLabel(linha, text=texto, font=("Arial", 12), text_color=TEXT,
                         fg_color="transparent").pack(side="left", padx=15, pady=12)

            ctk.CTkLabel(linha, text=f"{r['calorias']} kcal", font=("Arial", 11, "bold"),
                         text_color=GREEN, fg_color="transparent").pack(side="right", padx=(0, 8))

            ctk.CTkButton(
                linha, text="🗑", width=30, height=28, fg_color="transparent",
                hover_color="#F3E6E3", text_color=VERMELHO, corner_radius=6,
                command=lambda rid=r["id"]: self.acao_excluir_refeicao(data_str, rid)
            ).pack(side="right", padx=(0, 4))

            ctk.CTkButton(
                linha, text="✎", width=30, height=28, fg_color="transparent",
                hover_color="#EFEAE1", text_color=TEXT, corner_radius=6,
                command=lambda rf=r: self.acao_editar_refeicao(data_str, rf)
            ).pack(side="right", padx=(8, 0))

    def acao_salvar_refeicao(self):
        nome = self.entrada_refeicao.get().strip()
        calorias = self.entrada_calorias.get().strip()

        if nome == "" or calorias == "":
            messagebox.showwarning("Atenção", "Preencha o nome e as calorias da refeição.")
            return
        try:
            calorias_num = int(calorias)
            if calorias_num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Dados inválidos", "As calorias devem ser um número positivo.")
            return

        adicionar_refeicao(self.conta, self.dados, chave_data(date.today()), nome, calorias_num)
        self.tela_inicial()

    def acao_excluir_refeicao(self, data_str, id_refeicao):
        resposta = messagebox.askyesno("Excluir refeição", "Tem certeza que deseja excluir esta refeição?")
        if not resposta:
            return
        excluir_refeicao(self.conta, self.dados, data_str, id_refeicao)
        self._atualizar_apos_mudanca_refeicoes(data_str)

    def acao_limpar_refeicoes_dia(self, data_str):
        resposta = messagebox.askyesno(
            "Limpar refeições do dia",
            "Isso vai apagar todas as refeições registradas neste dia. Deseja continuar?"
        )
        if not resposta:
            return
        excluir_todas_refeicoes_do_dia(self.conta, self.dados, data_str)
        self._atualizar_apos_mudanca_refeicoes(data_str)

    def acao_editar_refeicao(self, data_str, refeicao):
        janela = ctk.CTkToplevel(self)
        janela.title("Editar refeição")
        janela.geometry("300x260")
        janela.configure(fg_color=BG)
        janela.resizable(False, False)
        janela.grab_set()

        ctk.CTkLabel(janela, text="Editar refeição", font=("Arial", 16, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(pady=(20, 15))

        nome_var = ctk.StringVar(value=refeicao["nome"])
        cal_var = ctk.StringVar(value=str(refeicao["calorias"]))

        ctk.CTkLabel(janela, text="Nome", font=("Arial", 10, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(anchor="w", padx=25)
        ctk.CTkEntry(janela, textvariable=nome_var, fg_color=CARD, text_color=TEXT,
                     border_color=BORDER, corner_radius=8, height=38).pack(fill="x", padx=25, pady=(4, 12))

        ctk.CTkLabel(janela, text="Calorias", font=("Arial", 10, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(anchor="w", padx=25)
        ctk.CTkEntry(janela, textvariable=cal_var, fg_color=CARD, text_color=TEXT,
                     border_color=BORDER, corner_radius=8, height=38).pack(fill="x", padx=25, pady=(4, 20))

        def confirmar():
            nome = nome_var.get().strip()
            cal_txt = cal_var.get().strip()
            if nome == "" or cal_txt == "":
                messagebox.showwarning("Atenção", "Preencha o nome e as calorias.", parent=janela)
                return
            try:
                cal_num = int(cal_txt)
                if cal_num <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Dados inválidos", "As calorias devem ser um número positivo.", parent=janela)
                return
            editar_refeicao(self.conta, self.dados, data_str, refeicao["id"], nome, cal_num)
            janela.destroy()
            self._atualizar_apos_mudanca_refeicoes(data_str)

        ctk.CTkButton(janela, text="Salvar", command=confirmar, fg_color=GREEN,
                      hover_color=GREEN, text_color="white", corner_radius=8,
                      height=40).pack(fill="x", padx=25, pady=(0, 8))
        ctk.CTkButton(janela, text="Cancelar", command=janela.destroy, fg_color="transparent",
                      hover_color="#EFEAE1", text_color=TEXT, border_color=BORDER,
                      border_width=1, corner_radius=8, height=40).pack(fill="x", padx=25)

    def _atualizar_apos_mudanca_refeicoes(self, data_str):
        """Redesenha a tela certa depois de excluir/editar refeições, sem perder o contexto."""
        if data_str == chave_data(date.today()) and self._tela_atual_eh_inicial():
            self.tela_inicial()
        elif hasattr(self, "frame_refeicoes_dia") and self.frame_refeicoes_dia.winfo_exists():
            self.atualizar_cabecalho_refeicoes()
        else:
            self.tela_inicial()

    def _tela_atual_eh_inicial(self):
        return hasattr(self, "lista_refeicoes_frame") and self.lista_refeicoes_frame.winfo_exists()

    # -------------------------------------------------
    # TELA 4 - REFEIÇÕES (com navegação por dia)
    # -------------------------------------------------
    def tela_refeicoes(self):
        self.limpar_tela()
        self.criar_titulo("Refeições", pady_topo=45)

        nav_data = ctk.CTkFrame(self, fg_color="transparent")
        nav_data.pack(fill="x", padx=20)

        ctk.CTkButton(nav_data, text="◀", width=40, height=36, fg_color=CARD,
                      hover_color="#EFEAE1", text_color=TEXT, corner_radius=8,
                      command=self.dia_anterior).pack(side="left")

        self.label_dia_refeicoes = ctk.CTkLabel(
            nav_data, text="", font=("Arial", 12, "bold"), text_color=TEXT, fg_color="transparent"
        )
        self.label_dia_refeicoes.pack(side="left", expand=True)

        ctk.CTkButton(nav_data, text="▶", width=40, height=36, fg_color=CARD,
                      hover_color="#EFEAE1", text_color=TEXT, corner_radius=8,
                      command=self.dia_seguinte).pack(side="right")

        self.label_total_refeicoes = ctk.CTkLabel(
            self, text="", font=("Arial", 11), text_color=GRAY, fg_color="transparent"
        )
        self.label_total_refeicoes.pack(pady=(10, 5))

        self.botao_limpar_dia_refeicoes = ctk.CTkButton(
            self, text="Limpar refeições deste dia", height=32, fg_color="transparent",
            hover_color="#F3E6E3", text_color=VERMELHO, border_color=VERMELHO,
            border_width=1, corner_radius=8, font=("Arial", 10),
            command=lambda: self.acao_limpar_refeicoes_dia(chave_data(self.data_selecionada))
        )

        self.frame_refeicoes_dia = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=GRAY
        )
        self.frame_refeicoes_dia.pack(fill="both", expand=True, padx=20)

        self.atualizar_cabecalho_refeicoes()
        self.criar_nav()

    def atualizar_cabecalho_refeicoes(self):
        data_str = chave_data(self.data_selecionada)
        rotulo = "Hoje" if self.data_selecionada == date.today() else formatar_data_curta(self.data_selecionada)
        self.label_dia_refeicoes.configure(text=rotulo)
        total = total_calorias(self.conta, data_str)
        self.label_total_refeicoes.configure(text=f"Total do dia: {total} kcal")
        self.desenhar_lista_refeicoes(self.frame_refeicoes_dia, data_str)

        self.botao_limpar_dia_refeicoes.pack_forget()
        if listar_refeicoes(self.conta, data_str):
            self.botao_limpar_dia_refeicoes.pack(fill="x", padx=20, pady=(0, 10), before=self.frame_refeicoes_dia)

    def dia_anterior(self):
        from datetime import timedelta
        self.data_selecionada -= timedelta(days=1)
        self.atualizar_cabecalho_refeicoes()

    def dia_seguinte(self):
        from datetime import timedelta
        if self.data_selecionada < date.today():
            self.data_selecionada += timedelta(days=1)
            self.atualizar_cabecalho_refeicoes()

    # -------------------------------------------------
    # TELA 5 - PESO (histórico + gráfico simples)
    # -------------------------------------------------
    def tela_peso(self):
        self.limpar_tela()
        self.criar_titulo("Peso", pady_topo=45)

        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=GRAY)
        corpo.pack(fill="both", expand=True, padx=0)

        card_grafico = ctk.CTkFrame(corpo, fg_color=CARD, border_color=BORDER,
                                     border_width=1, corner_radius=12)
        card_grafico.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(card_grafico, text="EVOLUÇÃO (últimos registros)", font=("Arial", 9, "bold"),
                     text_color=GRAY, fg_color="transparent").pack(pady=(15, 0))
        self.desenhar_grafico_peso(card_grafico, self.conta["pesos"])

        ctk.CTkLabel(corpo, text="Registrar novo peso", font=("Arial", 14, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(anchor="w", padx=25, pady=(10, 8))

        linha_add = ctk.CTkFrame(corpo, fg_color="transparent")
        linha_add.pack(fill="x", padx=20)

        self.entrada_peso_novo = ctk.CTkEntry(
            linha_add, placeholder_text="Peso de hoje (kg)", fg_color=CARD,
            text_color=TEXT, border_color=BORDER, corner_radius=8, height=40
        )
        self.entrada_peso_novo.pack(side="left", fill="x", expand=True)
        self.entrada_peso_novo.bind("<Return>", lambda e: self.acao_salvar_peso())

        ctk.CTkButton(
            corpo, text="Salvar peso", command=self.acao_salvar_peso,
            fg_color=GREEN, hover_color=GREEN, text_color="white",
            corner_radius=8, height=40
        ).pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(corpo, text="Histórico", font=("Arial", 14, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(anchor="w", padx=25, pady=(10, 8))

        if not self.conta["pesos"]:
            ctk.CTkLabel(corpo, text="Nenhum peso registrado ainda.", font=("Arial", 10),
                         text_color=GRAY, fg_color="transparent").pack(padx=25, pady=10)
        else:
            for p in reversed(self.conta["pesos"]):
                linha = ctk.CTkFrame(corpo, fg_color=CARD, border_color=BORDER,
                                      border_width=1, corner_radius=10)
                linha.pack(fill="x", padx=20, pady=4)
                d = date.fromisoformat(p["data"])
                ctk.CTkLabel(linha, text=formatar_data_curta(d), font=("Arial", 11),
                             text_color=TEXT, fg_color="transparent").pack(side="left", padx=15, pady=10)
                ctk.CTkLabel(linha, text=f"{p['peso']:.1f} kg".replace(".", ","),
                             font=("Arial", 11, "bold"), text_color=GREEN,
                             fg_color="transparent").pack(side="right", padx=15)
                ctk.CTkButton(
                    linha, text="🗑", width=28, height=26, fg_color="transparent",
                    hover_color="#F3E6E3", text_color=VERMELHO, corner_radius=6,
                    command=lambda data=p["data"]: self.acao_excluir_peso(data)
                ).pack(side="right", padx=(0, 4))

        self.criar_nav()

    def desenhar_grafico_peso(self, container, pesos):
        largura, altura = 330, 150
        canvas = tk.Canvas(container, width=largura, height=altura, bg=CARD, highlightthickness=0)
        canvas.pack(pady=10)

        pontos_dados = pesos[-10:]
        if len(pontos_dados) < 2:
            canvas.create_text(largura / 2, altura / 2,
                                text="Adicione mais registros\npara ver o gráfico",
                                fill=GRAY, font=("Arial", 10), justify="center")
            return

        valores = [p["peso"] for p in pontos_dados]
        minv, maxv = min(valores), max(valores)
        if minv == maxv:
            minv -= 1
            maxv += 1

        margem = 25
        largura_util = largura - 2 * margem
        altura_util = altura - 2 * margem
        n = len(valores)

        pontos = []
        for i, v in enumerate(valores):
            x = margem + i * (largura_util / (n - 1))
            y = margem + altura_util - ((v - minv) / (maxv - minv)) * altura_util
            pontos.append((x, y))

        for i in range(len(pontos) - 1):
            canvas.create_line(*pontos[i], *pontos[i + 1], fill=GREEN, width=2)
        for x, y in pontos:
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=GREEN, outline="")

        canvas.create_text(margem, 10, text=f"{maxv:.1f}".replace(".", ","),
                            fill=GRAY, font=("Arial", 8), anchor="w")
        canvas.create_text(margem, altura - 8, text=f"{minv:.1f}".replace(".", ","),
                            fill=GRAY, font=("Arial", 8), anchor="w")

    def acao_salvar_peso(self):
        texto = self.entrada_peso_novo.get().strip().replace(",", ".")
        try:
            peso_num = float(texto)
            if peso_num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Dados inválidos", "Digite um peso válido.")
            return

        adicionar_peso(self.conta, self.dados, chave_data(date.today()), peso_num)
        self.tela_peso()

    def acao_excluir_peso(self, data_str):
        resposta = messagebox.askyesno("Excluir registro", "Deseja excluir este registro de peso?")
        if not resposta:
            return
        excluir_peso(self.conta, self.dados, data_str)
        self.tela_peso()

    # -------------------------------------------------
    # TELA 6 - PERFIL
    # -------------------------------------------------
    def tela_perfil(self):
        self.limpar_tela()
        perfil = self.conta["perfil"]

        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=GRAY)
        corpo.pack(fill="both", expand=True)

        cabecalho = ctk.CTkFrame(corpo, fg_color="transparent")
        cabecalho.pack(fill="x", padx=25, pady=(40, 15))

        ctk.CTkLabel(cabecalho, text=f"👤 {perfil['nome']}", font=("Arial", 22, "bold"),
                     text_color=TEXT, fg_color="transparent").pack(side="left")

        ctk.CTkButton(
            cabecalho, text="🚪 Sair da conta", command=self.acao_sair_conta,
            font=("Arial", 11, "bold"), fg_color="transparent", hover_color="#EFEAE1",
            text_color=TEXT, border_color=BORDER, border_width=1,
            corner_radius=8, height=32, width=110
        ).pack(side="right")

        info_card = ctk.CTkFrame(corpo, fg_color=CARD, border_color=BORDER,
                                  border_width=1, corner_radius=12)
        info_card.pack(fill="x", padx=20, pady=(0, 15))

        meta = calcular_meta_calorica(perfil)
        imc = calcular_imc(peso_atual(self.conta), perfil["altura"])
        classificacao, _ = classificar_imc(imc)

        infos = [
            ("Peso", f"{peso_atual(self.conta):.1f} kg".replace(".", ",")),
            ("Altura", f"{perfil['altura']:.0f} cm"),
            ("Idade", f"{perfil['idade']} anos"),
            ("Sexo", perfil["sexo"]),
            ("Nível de atividade", perfil.get("nivel_atividade", "-")),
            ("Objetivo", perfil.get("objetivo", "-")),
            ("IMC", f"{imc:.1f} ({classificacao})".replace(".", ",", 1)),
            ("Meta calórica diária", f"{meta} kcal"),
        ]
        for i, (rotulo, valor) in enumerate(infos):
            linha = ctk.CTkFrame(info_card, fg_color="transparent")
            linha.pack(fill="x", padx=18, pady=(14 if i == 0 else 8, 0))
            ctk.CTkLabel(linha, text=rotulo, font=("Arial", 10), text_color=GRAY,
                         fg_color="transparent").pack(side="left")
            ctk.CTkLabel(linha, text=valor, font=("Arial", 11, "bold"), text_color=TEXT,
                         fg_color="transparent", wraplength=180, justify="right").pack(side="right")
        ctk.CTkFrame(info_card, fg_color="transparent", height=14).pack()

        self.criar_botao("Editar dados", lambda: self.tela_dados(editando=True), container=corpo, pady=(5, 10))
        self.criar_botao("Apagar dados desta conta", self.acao_apagar_dados, cor=VERMELHO,
                          container=corpo, pady=(0, 10))
        self.criar_botao_secundario("Sair do aplicativo", self.acao_sair_app, container=corpo, pady=(0, 25))

        self.criar_nav()

    def acao_sair_conta(self):
        resposta = messagebox.askyesno(
            "Sair da conta",
            "Deseja sair da sua conta?\n"
            "Seus dados continuam salvos e você pode entrar novamente ou criar uma nova conta."
        )
        if not resposta:
            return
        sair_conta(self.dados)
        self.conta = None
        self.conta_id = None
        self.tela_login()

    def acao_apagar_dados(self):
        resposta = messagebox.askyesno(
            "Tem certeza?",
            "Isso vai apagar o perfil, as refeições e o histórico de peso desta conta permanentemente."
        )
        if resposta:
            excluir_conta(self.dados, self.conta_id)
            self.conta = None
            self.conta_id = None
            self.tela_login()


if __name__ == "__main__":
    app = App()
    app.mainloop()