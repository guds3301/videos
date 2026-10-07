# Montar o ambiente local no Windows

Este guia roda no **seu computador**. A sessão na nuvem não alcança o seu Windows, o CapCut nem a sua pasta de vídeos, então a instalação é feita por você, com um script que pede confirmação antes de cada passo.

## O que o ambiente precisa
| Item | Para quê | Instalado pelo script? |
|---|---|---|
| Git | clonar o repositório e enviar alterações | sim, com confirmação (winget) |
| Python 3 | validador, render, testes | sim, com confirmação |
| FFmpeg + FFprobe | medir mídia e gerar vídeo de revisão | sim, com confirmação |
| jsonschema (pip) | validar `EDIT_PLAN.json` | sim, com confirmação |
| Node.js LTS | gráficos Remotion (mais tarde, opção `-WithNode`) | sim, com confirmação |
| CapCut Desktop | editor | **não**; instale em capcut.com |
| Claude Desktop | rodar o Claude Code localmente | **não**; instale você |

O script não mexe em chaves de API, não baixa mídia e não instala servidores MCP.

## Passos
1. **Clonar o repositório** (PowerShell):
   ```powershell
   cd $HOME\Documents
   git clone https://github.com/guds3301/videos.git
   cd videos
   git checkout main
   ```
   Se o Git ainda não estiver instalado, baixe em git-scm.com ou rode o passo 2 primeiro e depois volte.
2. **Verificar o ambiente** (só olha, não altera nada):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\fabrica-videos\setup\setup-windows.ps1
   ```
3. **Instalar o que faltar** (pergunta antes de cada item):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\fabrica-videos\setup\setup-windows.ps1 -Install
   ```
   Depois de instalar algo, **feche o PowerShell, abra outro** e rode de novo, para o PATH atualizar.
4. **Ler o resultado.** O script mostra uma tabela OK / MISSING / NOT FOUND, roda `workflow\probe_tools.py` e os 28 testes. Todos devem passar.
5. **Abrir no Claude Desktop:** aba Code, ambiente local, pasta `videos`. A partir daí o Claude lê e edita os arquivos do seu PC.
6. **CapCut:** instale, abra uma vez, crie um projeto curto (um clipe e um texto) e feche. Isso cria a pasta de rascunhos que o conversor vai usar.

## Comandos no Windows
Os guias usam `python3`; no Windows use `py -3`:
```powershell
py -3 fabrica-videos\timeline\validate_plan.py fabrica-videos\episodes\<slug>\EDIT_PLAN.json
py -3 -m unittest discover -s fabrica-videos\timeline\tests
py -3 -m unittest discover -s fabrica-videos\workflow\tests
```

## Limites conhecidos
- O script de instalação **não foi executado em Windows**: foi escrito e conferido na estrutura, mas nunca rodou numa máquina Windows. Se algum passo falhar, copie a mensagem de erro e me envie.
- No Windows, as fontes são procuradas em `C:\Windows\Fonts` e na pasta de fontes do usuário. Se Inter ou Cormorant Garamond não estiverem instaladas, o texto na tela é pulado e o relatório do render avisa.
- Pastas de rascunho do CapCut, caminho de mídia aceito por ele e comportamento ao escrever o rascunho com o app aberto precisam ser confirmados na sua versão.
- `capcut-kit` (matt-j-penny) é só para macOS e não deve ser instalado no Windows.
