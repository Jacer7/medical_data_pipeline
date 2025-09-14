from dagster import Definitions
from .assets import (
    raw_drugs_data, 
    raw_pubmed_csv_data, 
    raw_clinical_trials_data,
    consolidated_publications,
    drug_mentions_extracted,
    medical_graph_json,
    save_medical_graph
)

defs = Definitions(
    assets=[
        raw_drugs_data,
        raw_pubmed_csv_data,
        raw_clinical_trials_data,
        consolidated_publications,
        drug_mentions_extracted,
        medical_graph_json,
        save_medical_graph
    ]
)