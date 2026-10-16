"""Testes unitários para geração e formatação de tabelas via great_tables."""

from great_tables import GT

from src.evaluation.tables import (
    table_category_performance,
    table_discount_buckets,
    table_marketing_performance,
    table_methodology,
    table_model_evaluation,
    table_returns_root_cause,
    table_rfm_segments,
    table_roadmap,
    table_threshold_costs,
    table_yearly_summary,
)


def test_table_yearly_summary() -> None:
    gt = table_yearly_summary()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Faturamento Líquido" in html
    assert "Lucro Operacional" in html
    assert "2021" in html
    assert "Total" in html


def test_table_methodology() -> None:
    gt = table_methodology()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Pré-Código" in html
    assert "Gate 1: Data Discovery" in html


def test_table_discount_buckets() -> None:
    gt = table_discount_buckets()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "0% a 10%" in html
    assert "55% a 60%" in html


def test_table_marketing_performance() -> None:
    gt = table_marketing_performance()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Organic Search" in html
    assert "Google Ads" in html


def test_table_rfm_segments() -> None:
    gt = table_rfm_segments()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Champions" in html
    assert "At-Risk High-Value" in html


def test_table_category_performance() -> None:
    gt = table_category_performance()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Electronics" in html
    assert "Books" in html


def test_table_model_evaluation() -> None:
    gt = table_model_evaluation()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "LightGBM At-Purchase" in html
    assert "PR-AUC" in html


def test_table_threshold_costs() -> None:
    gt = table_threshold_costs()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Mínimo Global de Custo" in html
    assert "69,415.00" in html or "69.415,00" in html


def test_table_returns_root_cause() -> None:
    gt = table_returns_root_cause()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Wrong Product" in html
    assert "425,790.00" in html or "425.790,00" in html


def test_table_roadmap() -> None:
    gt = table_roadmap()
    assert isinstance(gt, GT)
    html = gt.as_raw_html()
    assert "Q1" in html
    assert "Pricing" in html
