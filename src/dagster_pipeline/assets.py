from dagster import asset, Config
import pandas as pd
from pathlib import Path
import json
from data_ingestion.file_readers import DataFileReader
from data_ingestion.schema_validators import SchemaValidator

class DataConfig(Config):
    data_dir: str = "/opt/dagster/data/raw"

@asset
def raw_drugs_data(config: DataConfig) -> pd.DataFrame:
    """Load and validate drugs.csv"""
    reader = DataFileReader(config.data_dir)
    df = reader.read_csv("drugs.csv", required_columns=['atccode', 'drug'])
    return SchemaValidator.validate_drugs_schema(df)

@asset  
def raw_pubmed_csv_data(config: DataConfig) -> pd.DataFrame:
    """Load and validate pubmed.csv"""
    reader = DataFileReader(config.data_dir)
    df = reader.read_csv("pubmed.csv", required_columns=['id', 'title', 'date', 'journal'])
    return SchemaValidator.validate_pubmed_schema(df)

@asset
def raw_pubmed_json_data(config: DataConfig) -> pd.DataFrame:
    """Load and validate pubmed.json"""
    reader = DataFileReader(config.data_dir)
    json_data = reader.read_json("pubmed.json")
    df = pd.DataFrame(json_data)
    return SchemaValidator.validate_pubmed_schema(df)

@asset
def raw_clinical_trials_data(config: DataConfig) -> pd.DataFrame:
    """Load and validate clinical_trials.csv"""
    reader = DataFileReader(config.data_dir)
    df = reader.read_csv("clinical_trials.csv", required_columns=['id', 'scientific_title', 'date', 'journal'])
    return SchemaValidator.validate_clinical_trials_schema(df)

@asset
def consolidated_publications(
    raw_pubmed_csv_data: pd.DataFrame,
    # raw_pubmed_json_data: pd.DataFrame,  # Comment out temporarily
    raw_clinical_trials_data: pd.DataFrame
) -> pd.DataFrame:
    """Consolidate all publication sources into unified dataset"""
    
    pubmed_csv = raw_pubmed_csv_data.copy()
    pubmed_csv['source'] = 'pubmed_csv'
    
    clinical_trials = raw_clinical_trials_data.copy()
    clinical_trials['source'] = 'clinical_trials'
    
    # Combine sources (without JSON for now)
    all_publications = pd.concat([pubmed_csv, clinical_trials], ignore_index=True)
    
    return all_publications

@asset
def drug_mentions_extracted(
    raw_drugs_data: pd.DataFrame,
    consolidated_publications: pd.DataFrame
) -> pd.DataFrame:
    """Extract drug mentions from publication titles"""
    mentions = []
    
    for _, pub in consolidated_publications.iterrows():
        title = str(pub['title']).upper()
        
        for _, drug in raw_drugs_data.iterrows():
            drug_name = str(drug['drug']).upper()
            
            if drug_name in title:
                mentions.append({
                    'drug': drug['drug'],
                    'atccode': drug['atccode'],
                    'publication_id': pub['id'],
                    'publication_title': pub['title'],
                    'journal': pub['journal'],
                    'date': pub['date'],
                    'source': pub['source']
                })
    
    return pd.DataFrame(mentions)

@asset
def medical_graph_json(drug_mentions_extracted: pd.DataFrame) -> dict:
    """Build the final medical graph JSON structure"""
    
    # Group by drug to build drug-centric graph
    drug_graph = {}
    journal_stats = {}
    
    for _, mention in drug_mentions_extracted.iterrows():
        drug_name = mention['drug']
        journal = mention['journal']
        
        # Build drug entries
        if drug_name not in drug_graph:
            drug_graph[drug_name] = {
                'atccode': mention['atccode'],
                'mentions': []
            }
        
        drug_graph[drug_name]['mentions'].append({
            'publication_id': mention['publication_id'],
            'publication_title': mention['publication_title'],
            'journal': journal,
            'date': mention['date'],
            'source': mention['source']
        })
        
        # Build journal statistics
        if journal not in journal_stats:
            journal_stats[journal] = {
                'unique_drugs': set(),
                'total_mentions': 0,
                'publications': set()
            }
        
        journal_stats[journal]['unique_drugs'].add(drug_name)
        journal_stats[journal]['total_mentions'] += 1
        journal_stats[journal]['publications'].add(mention['publication_title'])
    
    # Convert sets to lists for JSON serialization
    journal_summary = {}
    for journal, stats in journal_stats.items():
        journal_summary[journal] = {
            'unique_drugs_count': len(stats['unique_drugs']),
            'unique_drugs_list': sorted(list(stats['unique_drugs'])),
            'total_mentions': stats['total_mentions'],
            'publications_count': len(stats['publications'])
        }
    
    # Final graph structure
    graph = {
        'drugs': drug_graph,
        'journals': journal_summary,
        'summary': {
            'total_drugs_with_mentions': len(drug_graph),
            'total_journals': len(journal_summary),
            'total_mentions': len(drug_mentions_extracted)
        }
    }
    
    return graph


@asset
def save_medical_graph(medical_graph_json: dict) -> str:
    """Save the medical graph to JSON file"""
    
    output_path = Path("/opt/dagster/output/medical_graph.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(medical_graph_json, f, indent=2, ensure_ascii=False)
    
    return str(output_path)