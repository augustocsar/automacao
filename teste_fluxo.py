import re
import sys
import time
import random
import traceback
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)

# Console do Windows costuma engasgar com emoji quando a saída é redirecionada.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =======================================================
# CONFIGURAÇÕES
# =======================================================
CURSOS = [
    "Administração",
    "Odontologia",
    "Medicina Veterinária",
    "Educação Física",
    "Direito",
    "Fisioterapia",
    "Fonoaudiologia",
    "Psicologia",
    "Enfermagem",
    "Biomedicina",
    "Sistemas de Informação",
    "Farmácia",
    "Análise e Desenvolvimento de Sistemas",
    "Terapia Ocupacional",
    "Estética e Cosmética",
    "Ciência da Computação",
]

TURNOS = ["Matutino", "Noturno"]
LISTA_CEPS = [
    "49090-080",  # usado no mapeamento manual
    "49010-000",
    "49020-010",
    "49030-020",
    "49040-030",
    "49050-040",
]

URL_AFILIADO = (
    "https://vest.uninassau.edu.br/cursos"
    "?utm_owner=0160101326&utm_profile=Comercial&utm_team=Consultor"
    "&modalities=presencial&city=aracaju-se&state=SE"
)

NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela",
    "Hugo", "Isabela", "Joao", "Larissa", "Marcos", "Natalia", "Otavio",
    "Paula", "Rafael", "Sofia", "Tiago", "Vanessa", "Wagner",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa",
    "Almeida", "Ferreira", "Rodrigues", "Gomes", "Martins", "Araujo",
    "Barbosa", "Ribeiro", "Cardoso", "Moraes", "Nunes",
]

POLO_ALVO = "ARACAJU"

PASTA_SHOTS = Path("screenshots")
PASTA_TRACES = Path("traces")


# =======================================================
# DADOS ALEATÓRIOS DE TESTE
# =======================================================
def gerar_cpf_valido():
    """Gera 11 dígitos com dígitos verificadores válidos (o site valida o CPF)."""
    while True:
        base = [random.randint(0, 9) for _ in range(9)]
        if len(set(base)) == 1:  # evita 111.111.111 etc.
            continue

        for peso_inicial in (10, 11):
            soma = sum(d * (peso_inicial - i) for i, d in enumerate(base))
            digito = (soma * 10) % 11
            base.append(0 if digito == 10 else digito)

        return "".join(str(d) for d in base)


def formatar_cpf(cpf):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def gerar_data_nascimento(idade_min=18, idade_max=35):
    hoje = date.today()
    mais_velho = hoje - timedelta(days=idade_max * 365 + 30)
    mais_novo = hoje - timedelta(days=idade_min * 365)
    dias = (mais_novo - mais_velho).days
    nascimento = mais_velho + timedelta(days=random.randint(0, max(dias, 1)))
    return nascimento.strftime("%d/%m/%Y")


def gerar_dados():
    nome = f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}"
    slug = re.sub(r"[^a-z]", "", nome.lower())
    cpf = gerar_cpf_valido()

    return {
        "nome": nome,
        "email": f"{slug}{random.randint(10, 9999)}@gmail.com",
        "telefone": f"799{random.randint(8000, 9999)}{random.randint(1000, 9999)}",
        "cpf": formatar_cpf(cpf),
        "cpf_digitos": cpf,
        "nascimento": gerar_data_nascimento(),
        "cep": random.choice(LISTA_CEPS),
        "numero": str(random.randint(10, 2000)),
    }


# =======================================================
# DIAGNÓSTICO
# =======================================================
def _slug(texto):
    return re.sub(r"[^a-z0-9]+", "_", str(texto).lower()).strip("_") or "passo"


