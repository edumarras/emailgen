import typer
import subprocess
import threading
import time
import os
import json
import requests
import re
import unicodedata
from typing import Optional
from datetime import datetime, timezone
from typer.testing import CliRunner

# app é nossa aplicação de linha de comando, criada com o Typer.
app = typer.Typer()

@app.command()
def serve():
    """Inicia o servidor Ollama em segundo plano."""
    def run_ollama_serve():
        # Usamos Popen para que o servidor Ollama rode sem travar este script.
        subprocess.Popen(["ollama", "serve"], shell=True)

    # Colocamos o servidor em uma thread separada para que ele continue rodando em background.
    thread = threading.Thread(target=run_ollama_serve)
    thread.start()
    
    # É uma boa prática esperar um pouco para garantir que o servidor esteja pronto.
    typer.echo("Aguardando 5 segundos para o servidor Ollama iniciar...")
    time.sleep(5)
    typer.echo("Servidor Ollama iniciado.")

@app.command()
def pull_model(model_name: str = "llama3"):
    """Verifica se um modelo já existe e o baixa se necessário."""
    try:
        # Primeiro, listamos os modelos já instalados para não baixar de novo sem necessidade.
        result = subprocess.run(["ollama", "list"], text=True, capture_output=True, check=True, shell=True)
        
        if model_name.lower() in result.stdout.lower():
            typer.echo(f"Modelo '{model_name}' já está instalado.")
        else:
            # Se não estiver na lista, iniciamos o download.
            typer.echo(f"Modelo '{model_name}' não encontrado. Baixando...")
            subprocess.run(["ollama", "pull", model_name], check=True, shell=True)
            typer.echo(f"Modelo '{model_name}' baixado com sucesso.")
    except subprocess.CalledProcessError as e:
        # Captura erros caso o comando 'ollama' falhe.
        typer.echo(f"Erro ao verificar ou puxar modelo: {e}")

