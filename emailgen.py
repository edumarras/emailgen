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

app = typer.Typer()

@app.command()
def serve():
    def run_ollama_serve():
        subprocess.Popen(["ollama", "serve"], shell=True)

    thread = threading.Thread(target=run_ollama_serve)
    thread.start()
    time.sleep(5)
    typer.echo("Servidor Ollama iniciado.")

@app.command()
def pull_model(model_name: str = "llama3"):
    try:
        result = subprocess.run(["ollama", "list"], text=True, capture_output=True, check=True, shell=True)
        if model_name.lower() in result.stdout.lower():
            typer.echo(f"Modelo {model_name} já está instalado.")
        else:
            typer.echo(f"Modelo {model_name} não encontrado. Baixando...")
            subprocess.run(["ollama", "pull", model_name], check=True, shell=True)
            typer.echo(f"Modelo {model_name} baixado com sucesso.")
    except subprocess.CalledProcessError as e:
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
    # Valores padrão para remetente e domínio caso não sejam declarados
    if not nome_remetente:
        nome_remetente = "Carlos Silva" if remetente_interno else "Atendimento"

    if not dominio_falso:
        dominio_falso = (empresa_remetente or empresa_alvo).lower().replace(" ", "") + ".com.br"

    email_remetente = f"{nome_remetente.lower().replace(' ', '.')}@{dominio_falso}"

    # Controla o foco da ação do email
    if tipo_acao == "link":
        acao = f"Acesse o link: {link_falso if link_falso else f'https://{dominio_falso}/atualizacao'}"
    elif tipo_acao == "anexo":
        acao = "Verifique as instruções no anexo."
    else:
        acao = "Responda este e-mail para confirmar seus dados."

    if not telefone_remetente:
        telefone_remetente = "(11) 91234-5678"
        
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
        # O 'input=prompt' envia o prompt gerado para a entrada padrão.
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

        # Formata o nome padrão do arquivo de saída
        nome_base = f"{dados.get('nome_colaborador', 'email')}_{dados.get('cenario', 'cenario')}".replace(" ", "_").replace("/", "_")
        caminho_saida = os.path.join(saida, f"{nome_base}.txt")
        caminho_meta = os.path.join(saida, f"{nome_base}.meta.json")

        # Passar argumentos de forma dinâmica a partir do JSON (CLIRUNNER)
        runner = CliRunner()
        # Cria uma lista a partir do JSON 
        args = ["gerar-email-teste-realista"] + sum([[
            f"--{k.replace('_', '-')}", str(v)
        ] if not isinstance(v, bool) else ([f"--{k.replace('_', '-')}"] if v else []) 
        for k, v in dados.items() if k not in ("assunto", "email_destinatario")], [])

        result = runner.invoke(app, args, catch_exceptions=False)

        # Corrige um errinho recorrente que estava acontecendo do tipo "realize a tarefa até 24h" para "realize a tarefa em até 24h", deixando o email mais realista
        conteudo_original = result.stdout
        conteudo_corrigido = re.sub(r"(?<!em ) até (\d{1,3} ?(h|minutos|dias))", r" em até \1", conteudo_original)

        with open(caminho_saida, "w", encoding="utf-8") as saida_txt:
            saida_txt.write(conteudo_corrigido)

        # Cria um arquivo de metadados (.meta.json) que armazena informações
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

            # O payload é o corpo da requisição JSON enviado para a API do GoPhish.
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

            response = requests.post(
                f"{gophish_url}/api/templates/",
                headers=headers,
                json=payload,
                verify=False # 'verify=False' desabilita a verificação do certificado SSL p/ testes no localhost
            )

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
    # robustez para encontrar o template correto no GoPhish
    # primeiro mapeamos todos os templates, para não perder algum
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

        # cada usuário é único, assim o envio do template também mira em um só alvo
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
            
            nome_grupo_gophish = f"Grupo_{titulo_campanha.replace(' ', '_')}"
            
            payload_novo_grupo = {"name": nome_grupo_gophish, "targets": [{"email": email_destinatario}]}
            requests.post(f"{gophish_url.rstrip('/')}/api/groups/", headers=headers_api, json=payload_novo_grupo, verify=ssl_verify)

            agora_utc_formatado = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

            # payload final para criar e lançar a campanha.
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

            # 'echo' muito útil para depuração - mostra o JSON exato
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
# executa tudo de uma vez, tem ainda um sleep pra deixar o gophish se preparar para continuar a execução
def full_run(
    entrada: str = typer.Argument("entrada", help="Diretório de entrada com os arquivos JSON."),
    saida: str = typer.Option("saida", help="Diretório de saída para e-mails e metadados."),
    api_key: str = typer.Option(..., help="Chave da API do GoPhish."),
    gophish_url: str = typer.Option("https://localhost:3333", help="URL da instância do GoPhish."),
    landing_page_name: str = typer.Option("Fake Page", help="Nome da Landing Page no GoPhish."),
    smtp_profile_name: str = typer.Option("Teste", help="Nome do Perfil de Envio (SMTP) no GoPhish."),
    campaign_url: str = typer.Option("http://phishing.example.com", help="URL de rastreamento para campanhas."),
):
    typer.echo("Iniciando execução completa do fluxo...")

    typer.echo("\n[ETAPA 1/3] Processando pasta de cenários para gerar os e-mails...")
    try:
        processar_pasta(entrada=entrada, saida=saida)
        typer.echo("Etapa 1 concluída com sucesso.")
    except typer.Exit as e:
        typer.echo(f"A Etapa 1 falhou e o script foi encerrado.")
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