def salvar_diagnostico(page, nome, run_id):
    """Salva screenshot + HTML da tela no momento da falha."""
    PASTA_SHOTS.mkdir(exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = PASTA_SHOTS / f"{run_id}_{carimbo}_{_slug(nome)}"

    try:
        page.screenshot(path=f"{base}.png", full_page=True)
        print(f"     📸 Screenshot salvo em: {base}.png")
    except Exception as erro:
        print(f"     (não foi possível salvar o screenshot: {erro})")

    try:
        Path(f"{base}.html").write_text(page.content(), encoding="utf-8")
    except Exception as erro:
        print(f"     (não foi possível salvar o HTML: {erro})")

    return base


@contextmanager
def passo(page, nome, run_id):
    """Agrupa uma etapa: loga antes e, em caso de erro, salva o diagnóstico."""
    print(f"  -> {nome}")
    try:
        if page.is_closed():
            raise RuntimeError(
                "O navegador/página foi fechado durante a execução "
                "(verifique se a janela foi fechada manualmente)"
            )
        yield
    except Exception as erro:
        print(f"  ❌ Falhou em '{nome}': {type(erro).__name__}: {erro}")
        salvar_diagnostico(page, nome, run_id)
        raise


# =======================================================
# HELPERS DE INTERAÇÃO
# =======================================================
def localizar(page, descricao, *candidatos, timeout=20000):
    """Espera (com polling) até algum dos candidatos ficar visível.

    O polling é essencial em SPA: logo após um clique a próxima tela ainda
    não existe no DOM, então uma checagem única daria falso negativo.
    """
    limite = time.time() + timeout / 1000

    while True:
        for locator in candidatos:
            try:
                if locator.count() > 0 and locator.first.is_visible():
                    return locator.first
            except Exception:
                continue

        if time.time() >= limite:
            raise RuntimeError(f"Campo não encontrado: {descricao}")

        page.wait_for_timeout(250)


def clicar(locator, descricao):
    """Clique normal e, se o elemento estiver coberto/instável, clique forçado."""
    try:
        locator.scroll_into_view_if_needed()
        locator.click()
    except Exception:
        locator.click(force=True)
    print(f"     clique: {descricao}")


def preencher(campo, valor, descricao=None):
    campo.scroll_into_view_if_needed()
    campo.click()
    campo.fill(str(valor))
    valor_final = campo.input_value()
    if descricao:
        print(f"     {descricao}: {valor_final}")
    return valor_final


def preencher_mascarado(campo, valor, descricao=None):
    """Digita dígito a dígito para a máscara do campo se ajustar sozinha."""
    campo.scroll_into_view_if_needed()
    campo.click()
    campo.fill("")
    campo.press_sequentially(str(valor), delay=40)
    valor_final = campo.input_value()
    if descricao:
        print(f"     {descricao}: {valor_final}")
    return valor_final


def preencher_data_nascimento(campo, data_br):
    """Digita 8 dígitos e, se o campo não tiver máscara, aplica dd/mm/aaaa."""
    digitos = re.sub(r"\D", "", data_br)
    if len(digitos) != 8:
        raise ValueError(f"Data de nascimento inválida: {data_br!r}")

    campo.scroll_into_view_if_needed()
    campo.click()
    campo.fill("")
    campo.press_sequentially(digitos, delay=40)
    valor = campo.input_value()

    if re.fullmatch(r"\d{8}", (valor or "").strip()):
        campo.fill(f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}")
        valor = campo.input_value()

    print(f"     nascimento: {valor}")
    if not (valor or "").strip():
        raise RuntimeError("O campo de data de nascimento ficou vazio")
    return valor


def campo_checkout(page, componente, rotulo, nome_acessivel, placeholder=None, timeout=30000):
    """Usa o nome do mapeamento primeiro e a classe Appian como reserva."""
    candidatos = [
        # Mesmo padrão do mapeamento: string (substring), nunca regex com "/".
        page.get_by_role("textbox", name=nome_acessivel),
        page.locator(f".mx-name-{componente} input"),
    ]
    if placeholder:
        candidatos.append(page.get_by_placeholder(placeholder))
    return localizar(page, rotulo, *candidatos, timeout=timeout)


def marcar_checkbox(page, padrao, descricao):
    candidatos = [
        page.get_by_role("checkbox", name=padrao),
        page.locator("label").filter(has_text=padrao).locator("input[type='checkbox']"),
    ]

    alvo = None
    for locator in candidatos:
        if locator.count() > 0:
            alvo = locator.first
            break

    if alvo is None:
        raise RuntimeError(f"Checkbox não encontrado: {descricao}")

    alvo.scroll_into_view_if_needed()
    if not alvo.is_checked():
        try:
            alvo.check(force=True)
        except Exception:
            # Alguns componentes só reagem ao clique no <label> que envolve o input.
            alvo.locator("xpath=ancestor::label[1]").click(force=True)

    expect(alvo).to_be_checked(timeout=8000)
    print(f"     {descricao}: marcado")


def fechar_popup_inicial(page):
    botao = page.get_by_role("button", name=re.compile(r"^(Close|Fechar)$", re.I))
    try:
        if botao.count() > 0 and botao.first.is_visible():
            botao.first.click()
            print("     popup inicial fechado")
    except Exception:
        pass


def fechar_banner_cookies(page):
    """O banner de privacidade fica sobre a lateral e pode interceptar cliques."""
    for nome in ("Recusar", "Aceitar"):
        botao = page.get_by_role("button", name=re.compile(rf"^{nome}$", re.I))
        try:
            botao.first.wait_for(state="visible", timeout=4000)
            clicar(botao.first, f"banner de cookies: {nome}")
            page.wait_for_timeout(600)
            return True
        except PlaywrightTimeoutError:
            continue
    print("     sem banner de cookies")
    return False


def abrir_card_curso(page, curso):
    """Segue o mapeamento: clica no link do card pelo nome acessível.

    `get_by_role(..., name=...)` casa por substring, então o nome do curso basta.
    Não existe fallback para `div`: clicar num container genérico já nos custou
    duas rodadas (clicava em elemento errado e a página não navegava).
    """
    link = page.get_by_role("link", name=curso).first
    link.wait_for(state="visible", timeout=30000)
    clicar(link, f"card do curso {curso}")


def selecionar_turno(page, turno_desejado):
    """Algumas ofertas deixam escolher o turno; outras já vêm com um turno fixo."""
    alternativo = "Noturno" if turno_desejado == "Matutino" else "Matutino"

    for turno in (turno_desejado, alternativo):
        botao = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(turno)}\b", re.I)
        )
        if botao.count() == 0:
            continue

        alvo = botao.first
        alvo.scroll_into_view_if_needed()
        clicar(alvo, f"turno {turno}")

        # Se o componente expõe aria-pressed/aria-checked, confere a seleção.
        try:
            if alvo.get_attribute("aria-pressed") == "true":
                print(f"     turno confirmado: {turno}")
            elif alvo.get_attribute("aria-checked") == "true":
                print(f"     turno confirmado: {turno}")
        except Exception:
            pass
        return turno

    # Não é falha: a oferta já define o turno (ele aparece no resumo do curso).
    turno_fixo = page.get_by_text(re.compile(r"^(Matutino|Noturno)$", re.I))
    if turno_fixo.count() > 0:
        valor = turno_fixo.first.inner_text().strip()
        print(f"     turno não é selecionável nesta oferta; a página define: {valor}")
        return valor

    print("     turno não é selecionável nesta oferta; seguindo sem escolher")
    return None


