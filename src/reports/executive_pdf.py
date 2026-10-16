"""Módulo de geração de parecer executivo em PDF de página única (One-Pager) via Typst."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import typst


class ExecutivePdfError(Exception):
    """Exceção levantada quando ocorre falha na compilação ou validação do relatório Typst."""

    pass


def _escape_typst(text: str) -> str:
    """Escapa caracteres com significado especial no conteúdo do Typst."""
    # Escapa barra invertida primeiro, depois delimitadores textuais do Typst
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("$", "\\$")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("@", "\\@")
    )


def _build_typst_content(scenario: dict[str, Any], risk_source: str | None = None) -> str:
    """Constrói o código fonte Typst inline para o One-Pager executivo."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Extração da fonte de risco (ML ou Heurística)
    resolved_source = str(scenario.get("risk_source", risk_source or "Heurística"))
    if resolved_source.startswith("ML") or resolved_source == "ML":
        risk_source_badge = "ML (τ\\* = 0.1549)"
        risk_source_detail = (
            "Modelo: LightGBM At-Purchase v1.0.0 · τ\\* calibrado = 0.1549 · Treinado em 2021–2024"
        )
        canc_display_kpi = "n/d (risco agregado no ML)"
    else:
        risk_source_badge = "Heurística"
        risk_source_detail = "Heurística calibrada (médias históricas + deltas de categoria/canal)"
        canc_display_kpi = None  # será preenchido após cálculo de canc_display

    # Extração e saneamento dos parâmetros de entrada
    unit_price = float(scenario.get("unit_price", 1200.0))
    unit_cost = float(scenario.get("unit_cost", 580.0))
    quantity = int(scenario.get("quantity", 50))
    discount_pct = float(scenario.get("discount_pct", 0.20))
    shipping_cost = float(scenario.get("shipping_cost", 25.0))
    tax_rate = float(scenario.get("tax_rate", 0.10))
    delivery_days = int(scenario.get("delivery_days", 4))
    reverse_logistics = float(scenario.get("reverse_logistics_cost", 45.0))
    category = _escape_typst(str(scenario.get("category", "Electronics")))
    channel = _escape_typst(str(scenario.get("channel", "Direct")))

    # Extração dos resultados computados
    gross_revenue = float(scenario.get("gross_revenue", unit_price * quantity))
    net_revenue = float(scenario.get("net_revenue", unit_price * (1.0 - discount_pct) * quantity))
    cm_val = float(scenario.get("contribution_margin_value", 0.0))
    cm_pct = float(scenario.get("contribution_margin_pct", 0.0))
    break_even = float(scenario.get("break_even_discount", 0.0))
    return_rate = float(scenario.get("estimated_return_rate", 0.0685))
    canc_rate = float(scenario.get("estimated_cancellation_rate", 0.0608))
    risk_alert = str(scenario.get("risk_alert", "SAFE_GREEN")).upper()

    # Formatações numéricas
    discount_display = f"{discount_pct * 100.0:.1f}%"
    break_even_display = f"{break_even * 100.0:.1f}%"
    diff_be = (break_even - discount_pct) * 100.0
    folga_display = f"{diff_be:+.1f}%"
    return_display = f"{return_rate * 100.0:.1f}%"
    canc_display = f"{canc_rate * 100.0:.1f}%"
    if canc_display_kpi is None:
        canc_display_kpi = f"{canc_display} Canc."

    # Definição do alerta e paleta semântica
    if "SAFE" in risk_alert or cm_val > 0 and diff_be >= 5.0:
        alert_title = "OPERAÇÃO FINANCEIRAMENTE SEGURA"
        alert_bg = "#f0fdf4"
        alert_border = "#22c55e"
        alert_text_color = "#15803d"
        alert_msg = (
            f"O desconto comercial concedido ({discount_display}) situa-se confortavelmente abaixo do "
            f"teto de break-even ({break_even_display}), com folga de {folga_display}. "
            f"A margem de contribuição de {cm_pct:.1f}% assegura rentabilidade e cobertura total de custos operacionais."
        )
    elif "WARN" in risk_alert or cm_val > 0 and diff_be < 5.0:
        alert_title = "ATENÇÃO À COMPRESSÃO DE MARGEM"
        alert_bg = "#fefce8"
        alert_border = "#eab308"
        alert_text_color = "#854d0e"
        alert_msg = (
            f"O desconto comercial ({discount_display}) aproxima a operação do teto de "
            f"equilíbrio ({break_even_display}), com folga reduzida a {folga_display}. "
            f"Margem de contribuição comprimida em {cm_pct:.1f}%. Recomenda-se travar novos incentivos."
        )
    else:
        alert_title = "DESTRUIÇÃO DE CAIXA DETECTADA"
        alert_bg = "#fef2f2"
        alert_border = "#ef4444"
        alert_text_color = "#b91c1c"
        alert_msg = (
            f"O desconto comercial ({discount_display}) ultrapassa o limite de break-even ({break_even_display}), "
            f"gerando déficit de {folga_display}. A operação destrói margem líquida a cada unidade faturada, "
            f"sendo deficitária antes mesmo de provisões extraordinárias."
        )

    # Recomendações dinâmicas
    rec_pricing = (
        f"Fixar alçada comercial com teto rígido em {min(break_even * 100.0, 35.0):.1f}% de desconto "
        f"para preservar margem líquida positiva neste lote."
    )
    if delivery_days <= 5:
        rec_logistics = (
            f"Prazo de entrega acordado ({delivery_days} dias) está dentro da zona de conformidade, "
            f"mantendo a devolução projetada controlada em {return_display}."
        )
    else:
        rec_logistics = (
            f"Prazo de {delivery_days} dias supera a janela ideal de 5 dias, elevando o risco de atrito "
            f"e elevando a taxa estimada de devolução para {return_display}."
        )

    rec_channel = (
        f"Canal {channel} e categoria {category} requerem acompanhamento de custos de logística "
        f"reversa fixados em USD {reverse_logistics:,.2f} por devolução."
    )

    # Código Typst estruturado em uma página A4
    return f"""
#set page(paper: "a4", margin: (x: 1.5cm, top: 1.5cm, bottom: 1.5cm))
#set text(font: "Liberation Sans", size: 9pt, fill: rgb("#0f172a"))

#grid(
  columns: (3fr, 2fr),
  gutter: 10pt,
  [
    #text(size: 15pt, weight: "bold", fill: rgb("#1e3a8a"))[Parecer Executivo de Cenário Comercial]
    #v(2pt)
    #text(size: 8.5pt, fill: rgb("#475569"))[E-Commerce Sales & Customer Analytics · Motor What-If]
    #v(2pt)
    #text(size: 8pt, fill: rgb("#64748b"))[Modo de inferência: *{risk_source_badge}* · {risk_source_detail}]
  ],
  align(right + top)[
    #text(size: 8pt, fill: rgb("#64748b"))[Emissão: {now_str}]
    #v(1pt)
    #text(size: 8pt, fill: rgb("#64748b"))[Ambiente: Produção (v1.0.0)]
    #v(1pt)
    #text(size: 8pt, weight: "bold", fill: rgb("#2563eb"))[Modo: {risk_source_badge}]
  ]
)

#v(4pt)
#line(length: 100%, stroke: 0.8pt + rgb("#2563eb"))
#v(6pt)

#text(size: 10.5pt, weight: "bold", fill: rgb("#1e293b"))[1. Parâmetros Operacionais do Lote]
#v(4pt)

#table(
  columns: (1.2fr, 1fr, 1.2fr, 1fr),
  stroke: 0.5pt + rgb("#e2e8f0"),
  fill: (col, row) => if row == 0 {{ rgb("#f8fafc") }} else {{ rgb("#ffffff") }},
  inset: 5.5pt,
  [#text(weight: "bold")[Parâmetro]], [#text(weight: "bold")[Valor]],
  [#text(weight: "bold")[Parâmetro]], [#text(weight: "bold")[Valor]],
  [Preço Base (Catálogo)], [USD {unit_price:,.2f}], [Desconto Concedido], [{discount_display}],
  [Custo do Produto (CMV)], [USD {unit_cost:,.2f}], [Volume Projetado], [{quantity} un.],
  [Frete Unitário Envio], [USD {shipping_cost:,.2f}], [Prazo Prometido], [{delivery_days} dias],
  [Categoria Comercial], [{category}], [Canal de Aquisição], [{channel}],
  [Alíquota Tributária], [{tax_rate * 100.0:.1f}%], [Logística Reversa Unit.], [USD {reverse_logistics:,.2f}]
)

#v(8pt)
#text(size: 10.5pt, weight: "bold", fill: rgb("#1e293b"))[2. Indicadores Consolidados de Performance (KPIs)]
#v(4pt)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 8pt,
  rect(width: 100%, inset: 8pt, radius: 4pt, fill: rgb("#f8fafc"), stroke: 0.8pt + rgb("#cbd5e1"))[
    #text(size: 7.5pt, fill: rgb("#64748b"))[RECEITA LÍQUIDA]
    #v(3pt)
    #text(size: 12.5pt, weight: "bold", fill: rgb("#0f172a"))[USD {net_revenue:,.2f}]
    #v(2pt)
    #text(size: 7.5pt, fill: rgb("#475569"))[Bruta: USD {gross_revenue:,.2f}]
  ],
  rect(width: 100%, inset: 8pt, radius: 4pt, fill: rgb("#f8fafc"), stroke: 0.8pt + rgb("#cbd5e1"))[
    #text(size: 7.5pt, fill: rgb("#64748b"))[MARGEM CONTRIBUIÇÃO]
    #v(3pt)
    #text(size: 12.5pt, weight: "bold", fill: rgb("{"#16a34a" if cm_val >= 0 else "#dc2626"}"))[USD {cm_val:,.2f}]
    #v(2pt)
    #text(size: 7.5pt, fill: rgb("{"#16a34a" if cm_val >= 0 else "#dc2626"}"))[{cm_pct:.1f}% da receita líquida]
  ],
  rect(width: 100%, inset: 8pt, radius: 4pt, fill: rgb("#f8fafc"), stroke: 0.8pt + rgb("#cbd5e1"))[
    #text(size: 7.5pt, fill: rgb("#64748b"))[BREAK-EVEN (D\\*)]
    #v(3pt)
    #text(size: 12.5pt, weight: "bold", fill: rgb("#2563eb"))[{break_even_display}]
    #v(2pt)
    #text(size: 7.5pt, fill: rgb("#2563eb"))[Folga de {folga_display}]
  ],
  rect(width: 100%, inset: 8pt, radius: 4pt, fill: rgb("#f8fafc"), stroke: 0.8pt + rgb("#cbd5e1"))[
    #text(size: 7.5pt, fill: rgb("#64748b"))[RISCO OPERACIONAL]
    #v(3pt)
    #text(size: 12.5pt, weight: "bold", fill: rgb("#d97706"))[{return_display} Dev.]
    #v(2pt)
    #text(size: 7.5pt, fill: rgb("#d97706"))[{canc_display_kpi}]
  ]
)

#v(8pt)
#text(size: 10.5pt, weight: "bold", fill: rgb("#1e293b"))[3. Parecer Sanitário de Risco e Rentabilidade]
#v(4pt)

#rect(width: 100%, inset: 8.5pt, radius: 4pt, fill: rgb("{alert_bg}"), stroke: 1pt + rgb("{alert_border}"))[
  #text(weight: "bold", fill: rgb("{alert_text_color}"))[{alert_title}]
  #v(2pt)
  #text(size: 8.5pt, fill: rgb("{alert_text_color}"))[
    {alert_msg}
  ]
]

#v(8pt)
#text(size: 10.5pt, weight: "bold", fill: rgb("#1e293b"))[4. Recomendações Estratégicas para o Decisor]
#v(3pt)

- *Alçada de Preço e Desconto:* {rec_pricing}
- *Logística e Nível de Serviço:* {rec_logistics}
- *Eficiência Comercial:* {rec_channel}

#v(1fr)
#line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
#v(3pt)
#align(center)[
  #text(size: 7.5pt, fill: rgb("#64748b"))[
    Base empírica: 138.116 transações comerciais (2021–2025) · Ticket Médio Histórico: USD 1.282,50 · Taxa Base de Devolução: 6,85% \\
    Documento de governança comercial para apoio à decisão executiva. Confidencial e restrito à diretoria de pricing e operações.
  ]
]
"""


