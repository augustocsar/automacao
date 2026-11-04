import re
import random
from playwright.sync_api import sync_playwright, TimeoutError

def testar_curso_randomico():
    cursos = [
        "Pedagogia", "Enfermagem", "Administração", "Análise e Desenvolvimento de Sistemas", 
        "Tecnologia em Gestão de Recursos Humanos", "Terapia Ocupacional", "Farmácia", 
        "Ciências Contábeis", "Educação Física", "Logística", "Gestão Pública", "Fisioterapia", 
        "Biomedicina", "Gestão Comercial", "Marketing", "Gestão Financeira", "Engenharia Civil", 
        "Gestão de Serviços Judiciais e Notariais", "Tecnologia em Processos Gerenciais", 
        "Engenharia Elétrica", "Estética e Cosmética", "Arquitetura e Urbanismo", 
        "Engenharia Mecânica", "Ciências Aeronáuticas", "Gestão da Tecnologia da Informação", 
        "Letras - Português", "Tecnologia em Design de Interiores", "Engenharia de Produção", 
        "História", "Letras - Inglês", "Gestão da Qualidade", "Segurança Pública", 
        "Gestão Ambiental", "Matemática", "Bacharelado em Serviço Social", "Teologia", 
        "Gestão de Trânsito", "Ciências Econômicas", "Ciências Biológicas", "Gestão Hospitalar", 
        "Negócios Imobiliários", "Educação Especial", "Tecnologia em Segurança da Informação", 
        "Tecnologia em Banco de Dados", "Medicina Veterinária", "Ciência da Computação", 
        "Direito", "Fonoaudiologia", "Odontologia", "Psicologia"
    ]
    
    turnos = ["Matutino", "Noturno"]
    lista_ceps = ["49010-000", "49020-010", "49030-020", "49040-030", "49050-040"]

    curso = random.choice(cursos)
    turno_sorteado = random.choice(turnos)
    
    url_afiliado = "https://vest.uninassau.edu.br/cursos?utm_owner=0160101326&utm_profile=Comercial&utm_team=Consultor&modalities=presencial&city=aracaju-se&state=SE"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"\n🎲 Sorteio da rodada -> Curso: {curso} | Turno: {turno_sorteado}")
        
        try:
            # ==========================================
            # PÁGINA 1: BUSCA DO CURSO E CLIQUE NO CARD
            # ==========================================
            page.goto(url_afiliado, wait_until="domcontentloaded")

            try:
                botao_close = page.get_by_role("button", name="Close")
                if botao_close.is_visible(timeout=2000):
                    botao_close.click()
            except Exception:
                pass

            cb_padrao = page.get_by_role("checkbox", name=re.compile("^Presencial", re.IGNORECASE))
            if cb_padrao.is_checked():
                cb_padrao.uncheck(force=True)
                page.wait_for_timeout(1000)

            campo_curso = page.get_by_role("textbox", name="Nome do curso")
            campo_curso.click(force=True)
            campo_curso.fill(curso)

            page.get_by_role("button", name="Aplicar").click(force=True)
            page.wait_for_timeout(2000) 

            try:
                page.get_by_role("link", name=re.compile(f"^{curso}", re.IGNORECASE)).first.click(timeout=8000, force=True)
                print("  ✅ Sucesso! Card furado.")
            except TimeoutError:
                try:
                    page.locator("div").filter(has_text=re.compile(f"^{curso}", re.IGNORECASE)).first.click(force=True, timeout=8000)
                    print("  ✅ Sucesso (div alternativa)! Card furado.")
                except TimeoutError:
                    print(f"  ❌ Falha: O card de {curso} não apareceu nos resultados.")
                    return
            
            # ==========================================
            # PÁGINA 2: FORMULÁRIO DE INSCRIÇÃO
            # ==========================================
            print("  -> Preenchendo formulário (Página 2)...")
            
            campo_nome = page.get_by_role("textbox", name="Nome completo")
            campo_nome.wait_for(state="visible", timeout=15000)

            campo_nome.fill("Aluno Teste Random")
            page.get_by_role("textbox", name="E-mail").fill("aluno_random@email.com")
            page.get_by_role("textbox", name="Telefone/WhatsApp").fill("79999999999")

            print(f"  -> Marcando turno: {turno_sorteado}")
            btn_turno = page.get_by_role("button", name=turno_sorteado)
            if btn_turno.is_visible():
                btn_turno.click(force=True)

            page.get_by_role("checkbox", name=re.compile("Li e aceito o", re.IGNORECASE)).check(force=True)
            page.get_by_role("button", name="Quero me inscrever").click(force=True)

            btn_confirmar = page.get_by_role("button", name="Confirmar e continuar")
            btn_confirmar.wait_for(state="visible", timeout=10000) 
            btn_confirmar.click(force=True)
            print("  ✅ Página 2 concluída! Indo para a página 3 (Checkout)...")

            # ==========================================
            # PÁGINA 3: CHECKOUT / DADOS FINAIS
            # ==========================================
            campo_email_pg3 = page.get_by_role("textbox", name="E-mail*")
            campo_email_pg3.wait_for(state="visible", timeout=15000)
            
            print("  -> Preenchendo dados finais e deixando o CEP autocompletar...")
            
            campo_email_pg3.fill("aluno_random@email.com")
            page.get_by_role("textbox", name="(00) 0000-").fill("79999999999")
            
            page.get_by_role("textbox", name="000.000.000-").click(force=True)
            page.get_by_role("textbox", name="000.000.000-").fill("12345678909") 
            page.get_by_role("textbox", name="DD/MM/AAAA").click(force=True)
            page.get_by_role("textbox", name="DD/MM/AAAA").fill("01012000") 
            
            cep_escolhido = random.choice(lista_ceps)
            page.get_by_role("textbox", name="00000-").click(force=True)
            page.get_by_role("textbox", name="00000-").fill(cep_escolhido) 
            
            page.wait_for_timeout(3000) 
            
            page.get_by_role("textbox", name="Número*").click(force=True)
            page.get_by_role("textbox", name="Número*").fill(str(random.randint(10, 2000))) 

            print("  -> Selecionando opção 'Pagar depois' via rádio...")
            
            try:
                page.get_by_role("radio", name="Sim").check(force=True)
            except Exception:
                page.locator("input[type='radio']").nth(1).click(force=True)
            
            # Pequena pausa para o modal abrir com segurança
            page.wait_for_timeout(1000)

            print("  -> Clicando no botão 'Entendi' do pop-up...")
            try:
                page.get_by_role("button", name="Entendi").click(timeout=5000, force=True)
                print("  -> Botão 'Entendi' clicado com sucesso!")
            except Exception as e:
                print(f"  -> Aviso ao clicar em 'Entendi': {e}")

            print("  -> Aceitando termos finais e finalizando...")
            
            try:
                page.locator("input[type='checkbox']").last.click(force=True)
            except Exception:
                pass
            
            # Finalizar Compra
            page.get_by_role("button", name="Finalizar compra").click(force=True)

            try:
                page.get_by_text("Pedido em andamento!", exact=False).wait_for(state="visible", timeout=15000)
                print("  ✅ TELA DE CONFIRMAÇÃO EXIBIDA COM SUCESSO!")
            except Exception:
                print("  ⚠️ Aviso: A tela de confirmação demorou a carregar, mas o fluxo prosseguiu.")
            
            page.wait_for_timeout(5000) 

        except Exception as e:
            print(f"  ❌ Erro crítico no fluxo: {str(e)}")

        context.close()
        browser.close()
        print("\n🔥 Teste ponta a ponta finalizado!")

if __name__ == "__main__":
    testar_curso_randomico()