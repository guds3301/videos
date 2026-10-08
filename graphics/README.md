# Gráficos com Remotion

Gera diagramas, linhas de medida e cartões de capítulo como **clipes curtos com fundo transparente**. Eles entram no CapCut como camadas sobre a filmagem. O estilo segue `fabrica-videos/style/STYLE_GUIDE.md` (aço frio, núcleo quente).

## Três modelos
| Composição | Para quê |
|---|---|
| `ChapterTitle` | cartão de capítulo: número em âmbar, título em maiúsculas, linha que se desenha |
| `MeasureLine` | linha de medida com valor, para dar escala real à imagem |
| `ComponentDiagram` | diagrama de uma ideia só; os rótulos entram em etapas; marca "SIMPLIFIED MODEL" |

## Como funciona
1. Você (ou o Claude) escreve um arquivo de especificação em `specs/` (veja os três exemplos).
2. `node render_graphics.mjs` gera um `.mov` (ProRes 4444 com alfa) por especificação e um `manifest.json`.
3. `graphics_assets.py` transforma o manifesto em ativos do `EDIT_PLAN.json`, com caminhos relativos ao episódio.
4. O conversor para o CapCut coloca cada clipe na linha do tempo.

## Instalar e rodar (Windows)
Precisa do **Node.js LTS**. O script `fabrica-videos/setup/setup-windows.ps1 -WithNode -Install` oferece instalar.

```powershell
cd graphics
npm install
node render_graphics.mjs --stills
```
- `--stills` também grava um `.png` de um quadro do meio, para você ver o resultado sem abrir editor.
- `--only <id>` renderiza uma especificação só.
- `--format webm` gera WebM com alfa (VP9) no lugar do `.mov`.
- `--specs <pasta>` e `--out <pasta>` mudam de onde ler e onde gravar.
- Na primeira vez o Remotion baixa um navegador próprio (alguns minutos). Para usar um Chrome já instalado: `$env:REMOTION_BROWSER_EXECUTABLE="C:\caminho\chrome-headless-shell.exe"`. Ele exige o **headless shell**, não o Chrome comum.
- Ver ao vivo: `npm run studio` abre o Remotion Studio no navegador.

## Fonte
O texto usa Inter, se estiver instalada, e cai em Segoe UI, Arial ou DejaVu Sans. Instale Inter para o visual pretendido.

## Regras de conteúdo
- Um conceito por diagrama. Deixe um vão entre caixas maior que o texto da seta.
- Reconstrução ou modelo simplificado: mantenha `"illustrative": true` (o padrão do diagrama).
- Valores numéricos precisam vir de fonte verificada e constar no `sources.md` do episódio.

## O que foi testado e o que não foi
Testado em Linux: os três modelos renderizam, os `.mov` têm canal alfa, a duração em quadros e os 24 fps batem com a especificação, e o manifesto mescla renders parciais. O resultado visual foi conferido em quadros.
**Não testado:** importação desses `.mov` no CapCut (confirme que o alfa é reconhecido; se não for, use `--format webm` ou uma sequência PNG), renderização no Windows e a aparência com a fonte Inter.
