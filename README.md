# Gerador de Campanhas de Phishing Educacional com IA + GoPhish

Ferramenta em Python que gera e-mails de phishing realistas com IA (via Ollama + LLaMA3) e automatiza a criação de campanhas no GoPhish.

## Funcionalidades
- Geração de e-mails com IA usando o modelo LLaMA3
- Processamento em lote de arquivos JSON com cenários
- Criação automática de templates e campanhas no GoPhish

## Requisitos
- Python 3.8+
- Ollama instalado com o modelo `llama3`
- Instância do GoPhish com API habilitada
- `pip install typer requests`

## Uso
1. Coloque os arquivos `.json` na pasta `entrada/`
2. Execute o comando principal:

python script.py full-run --api-key SUA_API_KEY

## Exemplo de JSON para a pasta 'Entrada'

{
  "empresa_alvo": "Tech Solutions",
  "nome_colaborador": "Mariana Souza",
  "cenario": "Solicitação urgente de atualização de credenciais",
  "nivel_sofisticacao": 4,
  "tipo_acao": "link",
  "link_falso": "https://techsolutions-login.com/atualizacao",
  "remetente_interno": true,
  "nome_remetente": "Carlos Oliveira",
  "departamento_remetente": "Tecnologia da Informação",
  "dominio_falso": "techsolutions.com",
  "empresa_remetente": "Tech Solutions",
  "telefone_remetente": "(11) 98765-4321",
  "assunto": "Atualização obrigatória de sistema",
  "email_destinatario": "mariana.souza@techsolutions.com"
}