def obter_valor(locator):
    try:
        return locator.input_value()
    except Exception:
        try:
            return locator.inner_text()
        except Exception:
            return ""


def garantir_polo(page):
    """Seleciona o polo por role/label, sem depender de IDs gerados pelo Downshift."""
    polo = page.get_by_role("combobox", name=re.compile("Polo de ensino", re.I))

    if polo.count() == 0:
        # Fallback: às vezes o combobox não recebe o nome acessível.
        polo = page.get_by_label(re.compile("Polo de ensino", re.I))

    if polo.count() == 0:
        print("     ⚠️ Campo 'Polo de ensino' não apareceu nesta tela.")
        return None

    alvo = polo.first
    try:
        alvo.wait_for(state="visible", timeout=12000)
    except PlaywrightTimeoutError:
        print("     ⚠️ Campo 'Polo de ensino' existe, mas não ficou visível.")
        return None

    atual = obter_valor(alvo).upper()
    if POLO_ALVO in atual:
        print(f"     polo já preenchido: {obter_valor(alvo)}")
        return obter_valor(alvo)

    alvo.scroll_into_view_if_needed()
    try:
        alvo.click()
    except Exception:
        alvo.click(force=True)

    try:
        alvo.fill("")
    except Exception:
        # Combobox que não aceita fill: seleciona o texto e apaga.
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")

    print("     digitando 'Aracaju' para filtrar os polos...")
    page.keyboard.type("araca", delay=60)

    opcao = page.get_by_role("option", name=re.compile(POLO_ALVO, re.I))
    if opcao.count() == 0:
        opcao = page.get_by_text(re.compile(r"SE\s*-\s*ARACAJU", re.I), exact=False)

    if opcao.count() == 0:
        raise RuntimeError(
            "A lista de polos abriu, mas a opção 'SE - ARACAJU' não foi encontrada"
        )

    escolhida = opcao.first
    escolhida.wait_for(state="visible", timeout=10000)
    clicar(escolhida, "opção SE - ARACAJU")

    final = obter_valor(alvo)
    if POLO_ALVO not in final.upper():
        raise RuntimeError(
            f"O polo foi clicado, mas o campo não confirma a seleção (valor: {final!r})"
        )

    print(f"     polo selecionado: {final}")
    return final


