"""Motor de inferência e recalibração marginal do modelo supervisionado de risco."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.models.schemas import RiskScenarioInput


class RiskModelInference:
    """Adaptador de inferência para o LightGBM At-Purchase.

    Aplica as etapas obrigatórias de governança:
    1. pipeline.predict_proba() -> probabilidade na escala balanceada (class_weight="balanced")
    2. Fórmula de Elkan (com prevalência empírica pi) -> probabilidade calibrada na escala real
    3. Comparação com o limiar de custo ótimo recalibrado (tau_optimal_calibrated).
    """

    def __init__(self, model_dir: Path | str | None = None) -> None:
        """Inicializa o adaptador carregando os artefatos de modelo e metadados."""
        if model_dir is None:
            resolved_dir = Path("models")
            if not resolved_dir.exists():
                resolved_dir = Path(__file__).resolve().parent.parent.parent / "models"
            self.model_dir = resolved_dir
        else:
            self.model_dir = Path(model_dir)

        model_path = self.model_dir / "lightgbm_at_purchase.joblib"
        metadata_path = self.model_dir / "metadata.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Artefato de modelo não encontrado: {model_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Arquivo de metadados não encontrado: {metadata_path}")

        self.pipeline = joblib.load(model_path)
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        # Validações de sanidade do contrato de governança
        assert "tau_optimal_calibrated" in self.metadata, "metadata sem tau_optimal_calibrated"
        assert "base_rate_real" in self.metadata, "metadata sem base_rate_real"
        assert "numeric_cols" in self.metadata, "metadata sem numeric_cols"
        assert "categorical_cols" in self.metadata, "metadata sem categorical_cols"

        self.pi: float = float(self.metadata["base_rate_real"])
        self.tau_calibrated: float = float(self.metadata["tau_optimal_calibrated"])
        self.tau_balanced: float = float(self.metadata.get("tau_optimal_balanced", 0.55))
        self.numeric_cols: list[str] = list(self.metadata["numeric_cols"])
        self.categorical_cols: list[str] = list(self.metadata["categorical_cols"])

    def _calibrate_elkan(self, p_balanced: float) -> float:
        """Converte a probabilidade balanceada em probabilidade marginal real (Elkan, 2001)."""
        if p_balanced <= 0.0:
            return 0.0
        if p_balanced >= 1.0:
            return 1.0

        odds_bal = p_balanced / (1.0 - p_balanced)
        odds_real = odds_bal * (self.pi / (1.0 - self.pi))
        return odds_real / (1.0 + odds_real)

    def predict_risk(self, scenario: RiskScenarioInput) -> dict[str, Any]:
        """Gera a predição pontual calibrada e a recomendação de ação operacional.

        Args:
            scenario: Contrato validado contendo as features pontuais do pedido.

        Returns:
            Dicionário com probabilidades, limiar e decisão de política de crédito.
        """
        scenario.check_no_leakage()

        df = pd.DataFrame([scenario.model_dump()])
        df = df[self.numeric_cols + self.categorical_cols]

        p_bal = float(self.pipeline.predict_proba(df)[:, 1][0])
        p_cal = self._calibrate_elkan(p_bal)

        return {
            "prob_devolucao_calibrada": round(p_cal, 4),
            "prob_devolucao_balanceada": round(p_bal, 4),
            "decisao": "BLOQUEAR" if p_cal >= self.tau_calibrated else "LIBERAR",
            "tau_aplicado": self.tau_calibrated,
            "tau_balanceado": self.tau_balanced,
            "modo": "ML_LightGBM_Calibrado",
        }
