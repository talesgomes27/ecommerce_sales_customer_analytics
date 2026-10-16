"""Treinamento do classificador preventivo At-Purchase (Baseline vs. LightGBM)."""

import lightgbm as lgb
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    """Cria transformador de colunas com padronização e One-Hot Encoding."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_cols,
            ),
        ],
        remainder="drop",
    )


def train_baseline_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    numeric_cols: list[str],
    categorical_cols: list[str],
    random_state: int = 42,
) -> Pipeline:
    """Treina o modelo baseline (Regressão Logística com pesos balanceados)."""
    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    clf = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=random_state,
        solver="lbfgs",
    )
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", clf)])
    pipeline.fit(X_train, y_train)
    return pipeline


def train_lightgbm_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    numeric_cols: list[str],
    categorical_cols: list[str],
    random_state: int = 42,
    n_estimators: int = 150,
) -> tuple[Pipeline, pd.DataFrame]:
    """Treina o classificador LightGBM com importância de atributos por ganho real (gain).

    Args:
        X_train: Matriz de features At-Purchase de treino.
        y_train: Série alvo supervisionada.
        numeric_cols: Lista de colunas numéricas.
        categorical_cols: Lista de colunas categóricas.
        random_state: Semente para reprodutibilidade.
        n_estimators: Número de árvores.

    Returns:
        Tupla com (pipeline treinado, DataFrame com importância de features por gain).
    """
    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    preprocessor.fit(X_train)

    X_train_trans = preprocessor.transform(X_train)

    # Nomes das colunas pós-transformação
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_names = list(cat_encoder.get_feature_names_out(categorical_cols))
    all_feature_names = numeric_cols + cat_names

    clf = lgb.LGBMClassifier(
        class_weight="balanced",
        n_estimators=n_estimators,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        importance_type="gain",
        random_state=random_state,
        verbosity=-1,
    )
    clf.fit(X_train_trans, y_train)

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", clf)])

    importances = clf.feature_importances_
    importance_df = (
        pd.DataFrame(
            {
                "feature": all_feature_names,
                "gain_importance": importances,
            }
        )
        .sort_values(by="gain_importance", ascending=False)
        .reset_index(drop=True)
    )

    return pipeline, importance_df