@app.command()
def gerar_email_teste_realista(
    empresa_alvo: str = typer.Option(..., help="Nome da empresa alvo"),
    nome_colaborador: str = typer.Option(..., help="Nome do colaborador alvo"),
    cenario: str = typer.Option(..., help="Cenário do e-mail"),
    nivel_sofisticacao: int = typer.Option(5, help="Nível de sofisticação (1-5)"),
    tipo_acao: str = typer.Option("link", help="Tipo de ação (link, anexo, resposta)"),
    link_falso: Optional[str] = typer.Option(None, help="Link falso de phishing"),
    remetente_interno: bool = typer.Option(False, help="Se o remetente é interno"),
    nome_remetente: Optional[str] = typer.Option(None, help="Nome do remetente"),
    departamento_remetente: Optional[str] = typer.Option("Tecnologia da Informação", help="Departamento do remetente"),
    dominio_falso: Optional[str] = typer.Option(None, help="Domínio falso de e-mail"),
    empresa_remetente: Optional[str] = typer.Option(None, help="Nome da empresa remetente"),
    telefone_remetente: Optional[str] = typer.Option(None, help="Telefone para assinatura")
):
    """Gera o corpo de um e-mail de phishing usando o modelo de linguagem."""
    # Se alguns dados não forem fornecidos, usamos valores padrão para preencher.
    if not nome_remetente:
        nome_remetente = "Carlos Silva" if remetente_interno else "Atendimento"

    if not dominio_falso:
        dominio_falso = (empresa_remetente or empresa_alvo).lower().replace(" ", "") + ".com.br"

    email_remetente = f"{nome_remetente.lower().replace(' ', '.')}@{dominio_falso}"

    # Monta a frase de "chamada para ação" dependendo do tipo de teste.
    if tipo_acao == "link":
        acao = f"Acesse o link: {link_falso if link_falso else f'https://{dominio_falso}/atualizacao'}"
    elif tipo_acao == "anexo":
        acao = "Verifique as instruções no anexo."
    else:
        acao = "Responda este e-mail para confirmar seus dados."

    if not telefone_remetente:
        telefone_remetente = "(11) 91234-5678"
        
    # Existem dois modelos de prompt: um para e-mails internos e outro para externos.
    # Isso ajuda a IA a ajustar o tom da mensagem.
    if remetente_interno:
        prompt = f"""
Escreva um e-mail interno corporativo em português brasileiro, com base nas informações abaixo.

**Instruções:**
- Tom formal, neutro e objetivo.
- Use apenas palavras claras e comuns no ambiente de trabalho.
- Evite floreios, elogios ou tom de imposição.
- Utilize frases educadas como: "solicitamos que você acesse", "recomendamos que realize", etc.
- Escreva diretamente o corpo do e-mail (não inclua título nem assunto).
- Finalize com uma assinatura profissional (nome, departamento, telefone e e-mail do remetente).

**Dados:**
Empresa: {empresa_alvo}
Colaborador: {nome_colaborador}
Cenário: {cenario}
Ação esperada: {acao}
Departamento: {departamento_remetente}
Telefone do remetente: {telefone_remetente}
E-mail do remetente: {email_remetente}

**Formato esperado:**

Prezado(a) [Nome do Colaborador],

[Corpo do e-mail]

Atenciosamente,  
[Departamento]  
[Empresa]  
Telefone: [Telefone]  
E-mail: [E-mail]
"""
    else:
        prompt = f"""
Escreva um e-mail formal-comercial em português brasileiro com base nas informações abaixo.

**Instruções:**
- Tom profissional e direto, como o de uma empresa parceira.
- Use linguagem educada, sem bajulações ou alarmismo.
- Pode incluir leve urgência: "confirme até 24h", "evite bloqueio", etc.
- Escreva apenas o corpo do e-mail (não inclua título ou assunto).
- Não fale 'aqui está o corpo do email' ou algo do tipo
- Use um vocabulário inteligente e realista, priorize palavras comuns e vocabulário comum.
- Finalize com uma assinatura corporativa (nome, empresa, departamento, telefone e e-mail do remetente).

**Dados:**
Empresa destino: {empresa_alvo}
Colaborador: {nome_colaborador}
Empresa remetente: {empresa_remetente if empresa_remetente else empresa_alvo}
Cenário: {cenario}
Ação esperada: {acao}
Departamento: {departamento_remetente}
Telefone do remetente: {telefone_remetente}
E-mail do remetente: {email_remetente}

**Formato esperado:**

Prezado(a) [Nome do Colaborador],

[Corpo do e-mail]

Atenciosamente,  
[Empresa Remetente] - [Departamento]  
Telefone: [Telefone]  
E-mail: [E-mail]
"""
        
    try:
        # Enviamos o prompt para o modelo Llama3 e capturamos a resposta.
        # O encoding='utf-8' é importante para não ter problemas com acentos.
        cmd = ["ollama", "run", "llama3"]
        resultado = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            shell=True,
            encoding="utf-8"
        )
        typer.echo(resultado.stdout)
    except Exception as e:
        typer.echo(f"Erro ao gerar e-mail: {e}")

