# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-10-16

### Adicionado
- Estrutura completa de governança e contratos de dados sob o Arquétipo A (CRISP-ML(Q) + Data Storytelling).
- Módulo canônico de carregamento e tipagem determinística em `src/data/loader.py` com validação formal Pandera em `src/data/contracts.py`.
- Engenharia de atributos retroativos *point-in-time* (`src/features/builder.py`) blindada contra vazamento de dados (*data leakage*).
- Cálculo dinâmico de Recência, Frequência e Valor Monetário (`src/features/rfm.py`) com segmentação comportamental via K-Means ($K=4$, Silhouette 0,299).
- Análise empírica de sensibilidade e elasticidade de descontos (`src/models/pricing.py`), identificando o limiar crítico de destruição de margem $D^* = 35,93\%$.
- Pipeline preditivo At-Purchase com LightGBM (`src/models/train.py`), alcançando PR-AUC de 0,578 (lift de 4,47x sobre a taxa base) e ROC-AUC de 0,885 no teste cego temporal de 2025.
- Avaliação de custos operacionais com simulação de 9 limiares de decisão, identificando o ponto de custo mínimo global em $\tau^* = 0,55$ (economia líquida de \$92.495/ano).
- Teste de hipótese estatística via Mann-Whitney U ($p < 0,0001$, Cohen's $d = 1,19$) confirmando penalidade média de -0,53 estrelas por atraso na entrega.
- Gerador de figuras editoriais em alta resolução (300 DPI, `aspect=1`, `sns.despine`) em `src/evaluation/plots.py`.
- Módulo `src/evaluation/tables.py` com 10 tabelas executivas estilizadas via `great_tables`, integrando formatação tipada de moedas, porcentagens e realce condicional de perdas.
- Suíte automatizada com 26 testes unitários e de contratos contábeis passando em verde (`tests/`).
- Sumário de navegação retrátil (TOC Collapsible) com alternância fluida via script JavaScript e botão flutuante para liberação de tela cheia.
- Workflows de CI/CD para GitHub Actions com lint, testes e deploy automatizado no GitHub Pages.

### Alterado
- Reorganização das bases de dados locais na pasta canônica `data/raw/` e exclusão de rastreamento no Git para manter o repositório remoto enxuto e seguro.
- Adição de guardas de execução graciosa nos testes de contratos para permitir execuções em ambientes de CI sem a base bruta.
- Versionamento do diretório de cache `_freeze/` no Quarto para viabilizar compilação estática instantânea no GitHub Pages sem kernel em tempo de execução.

### Corrigido
- Substituição do diagrama Mermaid por infográfico editorial a 300 DPI (`fig_timeline_leakage.png`), eliminando problemas de contraste e legibilidade em navegadores.
- Eliminação do conflito de caracteres matemáticos no Markdown que provocava fusão de colunas monetárias e colunas fantasmas sem título nas tabelas.
