# ADR 0003: Governança Editorial Quarto e Padrão Canônico de Storytelling

**Status:** Aprovado  
**Data:** 2026-10-16  
**Contexto Técnico:** Arquétipo A (Data Science, Analytics & ML)  

---

## Contexto e Problema
A apresentação de projetos analíticos corporativos frequentemente falha na separação entre código de exploração e narrativa executiva. Relatórios com gráficos mal alinhados, ausência de contexto de negócio ou tabelas numéricas desconexas das recomendações finais comprometem a credibilidade das análises.

Precisamos de uma convenção editorial rigorosa e automatizada para a geração do relatório final.

## Decisão Técnica
Adotamos o ecossistema Quarto CLI (`/opt/quarto/bin/quarto` ou `/usr/local/bin/quarto`) seguindo o documento de referência `quarto-quality-checklist.md`:

1. **Estrutura Canônica em 6 Seções (CRISP-ML(Q) + Storytelling):**
   - Seção 1: Contexto de Negócio & Hipóteses (*Business Understanding / Ask*)
   - Seção 2: Auditoria de Dados & Contratos (*Data Understanding / Prepare*)
   - Seção 3: Análise Exploratória & Engenharia de Atributos (*Data Prep & EDA / Process*)
   - Seção 4: Modelagem Estatística & Machine Learning (*Modeling / Construct*)
   - Seção 5: Avaliação, Diagnóstico & Explicabilidade (*Evaluation / Share*)
   - Seção 6: Recomendações Executivas & Plano de Ação (*Deployment / Act*)

2. **Configuração de Publicação (`_quarto.yml`):**
   - Idioma português: `lang: pt-BR` para títulos automáticos padronizados.
   - Cache de execução: `execute: freeze: auto` para blindar o relatório contra reexecuções desnecessárias de treinamento durante alterações estéticas.
   - Numeração: `number-sections: true` com títulos Markdown sem numeração manual no `.qmd`.

3. **Padrão Gráfico e Visual (Matplotlib / Seaborn):**
   - Subplots lado a lado gerados via painel único `fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)` com aplicação obrigatória de `ax.set_box_aspect(1)`.
   - Limpeza visual: aplicação de `sns.despine()` (remoção de eixos superior e direito) e exportação em 300 DPI.
   - Correspondência 1:1 rigorosa entre as perguntas norteadoras da Seção 1 e as figuras de diagnóstico das Seções 3 e 5.

## Consequências
- **Positivas:**
  - Relatório executivo profissional pronto para tomada de decisão pela diretoria.
  - Alinhamento pleno entre narrativa textual e dados visuais.
  - Reprodutibilidade completa via linha de comando (`quarto render`).
- **Negativas / Trade-offs:**
  - Exige rigor na formatação de figuras e controle estrito de sementes aleatórias.