@app.command()
def processar_pasta(
    entrada: str = typer.Argument(..., help="Diretório contendo arquivos JSON"),
    saida: str = typer.Argument(..., help="Diretório para salvar os e-mails gerados")
):
    """Lê arquivos JSON de uma pasta e gera um e-mail para cada um."""
    if not os.path.isdir(entrada):
        typer.echo(f"Pasta de entrada '{entrada}' não existe.")
        raise typer.Exit(code=1)

    os.makedirs(saida, exist_ok=True)

    arquivos = [f for f in os.listdir(entrada) if f.endswith(".json")]

    if not arquivos:
        typer.echo("Nenhum arquivo JSON encontrado.")
        raise typer.Exit(code=1)

    for arquivo in arquivos:
        caminho = os.path.join(entrada, arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        nome_base = f"{dados.get('nome_colaborador', 'email')}_{dados.get('cenario', 'cenario')}".replace(" ", "_").replace("/", "_")
        caminho_saida = os.path.join(saida, f"{nome_base}.txt")
        caminho_meta = os.path.join(saida, f"{nome_base}.meta.json")

        # Em vez de duplicar a lógica, usamos o CliRunner para chamar nosso próprio comando
        # 'gerar-email-teste-realista', passando os dados do JSON como argumentos.
        # Isso mantém o código mais limpo e fácil de manter.
        runner = CliRunner()
        args = ["gerar-email-teste-realista"] + sum([[
            f"--{k.replace('_', '-')}", str(v)
        ] if not isinstance(v, bool) else ([f"--{k.replace('_', '-')}"] if v else [])  
        for k, v in dados.items() if k not in ("assunto", "email_destinatario")], [])

        result = runner.invoke(app, args, catch_exceptions=False)

        # A IA às vezes gera uma gramática um pouco estranha. Esta linha corrige uma
        # pequena inconsistência para o texto soar mais natural.
        conteudo_original = result.stdout
        conteudo_corrigido = re.sub(r"(?<!em ) até (\d{1,3} ?(h|minutos|dias))", r" em até \1", conteudo_original)

        with open(caminho_saida, "w", encoding="utf-8") as saida_txt:
            saida_txt.write(conteudo_corrigido)

        # Guardamos informações importantes (como assunto e destinatário) em um arquivo de metadados.
        # Isso facilita o trabalho na hora de criar as campanhas no GoPhish.
        with open(caminho_meta, "w", encoding="utf-8") as meta_json:
            json.dump({
                "assunto": dados["assunto"],
                "titulo": nome_base.replace("_", " ").title(),
                "email_destinatario": dados["email_destinatario"]
            }, meta_json, ensure_ascii=False, indent=2)

        typer.echo(f"Gerado: {caminho_saida}")

@app.command()
def launch_template(
    saida: str = typer.Option("saida", help="Pasta com arquivos de saída"),
    api_key: str = typer.Option(..., help="Chave da API do GoPhish"),
    gophish_url: str = typer.Option("https://localhost:3333", help="URL da API do GoPhish")
):
    """Envia os e-mails gerados para o GoPhish como templates."""
    if not os.path.isdir(saida):
        typer.echo(f"Pasta '{saida}' não encontrada.")
        raise typer.Exit(code=1)

    arquivos_txt = [f for f in os.listdir(saida) if f.endswith(".txt")]

    for arquivo_txt in arquivos_txt:
        base = os.path.splitext(arquivo_txt)[0]
        caminho_txt = os.path.join(saida, arquivo_txt)
        caminho_meta = os.path.join(saida, f"{base}.meta.json")

        if not os.path.isfile(caminho_meta):
            typer.echo(f"Metadado ausente para {arquivo_txt}. Pulando...")
            continue

        try:
            with open(caminho_txt, "r", encoding="utf-8") as f_txt:
                corpo_html = f_txt.read()
            with open(caminho_meta, "r", encoding="utf-8") as f_meta:
                meta = json.load(f_meta)

            # O 'payload' é o corpo da requisição, formatado como a API do GoPhish espera.
            payload = {
                "name": meta.get("titulo", base.title()),
                "subject": meta.get("assunto", "Assunto padrão"),
                "html": corpo_html,
                "text": "",
                "attachments": []
            }

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            # 'verify=False' desabilita a verificação de certificado SSL.
            # É útil para testes em localhost, mas deve ser ativado em produção.
            response = requests.post(
                f"{gophish_url}/api/templates/",
                headers=headers,
                json=payload,
                verify=False
            )

            # O status 201 (Created) confirma que o template foi criado com sucesso.
            if response.status_code == 201:
                typer.echo(f"Enviado: {payload['name']}")
            else:
                typer.echo(f"[{response.status_code}] {payload['name']}: {response.text}")

        except Exception as e:
            typer.echo(f"Erro com '{arquivo_txt}': {e}")

@app.command()
def create_campaigns(
    saida: str = typer.Option("saida", help="Pasta com arquivos de saída (.meta.json)"),
    api_key: str = typer.Option(..., help="Chave da API do GoPhish"),
    gophish_url: str = typer.Option("https://localhost:3333", help="URL da API do GoPhish"),
    smtp_profile_name: str = typer.Option("Primary SMTP", help="Nome do perfil SMTP a ser usado no GoPhish."),
    landing_page_name: str = typer.Option("Default", help="Nome da Landing Page a ser usada no GoPhish."),
    campaign_url: str = typer.Option("http://phishing.example.com", help="URL base para rastreamento da campanha")
):
    """Cria e lança as campanhas no GoPhish."""
    # Função auxiliar para "limpar" os nomes, removendo acentos e espaços.
    # Isso ajuda a evitar erros ao comparar nomes de templates.
    def normalizar(texto):
        if not texto: return ""
        texto = texto.lower().strip()
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto

    if not os.path.isdir(saida):
        typer.echo(f"Pasta de saída '{saida}' não encontrada.")
        raise typer.Exit(code=1)

    headers_api = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    ssl_verify = not ("localhost" in gophish_url or "127.0.0.1" in gophish_url)

    try:
        # Primeiro, buscamos todos os templates que já existem no GoPhish
        # para garantir que vamos usar o nome correto na hora de criar a campanha.
        templates_resp = requests.get(f"{gophish_url.rstrip('/')}/api/templates/", headers=headers_api, verify=ssl_verify)
        templates_resp.raise_for_status()
        gophish_templates = templates_resp.json()
        map_templates_normalizados = {normalizar(t["name"]): t["name"] for t in gophish_templates}
    except requests.exceptions.RequestException as e:
        typer.echo(f"Erro ao conectar com GoPhish ou buscar templates: {e}")
        raise typer.Exit(code=1)

    arquivos_meta_json = [f for f in os.listdir(saida) if f.endswith(".meta.json")]
    if not arquivos_meta_json:
        typer.echo(f"Nenhum arquivo .meta.json encontrado na pasta '{saida}'.")
        return

    typer.echo(f"Usando Perfil SMTP: '{smtp_profile_name}'")
    typer.echo(f"Usando Landing Page: '{landing_page_name}'")

    for meta_json_nome in arquivos_meta_json:
        caminho_meta_json = os.path.join(saida, meta_json_nome)

        try:
            with open(caminho_meta_json, "r", encoding="utf-8") as f_meta:
                metadados = json.load(f_meta)

            titulo_campanha = metadados.get("titulo")
            email_destinatario = metadados.get("email_destinatario")

            if not titulo_campanha or not email_destinatario:
                typer.echo(f"Metadados incompletos em {meta_json_nome}. Pulando...")
                continue

            nome_real_template = map_templates_normalizados.get(normalizar(titulo_campanha))
            if not nome_real_template:
                typer.echo(f"Template '{titulo_campanha}' não encontrado no GoPhish. Pulando.")
                continue
            
            # Para cada alvo, criamos um grupo específico no GoPhish.
            # Isso nos permite lançar uma campanha individual para cada e-mail gerado.
            nome_grupo_gophish = f"Grupo_{titulo_campanha.replace(' ', '_')}"
            
            payload_novo_grupo = {"name": nome_grupo_gophish, "targets": [{"email": email_destinatario}]}
            requests.post(f"{gophish_url.rstrip('/')}/api/groups/", headers=headers_api, json=payload_novo_grupo, verify=ssl_verify)

            # A API do GoPhish exige a data de lançamento em formato UTC (com 'Z' no final).
            agora_utc_formatado = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

            # Este é o payload final para criar e lançar a campanha.
            payload_campanha = {
                "name": titulo_campanha,
                "template": {"name": nome_real_template},
                "groups": [{"name": nome_grupo_gophish}],
                "page": {"name": landing_page_name},
                "smtp": {"name": smtp_profile_name},
                "url": campaign_url,
                "launch_date": agora_utc_formatado,
                "send_by_date": None,
            }

            # Imprimir o JSON que será enviado é uma ótima forma de depurar problemas.
            typer.echo(f"\nEnviando JSON para campanha '{titulo_campanha}':")
            typer.echo(json.dumps(payload_campanha, indent=2, ensure_ascii=False))

            campaign_resp = requests.post(
                f"{gophish_url.rstrip('/')}/api/campaigns/",
                headers=headers_api,
                json=payload_campanha,
                verify=ssl_verify
            )

            if campaign_resp.status_code == 201:
                typer.echo(f"Sucesso! Campanha '{titulo_campanha}' criada.")
            else:
                typer.echo(f"Erro ao criar campanha '{titulo_campanha}'. Status: {campaign_resp.status_code}")
                try:
                    typer.echo(f"Resposta do GoPhish: {campaign_resp.json()}")
                except json.JSONDecodeError:
                    typer.echo(f"Resposta do GoPhish (texto): {campaign_resp.text}")

        except Exception as e:
            typer.echo(f"Erro inesperado ao processar campanha para {meta_json_nome}: {e}")

@app.command()
def full_run(
    entrada: str = typer.Argument("entrada", help="Diretório de entrada com os arquivos JSON."),
    saida: str = typer.Option("saida", help="Diretório de saída para e-mails e metadados."),
    api_key: str = typer.Option(..., help="Chave da API do GoPhish."),
    gophish_url: str = typer.Option("https://localhost:3333", help="URL da instância do GoPhish."),
    landing_page_name: str = typer.Option("Fake Page", help="Nome da Landing Page no GoPhish."),
    smtp_profile_name: str = typer.Option("Teste", help="Nome do Perfil de Envio (SMTP) no GoPhish."),
    campaign_url: str = typer.Option("http://phishing.example.com", help="URL de rastreamento para campanhas."),
):
    """Executa o fluxo completo: gerar e-mails, enviar templates e criar campanhas."""
    typer.echo("Iniciando execução completa do fluxo...")

    typer.echo("\n[ETAPA 1/3] Processando pasta de cenários para gerar os e-mails...")
    try:
        processar_pasta(entrada=entrada, saida=saida)
        typer.echo("Etapa 1 concluída com sucesso.")
    except typer.Exit as e:
        typer.echo("A Etapa 1 falhou e o script foi encerrado.")
        raise e
    except Exception as e:
        typer.echo(f"Erro inesperado na Etapa 1 (processar_pasta): {e}")
        raise typer.Exit(code=1)

    typer.echo("\n[ETAPA 2/3] Enviando os templates de e-mail para o GoPhish...")
    try:
        launch_template(
            saida=saida,
            api_key=api_key,
            gophish_url=gophish_url
        )
        typer.echo("Etapa 2 concluída com sucesso.")
    except Exception as e:
        typer.echo(f"Erro inesperado na Etapa 2 (launch_template): {e}")
        raise typer.Exit(code=1)
        
    # É bom dar um pequeno tempo para o GoPhish processar os novos templates
    # antes de tentarmos usá-los para criar uma campanha.
    typer.echo("Aguardando 3 segundos para o GoPhish registrar os templates...")
    time.sleep(3)

    typer.echo("\n[ETAPA 3/3] Criando e lançando as campanhas no GoPhish...")
    try:
        create_campaigns(
            saida=saida,
            api_key=api_key,
            gophish_url=gophish_url,
            smtp_profile_name=smtp_profile_name,
            landing_page_name=landing_page_name,
            campaign_url=campaign_url
        )
        typer.echo("Etapa 3 concluída com sucesso.")
    except Exception as e:
        typer.echo(f"Erro inesperado na Etapa 3 (create_campaigns): {e}")
        raise typer.Exit(code=1)

    typer.echo("\nFluxo completo finalizado com sucesso.")

if __name__ == "__main__":
    app()
