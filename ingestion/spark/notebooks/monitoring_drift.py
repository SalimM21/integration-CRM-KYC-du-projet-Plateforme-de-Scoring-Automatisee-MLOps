# %% [markdown]
# # Monitoring Qualité et Drift Data
# Notebook pour analyser la dérive des données via Evidently AI

# %%
import pandas as pd
from pyspark.sql import SparkSession
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection
from pyspark.sql.functions import col

# %%
# Spark session
spark = SparkSession.builder \
    .appName("Monitoring_Data_Drift") \
    .getOrCreate()

# %%
# Charger le dataset actuel depuis Delta ou CSV
current_df = spark.read.format("delta").load("/delta/transactions").toPandas()

# Charger le dataset de référence (historique)
reference_df = pd.read_parquet("/delta/transactions_reference.parquet")

# %%
# Sélectionner les colonnes features pour monitoring
features = ["amount", "currency", "customer_id"]

current_df_features = current_df[features]
reference_df_features = reference_df[features]

# %%
# Création d'un rapport Evidently pour la dérive
report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])
report.run(reference_data=reference_df_features, current_data=current_df_features)

# %%
# Génération du rapport HTML
report.save_html("/tmp/transactions_drift_report.html")
print("✅ Rapport Evidently généré : /tmp/transactions_drift_report.html")

# %%
# Optionnel : Profiling détaillé
profile = Profile(sections=[DataDriftProfileSection()])
profile.calculate(reference_df_features, current_df_features)
profile.json()  # Pour logging ou API