def generate_executive_pdf(
    scenario: dict[str, Any], output_path: str | Path, risk_source: str | None = None
) -> Path:
    """Gera um parecer executivo em PDF (One-Pager) a partir dos dados do cenário simulado.

    Args:
        scenario: Dicionário contendo os parâmetros de entrada e KPIs da simulação.
        output_path: Caminho de destino para salvar o arquivo PDF.
        risk_source: Modo de inferência empregado ("Heurística" ou "ML"). Se None, extrai do dict.

    Returns:
        Path do arquivo PDF compilado.

    Raises:
        ExecutivePdfError: Caso a compilação via Typst falhe.
    """
    resolved_source = risk_source or str(scenario.get("risk_source", "Heurística"))
    dest = Path(output_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    try:
        typst_code = _build_typst_content(scenario, risk_source=resolved_source)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".typ", mode="w", encoding="utf-8", delete=False
        )
        temp_path = Path(temp_file.name)

        temp_file.write(typst_code)
        temp_file.flush()
        temp_file.close()

        typst.compile(str(temp_path), output=str(dest))

        if not dest.exists() or dest.stat().st_size == 0:
            raise ExecutivePdfError(f"O arquivo PDF de saída não foi gerado em {dest}")

        return dest

    except Exception as e:
        if isinstance(e, ExecutivePdfError):
            raise
        raise ExecutivePdfError(f"Falha na compilação do relatório executivo via Typst: {e}") from e

    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def generate_executive_pdf_bytes(scenario: dict[str, Any], risk_source: str | None = None) -> bytes:
    """Gera o parecer executivo em PDF e retorna diretamente os bytes compilados.

    Args:
        scenario: Dicionário contendo os parâmetros e resultados do cenário.
        risk_source: Modo de inferência empregado ("Heurística" ou "ML"). Se None, extrai do dict.

    Returns:
        Bytes brutos do documento PDF.

    Raises:
        ExecutivePdfError: Caso a compilação falhe.
    """
    resolved_source = risk_source or str(scenario.get("risk_source", "Heurística"))
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf_path = Path(tmp_pdf.name)

    try:
        generate_executive_pdf(scenario, tmp_pdf_path, risk_source=resolved_source)
        return tmp_pdf_path.read_bytes()
    finally:
        if tmp_pdf_path.exists():
            try:
                tmp_pdf_path.unlink()
            except OSError:
                pass
