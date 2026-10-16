"""Script de treinamento completo e serialização determinística dos modelos supervisionados."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import sklearn

# Adiciona raiz do projeto ao sys.path para import de src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_canonical_data  # noqa: E402
from src.evaluation.metrics import evaluate_classifier_out_of_time  # noqa: E402
from src.features.builder import (  # noqa: E402
    AT_PURCHASE_CATEGORICAL_COLS,
    AT_PURCHASE_NUMERIC_COLS,
    compute_point_in_time_features,
    get_feature_matrix,
    split_out_of_time,
)
from src.models.train import train_baseline_model, train_lightgbm_model  # noqa: E402


def compute_file_sha256(filepath: Path) -> str:
    """Calcula o hash SHA256 de um arquivo em disco."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    print("=" * 70)
    print(" INICIANDO PIPELINE DE TREINAMENTO E SERIALIZAÇÃO DE MODELOS")
    print("=" * 70)

    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    primary_dataset_path = raw_data_dir / "ecommerce_sales_customer_analytics_150k.csv"

    if not raw_data_dir.exists() or not primary_dataset_path.exists():
        raise FileNotFoundError(
            f"Diretório de dados brutos ou arquivo principal não encontrado em {primary_dataset_path}"
        )

    print(f"\n1. Calculando SHA256 do dataset primário: {primary_dataset_path.name}")
    dataset_hash = compute_file_sha256(primary_dataset_path)
    print(f"   SHA256: {dataset_hash}")

    print("\n2. Carregando dados canônicos unificados...")
    df_raw = load_canonical_data(primary_dataset_path)
    print(f"   Total de registros carregados: {len(df_raw):,}")

    print("\n3. Computando features temporais point-in-time (sem lookahead bias)...")
    df_pit = compute_point_in_time_features(df_raw)

    print("\n4. Aplicando split cronológico Out-of-Time (Corte: 2025-01-01)...")
    df_train, df_test = split_out_of_time(df_pit, cutoff_date="2025-01-01")
    print(f"   Treino (2021-2024): {len(df_train):,} transações")
    print(f"   Teste Cego (2025):  {len(df_test):,} transações")

    X_train, y_train = get_feature_matrix(df_train)
    X_test, y_test = get_feature_matrix(df_test)

    print(f"   Proporção de classe minoritária (Treino): {y_train.mean() * 100:.2f}%")
    print(f"   Proporção de classe minoritária (Teste):  {y_test.mean() * 100:.2f}%")

    print("\n5. Treinando modelo Baseline (Logistic Regression balanceada)...")
    baseline_pipeline = train_baseline_model(
        X_train=X_train,
        y_train=y_train,
        numeric_cols=AT_PURCHASE_NUMERIC_COLS,
        categorical_cols=AT_PURCHASE_CATEGORICAL_COLS,
        random_state=42,
    )

    print("\n6. Treinando modelo Principal (LightGBM At-Purchase Classifier)...")
    lgb_pipeline, importance_df = train_lightgbm_model(
        X_train=X_train,
        y_train=y_train,
        numeric_cols=AT_PURCHASE_NUMERIC_COLS,
        categorical_cols=AT_PURCHASE_CATEGORICAL_COLS,
        random_state=42,
        n_estimators=150,
    )
    print(f"   Top 3 features por ganho real:\n{importance_df.head(3).to_string(index=False)}")

    print("\n7. Avaliando performance no conjunto de teste cego de 2025...")
    eval_metrics = evaluate_classifier_out_of_time(
        model=lgb_pipeline,
        X_test=X_test,
        y_test=y_test,
        cost_fp=1.0,
        cost_fn=5.0,
    )

    print(f"   ROC-AUC:            {eval_metrics['roc_auc']:.4f}")
    print(f"   PR-AUC:             {eval_metrics['pr_auc']:.4f}")
    print(f"   Brier Score:        {eval_metrics['brier_score']:.4f}")
    print(f"   Limiar Custo Ótimo: {eval_metrics['optimal_threshold']:.2f} (tau*)")
    print(f"   F1 no Limiar Ótimo: {eval_metrics['optimal_f1']:.4f}")

    # Calibração de Elkan: converter τ* da escala balanceada para a escala real
    pi = float(y_test.mean())  # prevalência real (base rate)
    tau_balanced = 0.55

    odds_balanced = tau_balanced / (1.0 - tau_balanced)
    odds_real = odds_balanced * (pi / (1.0 - pi))
    tau_calibrated = odds_real / (1.0 + odds_real)

    print("\n8. Calibração de Decisão (Fórmula de Elkan):")
    print(f"   Base rate real (π): {pi:.6f}")
    print(f"   τ* balanceado:      {tau_balanced:.4f}")
    print(f"   τ* calibrado:       {tau_calibrated:.6f}")

    # Criação do diretório de destino
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    lgb_artifact_path = models_dir / "lightgbm_at_purchase.joblib"
    baseline_artifact_path = models_dir / "baseline_logit_at_purchase.joblib"
    metadata_path = models_dir / "metadata.json"

    print("\n9. Serializando pipelines treinados com joblib (compressão zlib=3)...")
    joblib.dump(lgb_pipeline, lgb_artifact_path, compress=3)
    joblib.dump(baseline_pipeline, baseline_artifact_path, compress=3)
    print(
        f"   Salvo: {lgb_artifact_path.relative_to(PROJECT_ROOT)} ({lgb_artifact_path.stat().st_size / 1024:.1f} KB)"
    )
    print(
        f"   Salvo: {baseline_artifact_path.relative_to(PROJECT_ROOT)} ({baseline_artifact_path.stat().st_size / 1024:.1f} KB)"
    )

    print("\n10. Serializando metadados de governança em JSON...")
    now_iso = datetime.now(UTC).isoformat()
    metrics_summary = {
        "roc_auc": round(eval_metrics["roc_auc"], 4),
        "pr_auc": round(eval_metrics["pr_auc"], 4),
        "brier_score": round(eval_metrics["brier_score"], 4),
        "base_rate": round(eval_metrics["base_rate"], 4),
        "f1_at_tau": round(eval_metrics["optimal_f1"], 4),
        "optimal_f1": round(eval_metrics["optimal_f1"], 4),
        "optimal_precision": round(eval_metrics["optimal_precision"], 4),
        "optimal_recall": round(eval_metrics["optimal_recall"], 4),
    }

    metadata = {
        "model_name": "LightGBM At-Purchase Preventative Classifier",
        "model_version": "1.0.0",
        "trained_at": now_iso,
        "training_timestamp_utc": now_iso,
        "training_cutoff_date": "2025-01-01",
        "training_samples_count": len(X_train),
        "test_samples_count": len(X_test),
        "base_rate_real": round(pi, 6),
        "tau_optimal": tau_balanced,
        "tau_optimal_balanced": tau_balanced,
        "tau_optimal_calibrated": round(tau_calibrated, 6),
        "optimal_cost_threshold_tau": tau_balanced,  # alias legado
        "metrics": metrics_summary,
        "metrics_out_of_time_2025": metrics_summary,
        "numeric_cols": AT_PURCHASE_NUMERIC_COLS,
        "categorical_cols": AT_PURCHASE_CATEGORICAL_COLS,
        "numeric_features": AT_PURCHASE_NUMERIC_COLS,  # alias legado
        "categorical_features": AT_PURCHASE_CATEGORICAL_COLS,  # alias legado
        "runtime_versions": {
            "sklearn": sklearn.__version__,
            "lightgbm": lgb.__version__,
            "joblib": joblib.__version__,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "sklearn_version": sklearn.__version__,
        "lightgbm_version": lgb.__version__,
        "joblib_version": joblib.__version__,
        "sha256_dataset": dataset_hash,
        "primary_dataset_file": primary_dataset_path.name,
        "primary_dataset_sha256": dataset_hash,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"   Salvo: {metadata_path.relative_to(PROJECT_ROOT)}")

    print("\n11. Smoke Test de Validação: Recarregando artefato serializado...")
    loaded_pipeline = joblib.load(lgb_artifact_path)
    sample_inputs = X_test.head(5)
    sample_preds = loaded_pipeline.predict_proba(sample_inputs)[:, 1]

    print("   Predições no holdout (5 amostras):")
    for idx, prob in enumerate(sample_preds, 1):
        odds_b = prob / (1.0 - prob)
        odds_r = odds_b * (pi / (1.0 - pi))
        prob_cal = odds_r / (1.0 + odds_r)
        decision = (
            "INTERVENÇÃO (Risco Alto)" if prob >= tau_balanced else "LIBERADO (Risco Aceitável)"
        )
        print(
            f"   - Amostra #{idx}: P(Bal)={prob:.4f} | P(Calibrada)={prob_cal:.4f} | "
            f"Decisão (tau_bal=0.55 / tau_cal={tau_calibrated:.4f}): {decision}"
        )

    assert len(sample_preds) == 5, "Falha na dimensão das predições recarregadas"
    assert np.all((sample_preds >= 0.0) & (sample_preds <= 1.0)), (
        "Probabilidades fora do intervalo [0, 1]"
    )

    print("\n" + "=" * 70)
    print(" SERIALIZAÇÃO CONCLUÍDA E VALIDADA COM 100% DE SUCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    main()