def escolher_pagar_depois(page):
    try:
        page.locator("text=COMO VOCÊ QUER GARANTIR SUA VAGA?").scroll_into_view_if_needed()
    except Exception:
        pass

    # Appian: o grupo `radio-button-payLater` é o "Pagar depois" (opção Sim = true).
    radio_pagar_depois = page.locator(
        ".radio-button-payLater input[type='radio'][value='true'], "
        ".mx-name-radioButtons2 input[type='radio'][value='true']"
    )

    candidatos = [
        # Mapeamento manual: o card "Pagar depois" é um <button> com esse texto.
        page.get_by_role("button", name="Mais flexibilidade"),
        radio_pagar_depois,
        page.get_by_role("radio", name=re.compile(r"pagar\s*depois", re.I)),
        page.get_by_text(re.compile(r"pagar\s*depois", re.I)),
    ]

    alvo = None
    for locator in candidatos:
        if locator.count() > 0:
            alvo = locator.first
            break

    if alvo is None:
        raise RuntimeError("Opção 'Pagar depois' não encontrada no checkout")

    alvo.scroll_into_view_if_needed()
    clicar(alvo, "'Pagar depois'")

    if radio_pagar_depois.count() > 0:
        try:
            expect(radio_pagar_depois.first).to_be_checked(timeout=8000)
            print("     'Pagar depois' confirmado como marcado")
        except Exception:
            print("     ⚠️ o rádio de 'Pagar depois' não ficou marcado")


def fechar_popup_entendi(page):
    botao = page.get_by_role("button", name="Entendi")
    try:
        botao.first.wait_for(state="visible", timeout=8000)
        clicar(botao.first, "popup 'Entendi'")
        return True
    except PlaywrightTimeoutError:
        print("     sem popup 'Entendi' nesta rodada")
        return False


def aceitar_contrato(page):
    padrao = re.compile(r"aceite o Contrato", re.I)

    candidatos = [
        # O sufixo do id muda a cada render (_gqt_30, _sgi_30...), por isso prefixo.
        page.locator("[id^='p.Checkout.SNP_Checkout_Web.chk_Resumo_AceiteTermos']"),
        page.locator(".mx-name-chk_Resumo_AceiteTermos input[type='checkbox']"),
        page.get_by_role("checkbox", name=re.compile("Contrato", re.I)),
        page.locator("label").filter(has_text=padrao).locator("input[type='checkbox']"),
        page.locator("input[type='checkbox']").last,
    ]

    alvo = None
    for locator in candidatos:
        if locator.count() > 0:
            alvo = locator.first
            break

    if alvo is None:
        raise RuntimeError("Checkbox do contrato não encontrado")

    alvo.scroll_into_view_if_needed()
    if not alvo.is_checked():
        try:
            alvo.check(force=True)
        except Exception:
            page.get_by_text(padrao, exact=False).first.click(force=True)

    expect(alvo).to_be_checked(timeout=8000)
    print("     contrato aceito")


