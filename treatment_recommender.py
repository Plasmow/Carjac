#!/usr/bin/env python3
"""
ESMO Metastatic Breast Cancer Treatment Recommender
Processes patient JSON through ESMO decision tree guidelines
"""

import json
import sys
from typing import Dict, List, Any, Optional, Tuple


#Index inversé




class ESMOTreatmentRecommender:
    
    def __init__(self, guidelines_path: str):
        """Initialize with ESMO guidelines JSON file"""
        with open(guidelines_path, 'r') as f:
            self.guidelines = json.load(f)
        self.recommendations = []
        
    def evaluate_condition(self, condition: Dict, patient: Dict) -> bool:
        """Evaluate a single condition against patient data"""
        condition_id = condition.get('condition_id')
        category = condition.get('category')
        expected_value = condition.get('value')
        operator = condition.get('operator', '=')
        
        # Map condition to patient data
        if category == 'diagnosis':
            if condition_id == 'mbc_diagnosis':
                return patient.get('diagnosis', {}).get('stage') == 'metastatic'
                
        elif category == 'biomarker':
            biomarkers = patient.get('biomarkers', {})
            
            if condition_id == 'er_positive':
                return biomarkers.get('ER') == 'positive'
            elif condition_id == 'her2_negative':
                return biomarkers.get('HER2') == 'negative'
            elif condition_id == 'her2_positive':
                return biomarkers.get('HER2') == 'positive'
            elif condition_id == 'hr_negative':
                return (biomarkers.get('ER') == 'negative' and 
                       biomarkers.get('PgR') == 'negative')
            elif condition_id == 'tnbc_status':
                return (biomarkers.get('ER') == 'negative' and 
                       biomarkers.get('PgR') == 'negative' and
                       biomarkers.get('HER2') == 'negative')
            elif condition_id == 'pik3ca_mutation':
                return biomarkers.get('PIK3CA') == 'mutant'
            elif condition_id == 'brca_or_palb2':
                return (biomarkers.get('BRCA1') == 'mutant' or 
                       biomarkers.get('BRCA2') == 'mutant' or
                       biomarkers.get('PALB2') == 'mutant')
            elif condition_id == 'esr1_mut':
                return biomarkers.get('ESR1') == 'mutant'
            elif condition_id == 'msi_high':
                return biomarkers.get('MSI') == 'high'
            elif condition_id == 'ntrk_fusion':
                return biomarkers.get('NTRK') == 'positive'
            elif condition_id == 'tmb_high':
                return biomarkers.get('TMB', 0) >= 10
                
        elif category == 'treatment_history':
            treatment_history = patient.get('treatment_history', [])
            
            if condition_id == 'progressed_on_cdk46':
                return any('CDK4/6' in t.get('regimen', '') and t.get('progression', False) 
                          for t in treatment_history)
            elif condition_id == 'progression_on_first_line':
                return len(treatment_history) >= 1 and any(t.get('progression', False) 
                                                          for t in treatment_history)
            elif condition_id == 'exhausted_standard':
                return len(treatment_history) >= 2
                
        elif category == 'lab_value':
            lab_values = patient.get('lab_values', {})
            
            if condition_id == 'hba1c_ok':
                return lab_values.get('HbA1c', 10) < 8.0
                
        elif category == 'contraindication':
            contraindications = patient.get('contraindications', [])
            
            if condition_id == 'chemo_contraindicated':
                return any('chemotherapy' in c for c in contraindications)
        
        return False
    
    def evaluate_conditions(self, conditions: List[Dict], patient: Dict) -> bool:
        """Evaluate all conditions for a node (AND logic)"""
        return all(self.evaluate_condition(cond, patient) for cond in conditions)
    
    def get_subtype(self, patient: Dict) -> str:
        """Determine breast cancer subtype"""
        biomarkers = patient.get('biomarkers', {})
        if (biomarkers.get('ER') == 'negative' and 
            biomarkers.get('PgR') == 'negative' and 
            biomarkers.get('HER2') == 'negative'):
            return 'TNBC'
        elif biomarkers.get('HER2') == 'positive':
            return 'HER2+'
        elif biomarkers.get('ER') == 'positive':
            return 'Luminal'
        else:
            return 'Unknown'
    
    def traverse_node(self, node: Dict, patient: Dict, path: List[str] = []) -> List[Dict]:
        """Recursively traverse decision tree and collect recommendations"""
        recommendations = []
        
        # Check if node conditions are met
        conditions = node.get('conditions', [])
        if conditions and not self.evaluate_conditions(conditions, patient):
            return recommendations
        
        # If this is an action node, collect the actions
        if node.get('node_type') == 'action':
            actions = node.get('actions', [])
            for action in actions:
                if action.get('action_type') == 'drug_therapy':
                    rec = {
                        'treatment': action.get('name'),
                        'evidence_level': action.get('evidence_level'),
                        'recommendation_strength': action.get('recommendation_strength'),
                        'node_path': ' -> '.join(path + [node.get('title', '')]),
                        'rationale': self.generate_rationale(node, action, patient),
                        'keywords': self.extract_keywords(action.get('name', ''))
                    }
                    recommendations.append(rec)
        
        # Traverse children
        children = node.get('children', [])
        for child in children:
            child_recs = self.traverse_node(child, patient, path + [node.get('title', '')])
            recommendations.extend(child_recs)
        
        return recommendations
    
    def generate_rationale(self, node: Dict, action: Dict, patient: Dict) -> str:
        """Generate human-readable rationale for treatment recommendation"""
        subtype = self.get_subtype(patient)
        treatment = action.get('name', 'Treatment')
        
        # Get relevant biomarkers
        biomarkers = patient.get('biomarkers', {})
        treatment_history = patient.get('treatment_history', [])
        
        rationale_parts = []
        
        # Add subtype context
        rationale_parts.append(f"Patient has {subtype} metastatic breast cancer")
        
        # Add specific biomarker context
        if 'PIK3CA' in treatment and biomarkers.get('PIK3CA') == 'mutant':
            rationale_parts.append(f"PIK3CA mutation present, making {treatment} a targeted option")
        elif 'PARP' in treatment and (biomarkers.get('BRCA1') == 'mutant' or 
                                     biomarkers.get('BRCA2') == 'mutant' or 
                                     biomarkers.get('PALB2') == 'mutant'):
            rationale_parts.append(f"Homologous recombination deficiency (BRCA/PALB2 mutation) supports PARP inhibitor use")
        elif 'Pembrolizumab' in treatment and biomarkers.get('MSI') == 'high':
            rationale_parts.append(f"MSI-high tumor supports immunotherapy with pembrolizumab")
        elif 'Trastuzumab' in treatment and biomarkers.get('HER2') == 'positive':
            rationale_parts.append(f"HER2-positive status supports anti-HER2 therapy")
        
        # Add treatment line context
        if len(treatment_history) > 0:
            rationale_parts.append(f"Recommended after progression on {len(treatment_history)} prior line(s)")
        
        return '. '.join(rationale_parts) + '.'
    
    def extract_keywords(self, treatment_name: str) -> List[str]:
        """Extract keywords from treatment names for search/matching"""
        keywords = []
        
        # Drug name mapping
        drug_mappings = {
            'Alpelisib': ['alpelisib', 'PIK3CA inhibitor', 'PI3K inhibitor'],
            'Fulvestrant': ['fulvestrant', 'SERD', 'selective estrogen receptor degrader'],
            'Everolimus': ['everolimus', 'mTOR inhibitor'],
            'Exemestane': ['exemestane', 'aromatase inhibitor'],
            'Olaparib': ['olaparib', 'PARP inhibitor', 'BRCA targeting'],
            'Talazoparib': ['talazoparib', 'PARP inhibitor', 'BRCA targeting'],
            'Sacituzumab Govitecan': ['sacituzumab govitecan', 'ADC', 'antibody drug conjugate', 'Trop-2'],
            'Pembrolizumab': ['pembrolizumab', 'PD-1 inhibitor', 'immunotherapy', 'checkpoint inhibitor'],
            'Trastuzumab': ['trastuzumab', 'anti-HER2', 'HER2 targeting'],
            'Pertuzumab': ['pertuzumab', 'anti-HER2', 'HER2 targeting'],
            'Larotrectinib': ['larotrectinib', 'TRK inhibitor', 'NTRK targeting'],
            'Entrectinib': ['entrectinib', 'TRK inhibitor', 'NTRK targeting']
        }
        
        # Extract keywords based on drug names in treatment
        for drug, terms in drug_mappings.items():
            if drug.lower() in treatment_name.lower():
                keywords.extend(terms)
        
        # Add combination keywords
        if '+' in treatment_name:
            keywords.append('combination therapy')
        
        # Add general keywords
        keywords.extend(['metastatic breast cancer', 'systemic therapy'])
        
        return list(set(keywords))  # Remove duplicates
    
    def process_patient(self, patient_path: str) -> Dict:
        """Process a single patient JSON file"""
        with open(patient_path, 'r') as f:
            patient = json.load(f)
        
        # Start traversal from root
        root = self.guidelines['decision_tree']['root']
        recommendations = self.traverse_node(root, patient)
        
        # Add patient summary
        subtype = self.get_subtype(patient)
        
        result = {
            'patient_id': patient.get('patient_id'),
            'subtype': subtype,
            'biomarker_summary': self.get_biomarker_summary(patient),
            'treatment_history_summary': self.get_treatment_history_summary(patient),
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
        
        return result
    
    def get_biomarker_summary(self, patient: Dict) -> Dict:
        """Summarize key biomarkers"""
        biomarkers = patient.get('biomarkers', {})
        return {
            'ER': biomarkers.get('ER', 'unknown'),
            'PgR': biomarkers.get('PgR', 'unknown'),
            'HER2': biomarkers.get('HER2', 'unknown'),
            'PIK3CA': biomarkers.get('PIK3CA', 'unknown'),
            'BRCA1': biomarkers.get('BRCA1', 'unknown'),
            'BRCA2': biomarkers.get('BRCA2', 'unknown'),
            'PALB2': biomarkers.get('PALB2', 'unknown'),
            'MSI': biomarkers.get('MSI', 'unknown'),
            'TMB': biomarkers.get('TMB', 'unknown')
        }
    
    def get_treatment_history_summary(self, patient: Dict) -> str:
        """Summarize treatment history"""
        history = patient.get('treatment_history', [])
        if not history:
            return "Treatment-naive"
        
        lines = len(history)
        last_regimen = history[-1].get('regimen', 'Unknown regimen')
        return f"{lines} prior line(s), last: {last_regimen}"
    
    def format_output(self, result: Dict) -> str:
        """Format results for human-readable output"""
        output = []
        output.append("=" * 60)
        output.append(f"ESMO Treatment Recommendations for {result['patient_id']}")
        output.append("=" * 60)
        output.append(f"Subtype: {result['subtype']}")
        output.append(f"Treatment History: {result['treatment_history_summary']}")
        output.append("")
        
        output.append("Key Biomarkers:")
        for marker, value in result['biomarker_summary'].items():
            output.append(f"  {marker}: {value}")
        output.append("")
        
        if result['recommendations']:
            output.append(f"Treatment Recommendations ({result['total_recommendations']} found):")
            output.append("-" * 40)
            
            for i, rec in enumerate(result['recommendations'], 1):
                output.append(f"\n{i}. {rec['treatment']}")
                output.append(f"   Evidence Level: {rec['evidence_level']} | Strength: {rec['recommendation_strength']}")
                output.append(f"   Rationale: {rec['rationale']}")
                output.append(f"   Keywords: {', '.join(rec['keywords'][:5])}...")  # Show first 5 keywords
                output.append(f"   Decision Path: {rec['node_path']}")
        else:
            output.append("No specific treatment recommendations found in guidelines.")
            output.append("Consider standard-of-care options or clinical trial enrollment.")
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)




def main():
    if len(sys.argv) != 3:
        print("Usage: python treatment_recommender.py <guidelines.json> <patient.json>")
        sys.exit(1)
    
    guidelines_file = sys.argv[1]
    patient_file = sys.argv[2]
    
    try:
        # Initialize recommender
        recommender = ESMOTreatmentRecommender(guidelines_file)
        
        # Process patient
        result = recommender.process_patient(patient_file)
        
        # Output results
        print(recommender.format_output(result))
        
        # Save structured results to JSON
        output_file = f"recommendations_{result['patient_id']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nStructured results saved to: {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing patient: {e}")
        sys.exit(1)





if __name__ == "__main__":
    main()