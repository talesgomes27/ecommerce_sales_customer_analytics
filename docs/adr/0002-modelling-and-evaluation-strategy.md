# ADR 0002: Estratégia de Modelagem, Algoritmos Candidatos e Métricas de Avaliação

**Status:** Aprovado  
**Data:** 2026-10-16  
**Contexto Técnico:** Arquétipo A (Data Science, Analytics & ML)  

---

## Contexto e Problema
O projeto abrange três frentes analíticas complementares:
1. Segmentação comportamental de clientes (aprendizado não supervisionado).
2. Otimização de precificação, desconto e margem (análise econométrica e empírica).
3. Classificação de risco preventivo de cancelamento e devolução no checkout (*At-Purchase*).

Para a tarefa de classificação, há um desbalanceamento moderado a severo (taxas de 6,08% de cancelamento e 6,85% de devolução). A acurácia tradicional é enviesada pela classe majoritária (pedidos concluídos). Além disso, modelos de árvore baseados em `split` podem distorcer a real contribuição das features.

## Decisão Técnica
1. **Modelos Candidatos e Baselines:**
   - *Baseline Supervisionado:* Regressão Logística com regularização L2 e ponderação balanceada de classes (`class_weight='balanced'`).
   - *Modelos Avançados de Árvore:* LightGBM e XGBoost, explorando não-linearidades e interações entre ticket, canal, cupom e categoria.
   - *Segmentação Não Supervisionada:* K-Means com padronização robusta (`StandardScaler`/`RobustScaler`), número de clusters $K \in [3, 6]$ selecionado por Silhouette Score e Cotovelo, comparado a agrupamento hierárquico ou RFM quantílico.

2. **Métricas de Avaliação e Explicabilidade:**
   - *Métrica Primária de Classificação:* **PR-AUC (Precision-Recall Area Under Curve)**, medindo a capacidade do modelo em capturar devoluções/cancelamentos com alta precisão sob desbalanceamento.
   - *Métrica Secundária e Calibração:* **F1-Score ponderado por custo operacional**. O limiar $\tau^*$ de probabilidade de decisão será calibrado para minimizar o custo total de erro (falsos positivos vs. falsos negativos).
   - *Importância de Atributos:* Em conformidade obrigatória com o checklist Quarto, os modelos baseados em árvore reportarão importância de atributos estritamente por **`gain`** (`importance_type='gain'`), refletindo a redução real de erro gerada por cada quebra.

3. **Partição Temporal:**
   - Treino em 2021-2024 (110.518 pedidos) com validação interna *TimeSeriesSplit*.
   - Teste cego estrito em 2025 (27.598 pedidos), sem retreinamento no conjunto de teste.

## Consequências
- **Positivas:**
  - Avaliação não inflada por classes majoritárias.
  - Alinhamento entre custo de negócio e limiar de corte do classificador.
  - Explicabilidade transparente e alinhada à literatura sênior de machine learning.
- **Negativas / Trade-offs:**
  - O LightGBM e o XGBoost exigem tuning cuidadoso para evitar sobreajuste temporal em regimes macroeconômicos voláteis.