def coletar_erros_validacao(page):
    """Junta mensagens visíveis de erro/validação para o log de falha.

    Ignora a barra de progresso do Appian (`mx-progress`), que também usa
    role=alert e era confundida com erro.
    """
    mensagens = []
    seletor = (
        "[role='alert']:not(.mx-progress), [aria-invalid='true'], "
        ".Mui-error, .error, .error-message"
    )
    try:
        for elemento in page.locator(seletor).all():
            try:
                if not elemento.is_visible():
                    continue
                if elemento.get_attribute("aria-busy") == "true":
                    continue
                texto = (elemento.inner_text() or "").strip().strip("\u200b")
            except Exception:
                continue
            if texto and texto not in mensagens:
                mensagens.append(texto[:160])
    except Exception:
        pass
    return mensagens


def app_ocupado(page):
    """True quando o Appian está processando (barra de progresso ativa)."""
    try:
        progresso = page.locator("[role='alert'][aria-busy='true'], .mx-progress[aria-busy='true']")
        return progresso.count() > 0 and progresso.first.is_visible()
    except Exception:
        return False


def finalizar_compra(page, timeout=90000):
    botao = page.get_by_role("button", name="Finalizar compra")
    if botao.count() == 0:
        raise RuntimeError("Botão 'Finalizar compra' não encontrado")

    alvo = botao.first
    alvo.scroll_into_view_if_needed()

    try:
        expect(alvo).to_be_enabled(timeout=15000)
    except Exception:
        erros = coletar_erros_validacao(page)
        detalhe = " | ".join(erros) if erros else "sem mensagem visível"
        raise RuntimeError(f"Botão 'Finalizar compra' continua desabilitado ({detalhe})")

    # Deixa o último XAS (aceite do contrato) assentar antes de submeter.
    page.wait_for_timeout(1000)
    clicar(alvo, "Finalizar compra")

    confirmacao = page.get_by_text(re.compile("Pedido em andamento", re.I)).first
    limite = time.time() + timeout / 1000
    ultimo_aviso = 0.0

    # O app carrega a página de feedback sob demanda; às vezes o chunk demora.
    while time.time() < limite:
        try:
            if confirmacao.is_visible():
                print("  ✅ TELA DE CONFIRMAÇÃO EXIBIDA COM SUCESSO!")
                return True
        except Exception:
            pass

        if time.time() - ultimo_aviso >= 15:
            estado = "processando" if app_ocupado(page) else "ocioso"
            print(f"     ... aguardando confirmação ({estado})")
            ultimo_aviso = time.time()

        page.wait_for_timeout(1000)

    erros = coletar_erros_validacao(page)
    detalhe = " | ".join(erros) if erros else "nenhuma mensagem de erro visível"
    raise RuntimeError(
        f"A confirmação não apareceu após 'Finalizar compra' em {timeout/1000:.0f}s "
        f"({detalhe})"
    )


def esperar_checkout(context, page):
    """O checkout é outra aplicação (checkoutv2): espera a URL ou uma nova aba."""
    padrao = re.compile(r"checkoutv2\.uninassau\.edu\.br/p/", re.I)

    try:
        page.wait_for_url(padrao, timeout=30000)
        print(f"     checkout carregado: {page.url[:100]}")
        return page
    except PlaywrightTimeoutError:
        pass

    for outra in context.pages:
        try:
            if padrao.search(outra.url or ""):
                outra.wait_for_load_state("domcontentloaded")
                print(f"     checkout carregado em outra aba: {outra.url[:100]}")
                return outra
        except Exception:
            continue

    raise RuntimeError("O checkout (checkoutv2.uninassau.edu.br) não abriu")


# =======================================================
# FLUXO PRINCIPAL
# =======================================================
def testar_curso_randomico(run_id):
    curso = random.choice(CURSOS)
    turno_sorteado = random.choice(TURNOS)
    dados = gerar_dados()

    resultado = {
        "run_id": run_id,
        "curso": curso,
        "turno_sorteado": turno_sorteado,
        "turno_usado": None,
        "dados": dados,
        "ok": False,
        "motivo": "",
    }

    print(
        f"\n🎲 Sorteio da rodada -> Curso: {curso} | Turno: {turno_sorteado}\n"
        f"   Nome: {dados['nome']} | E-mail: {dados['email']}\n"
        f"   Tel: {dados['telefone']} | CPF: {dados['cpf']} | "
        f"Nasc: {dados['nascimento']} | CEP: {dados['cep']} | Nº: {dados['numero']}"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        PASTA_TRACES.mkdir(exist_ok=True)
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()
        page.set_default_timeout(15000)

        try:
            # ==========================================
            # PÁGINA 1: BUSCA DO CURSO
            # ==========================================
            with passo(page, "Página 1: buscando o curso", run_id):
                page.goto(URL_AFILIADO, wait_until="domcontentloaded")
                fechar_popup_inicial(page)
                fechar_banner_cookies(page)

                campo_curso = localizar(
                    page,
                    "Nome do curso",
                    page.get_by_role("textbox", name=re.compile("Nome do curso", re.I)),
                    page.get_by_placeholder(re.compile("curso", re.I)),
                )
                preencher(campo_curso, curso, "curso digitado")

                clicar(
                    page.get_by_role("button", name=re.compile("Aplicar", re.I)).first,
                    "Aplicar filtro",
                )
                page.wait_for_timeout(1500)

            with passo(page, f"Página 1: abrindo o card de {curso}", run_id):
                abrir_card_curso(page, curso)

            with passo(page, "Página 2: aguardando a troca de tela", run_id):
                try:
                    page.wait_for_url(re.compile(r"/cursos/[^?]+"), timeout=20000)
                    print("     URL de inscrição carregada")
                except PlaywrightTimeoutError:
                    print("     ⚠️ a URL não mudou; vou procurar o formulário na tela atual")

            # ==========================================
            # PÁGINA 2: FORMULÁRIO DE INSCRIÇÃO
            # ==========================================
            with passo(page, "Página 2: preenchendo formulário", run_id):
                campo_nome = localizar(
                    page,
                    "Nome completo",
                    page.get_by_role("textbox", name="Nome completo"),
                    timeout=30000,
                )
                preencher(campo_nome, dados["nome"], "nome")

                preencher(
                    localizar(
                        page,
                        "E-mail",
                        page.get_by_role("textbox", name="E-mail"),
                    ),
                    dados["email"],
                    "e-mail",
                )

                preencher(
                    localizar(
                        page,
                        "Telefone/WhatsApp",
                        page.get_by_role("textbox", name="Telefone/WhatsApp"),
                    ),
                    dados["telefone"],
                    "telefone",
                )

                resultado["turno_usado"] = selecionar_turno(page, turno_sorteado)

                # Mapeamento: clica no decorator e garante o checkbox marcado.
                decorator = page.locator(".Checkbox-module__4Xr8zW__decorator")
                if decorator.count() > 0:
                    clicar(decorator.first, "decorator do aceite")
                marcar_checkbox(
                    page, re.compile("Li e aceito", re.I), "aceite dos termos"
                )

                clicar(
                    page.get_by_role("button", name="Quero me inscrever").first,
                    "Quero me inscrever",
                )

            with passo(page, "Página 2: confirmando inscrição", run_id):
                btn_confirmar = page.get_by_role(
                    "button", name="Confirmar e continuar"
                ).first
                btn_confirmar.wait_for(state="visible")
                clicar(btn_confirmar, "Confirmar e continuar")

            with passo(page, "Checkout: aguardando a página de pagamento", run_id):
                page = esperar_checkout(context, page)

            # ==========================================
            # CHECKOUT (checkoutv2 / Appian)
            # ==========================================
            with passo(page, "Checkout: CPF e data de nascimento", run_id):
                campo_cpf = campo_checkout(
                    page,
                    "txt_Pessoais_CPF",
                    "CPF",
                    "000.000.000-",
                    placeholder="000.000.000-00",
                )
                preencher_mascarado(
                    campo_cpf, re.sub(r"\D", "", dados["cpf"]), "CPF"
                )

                campo_nasc = campo_checkout(
                    page,
                    "txt_Pessoais_DataNascimento",
                    "Data de nascimento",
                    "DD/MM/AAAA",
                )
                preencher_data_nascimento(campo_nasc, dados["nascimento"])

            with passo(page, "Checkout: CEP e número", run_id):
                logradouro = page.locator(".mx-name-txt_Endereco_Logradouro input")
                outros = [c for c in LISTA_CEPS if c != dados["cep"]]
                ceps = [dados["cep"]] + random.sample(outros, k=min(2, len(outros)))
                endereco_ok = False

                # Nem todo CEP da lista existe; tenta até 3 até o endereço autocompletar.
                for cep in ceps:
                    campo_cep = campo_checkout(
                        page,
                        "txt_Endereco_CEP",
                        "CEP",
                        "00000-",
                        placeholder="00000-000",
                    )
                    preencher_mascarado(campo_cep, re.sub(r"\D", "", cep), "CEP")
                    campo_cep.press("Tab")
                    page.wait_for_timeout(3000)

                    if (
                        logradouro.count() > 0
                        and logradouro.first.input_value().strip()
                    ):
                        print(
                            f"     endereço preenchido: {logradouro.first.input_value()}"
                        )
                        endereco_ok = True
                        break

                if not endereco_ok:
                    print("     ⚠️ nenhum CEP preencheu o endereço automaticamente")

                campo_numero = campo_checkout(
                    page,
                    "txt_Endereco_Numero",
                    "Número",
                    "Número*",
                    placeholder="Ex: 456",
                )
                preencher(campo_numero, dados["numero"], "número")

            with passo(page, "Checkout: polo de ensino", run_id):
                resultado["polo"] = garantir_polo(page)

            with passo(page, "Checkout: opção 'Pagar depois'", run_id):
                escolher_pagar_depois(page)
                fechar_popup_entendi(page)

            with passo(page, "Checkout: aceite do contrato", run_id):
                aceitar_contrato(page)

            with passo(page, "Checkout: finalizando compra", run_id):
                resultado["ok"] = finalizar_compra(page)

        except Exception as erro:
            resultado["motivo"] = f"{type(erro).__name__}: {erro}"
            print(f"\n  ❌ Rodada {run_id} interrompida: {resultado['motivo']}")
            traceback.print_exc()
        finally:
            try:
                context.tracing.stop(path=str(PASTA_TRACES / f"{run_id}.zip"))
                print(f"  🧭 Trace salvo em: {PASTA_TRACES / f'{run_id}.zip'}")
            except Exception:
                pass
            context.close()
            browser.close()

    return resultado


def main():
    repeticoes = 1
    if len(sys.argv) > 1:
        try:
            repeticoes = max(1, int(sys.argv[1]))
        except ValueError:
            print("Uso: python teste_fluxo.py [quantidade_de_rodadas]")
            sys.exit(2)

    resultados = []
    for indice in range(1, repeticoes + 1):
        run_id = f"r{indice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n{'=' * 60}\nRODADA {indice}/{repeticoes}  (id: {run_id})\n{'=' * 60}")
        resultados.append(testar_curso_randomico(run_id))

    print(f"\n{'=' * 60}\nRESUMO\n{'=' * 60}")
    for item in resultados:
        status = "✅ OK" if item["ok"] else "❌ FALHOU"
        print(
            f"  {status} | {item['curso']} ({item['turno_usado'] or item['turno_sorteado']})"
            f" | id: {item['run_id']}"
        )
        dados = item.get("dados") or {}
        if dados:
            print(f"         aluno: {dados.get('nome')} | {dados.get('email')}")
        if item["motivo"]:
            print(f"         motivo: {item['motivo']}")

    total_ok = sum(1 for item in resultados if item["ok"])
    print(f"\n  Sucesso: {total_ok}/{len(resultados)}")
    print("\n🔥 Teste ponta a ponta finalizado!")

    sys.exit(0 if total_ok == len(resultados) else 1)


if __name__ == "__main__":
    main()
