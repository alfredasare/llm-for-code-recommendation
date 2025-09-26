import pandas as pd
import hashlib
import argparse
import os
from typing import Tuple, List, Set
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')


class DatasetPreprocessor:
    def __init__(self, dataset_name: str, similarity_threshold: float = 0.95):
        """
        Initialize preprocessor for a specific dataset.
        
        Args:
            dataset_name: 'bigvul' or 'cvefixes'
            similarity_threshold: Threshold for content similarity (0-1)
        """
        self.dataset_name = dataset_name.lower()
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        
        # Dataset-specific column mappings
        if self.dataset_name == 'bigvul':
            self.code_before_col = 'func_before'
            self.code_after_col = 'func_after'
            self.cve_col = 'CVE ID'
            self.cwe_col = 'CWE ID'
            self.id_col = 'commit_id'  
        elif self.dataset_name == 'cvefixes':
            self.code_before_col = 'code_before'
            self.code_after_col = 'code_after'
            self.cve_col = 'cve_id'
            self.cwe_col = 'cwe_id'
            self.id_col = 'hash'
        else:
            raise ValueError(f"Unsupported dataset: {dataset_name}. Use 'bigvul' or 'cvefixes'")
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate dataset."""
        print(f"Loading {self.dataset_name} dataset from {file_path}...")
        
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded {len(df)} rows")
            
            # Check required columns
            required_cols = [self.code_before_col, self.code_after_col, self.cve_col, self.cwe_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Clean data
            df = df.dropna(subset=required_cols)
            df = df[df[self.code_before_col].str.strip() != '']
            df = df[df[self.code_after_col].str.strip() != '']
            
            print(f"After cleaning: {len(df)} rows")
            return df
            
        except Exception as e:
            raise Exception(f"Error loading data: {e}")
    
    def create_content_hash(self, row: pd.Series) -> str:
        """Create a hash based on code content for exact duplicate detection."""
        content = f"{row[self.code_before_col]}{row[self.code_after_col]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def create_group_key(self, row: pd.Series) -> str:
        """Create a group key for CVE+CWE grouping."""
        return f"{row[self.cve_col]}_{row[self.cwe_col]}"
    
    def detect_content_similarity(self, df: pd.DataFrame) -> List[Set[int]]:
        """Detect similar content using TF-IDF and cosine similarity."""
        print("Detecting content similarity...")
        
        # Prepare text for similarity comparison
        texts = []
        for _, row in df.iterrows():
            text = f"{row[self.code_before_col]} {row[self.code_after_col]}"
            texts.append(text)
        
        # Vectorize texts
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Find similar pairs
        similarity_matrix = cosine_similarity(tfidf_matrix)
        similar_groups = []
        processed = set()
        
        for i in range(len(similarity_matrix)):
            if i in processed:
                continue
                
            similar_indices = set([i])
            for j in range(i + 1, len(similarity_matrix)):
                if j in processed:
                    continue
                    
                if similarity_matrix[i][j] >= self.similarity_threshold:
                    similar_indices.add(j)
                    processed.add(j)
            
            if len(similar_indices) > 1:
                similar_groups.append(similar_indices)
            
            processed.add(i)
        
        print(f"Found {len(similar_groups)} groups of similar content")
        return similar_groups
    
    def deduplicate_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply multi-level deduplication strategy."""
        print("Starting deduplication process...")
        
        # Add helper columns
        df = df.copy()
        df['content_hash'] = df.apply(self.create_content_hash, axis=1)
        df['group_key'] = df.apply(self.create_group_key, axis=1)
        df['row_id'] = range(len(df))
        
        original_count = len(df)
        print(f"Original dataset size: {original_count}")
        
        # Level 1: Remove exact duplicates based on content hash
        print("Level 1: Removing exact content duplicates...")
        df = df.drop_duplicates(subset=['content_hash'], keep='first')
        level1_count = len(df)
        print(f"After exact deduplication: {level1_count} (removed {original_count - level1_count})")
        
        # Level 2: Group by CVE+CWE and remove duplicates within groups
        print("Level 2: Removing duplicates within CVE+CWE groups...")
        df_grouped = df.groupby('group_key').apply(
            lambda group: group.drop_duplicates(subset=['content_hash'], keep='first')
        ).reset_index(drop=True)
        
        level2_count = len(df_grouped)
        print(f"After group deduplication: {level2_count} (removed {level1_count - level2_count})")
        
        # Level 3: Remove similar content using TF-IDF similarity
        print("Level 3: Removing similar content...")
        similar_groups = self.detect_content_similarity(df_grouped)
        
        indices_to_remove = set()
        for group in similar_groups:
            # Keep the first item in each similar group
            group_list = list(group)
            indices_to_remove.update(group_list[1:])
        
        df_final = df_grouped[~df_grouped['row_id'].isin(indices_to_remove)]
        level3_count = len(df_final)
        print(f"After similarity deduplication: {level3_count} (removed {level2_count - level3_count})")
        
        df_final = df_final.drop(['content_hash', 'group_key', 'row_id'], axis=1)
        
        print(f"Final deduplication: {original_count} -> {level3_count} (removed {original_count - level3_count})")
        return df_final
    
    def create_stratified_split(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("Creating stratified train/test split...")
        
        # Group by CVE+CWE to prevent data leakage
        df['group_key'] = df.apply(self.create_group_key, axis=1)
        groups = df.groupby('group_key')
        
        # Get group statistics
        cwe_distribution = df.groupby(self.cwe_col).size()
        
        print(f"Total groups: {len(groups)}")
        print(f"CWE distribution: {dict(cwe_distribution.head(10))}")
        
        group_names = list(groups.groups.keys())
        
        group_cwe_map = {}
        for group_name, group_df in groups:
            cwe = group_df[self.cwe_col].iloc[0]  
            group_cwe_map[group_name] = cwe
        
        # Handle groups with only 1 member 
        cwe_counts = Counter(group_cwe_map.values())
        single_groups = [g for g in group_names if cwe_counts[group_cwe_map[g]] == 1]
        multi_groups = [g for g in group_names if cwe_counts[group_cwe_map[g]] > 1]
        
        print(f"Groups with single CWE: {len(single_groups)} (will go to training)")
        print(f"Groups with multiple CWE: {len(multi_groups)} (will be stratified)")
        
        # Put single groups in training set
        train_groups = single_groups.copy()
        test_groups = []
        
        # Stratify the multi-groups
        if multi_groups:
            try:
                multi_train, multi_test = train_test_split(
                    multi_groups,
                    test_size=test_size,
                    random_state=random_state,
                    stratify=[group_cwe_map[g] for g in multi_groups]
                )
                train_groups.extend(multi_train)
                test_groups.extend(multi_test)
                print("Used stratified splitting for multi-groups")
            except ValueError as e:
                print(f"Stratified splitting failed for multi-groups: {e}")
                print("Using regular random splitting for multi-groups...")
                multi_train, multi_test = train_test_split(
                    multi_groups,
                    test_size=test_size,
                    random_state=random_state
                )
                train_groups.extend(multi_train)
                test_groups.extend(multi_test)
                print("Used regular random splitting for multi-groups")
        else:
            print("All groups have single CWE, all go to training")
        
        # Create train and test datasets
        train_df = df[df['group_key'].isin(train_groups)].drop('group_key', axis=1)
        test_df = df[df['group_key'].isin(test_groups)].drop('group_key', axis=1)
        
        print(f"Train set: {len(train_df)} rows from {len(train_groups)} groups")
        print(f"Test set: {len(test_df)} rows from {len(test_groups)} groups")
        
        # Verify no data leakage
        train_cve_cwe = set(zip(train_df[self.cve_col], train_df[self.cwe_col]))
        test_cve_cwe = set(zip(test_df[self.cve_col], test_df[self.cwe_col]))
        overlap = train_cve_cwe.intersection(test_cve_cwe)
        
        if overlap:
            raise ValueError(f"Data leakage detected! {len(overlap)} CVE+CWE combinations appear in both sets")
        else:
            print("No data leakage detected")
        
        return train_df, test_df
    
    def save_datasets(self, train_df: pd.DataFrame, test_df: pd.DataFrame, output_dir: str = "data"):
        os.makedirs(output_dir, exist_ok=True)
        
        # Save datasets
        train_file = os.path.join(output_dir, f"{self.dataset_name}_kb.csv")
        test_file = os.path.join(output_dir, f"{self.dataset_name}_test.csv")
        
        train_df.to_csv(train_file, index=False)
        test_df.to_csv(test_file, index=False)
        
        print(f"Saved knowledge base to: {train_file}")
        print(f"Saved test set to: {test_file}")
        
        # Generate and save statistics
        stats = self.generate_statistics(train_df, test_df)
        stats_file = os.path.join(output_dir, f"{self.dataset_name}_split_stats.txt")
        
        with open(stats_file, 'w') as f:
            f.write(f"Dataset: {self.dataset_name.upper()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(stats)
        
        print(f"Saved statistics to: {stats_file}")
    
    def generate_statistics(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> str:
        """Generate detailed statistics about the split."""
        stats = []
        
        # Basic counts
        stats.append(f"Train set size: {len(train_df)}")
        stats.append(f"Test set size: {len(test_df)}")
        stats.append(f"Total size: {len(train_df) + len(test_df)}")
        stats.append(f"Train ratio: {len(train_df) / (len(train_df) + len(test_df)):.3f}")
        stats.append(f"Test ratio: {len(test_df) / (len(train_df) + len(test_df)):.3f}\n")
        
        # CWE distribution
        train_cwe_dist = train_df[self.cwe_col].value_counts()
        test_cwe_dist = test_df[self.cwe_col].value_counts()
        
        stats.append("CWE Distribution:")
        stats.append("-" * 20)
        all_cwes = set(train_cwe_dist.index) | set(test_cwe_dist.index)
        
        for cwe in sorted(all_cwes):
            train_count = train_cwe_dist.get(cwe, 0)
            test_count = test_cwe_dist.get(cwe, 0)
            total = train_count + test_count
            stats.append(f"{cwe}: Train={train_count}, Test={test_count}, Total={total}")
        
        # CVE distribution
        train_cve_count = train_df[self.cve_col].nunique()
        test_cve_count = test_df[self.cve_col].nunique()
        total_cve_count = train_df[self.cve_col].nunique() + test_df[self.cve_col].nunique()
        
        stats.append(f"\nCVE Distribution:")
        stats.append("-" * 20)
        stats.append(f"Unique CVEs in train: {train_cve_count}")
        stats.append(f"Unique CVEs in test: {test_cve_count}")
        stats.append(f"Total unique CVEs: {total_cve_count}")
        
        return "\n".join(stats)
    
    def process_dataset(self, input_file: str, output_dir: str = "data", test_size: float = 0.2, 
                       random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Complete preprocessing pipeline."""
        print(f"Processing {self.dataset_name.upper()} dataset...")
        print("=" * 50)
        
        # Load data
        df = self.load_data(input_file)
        
        # Deduplicate
        df_dedup = self.deduplicate_dataset(df)
        
        # Split
        train_df, test_df = self.create_stratified_split(df_dedup, test_size, random_state)
        
        # Save
        self.save_datasets(train_df, test_df, output_dir)
        
        return train_df, test_df


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Preprocess vulnerability datasets with deduplication and splitting")
    parser.add_argument("dataset", choices=["bigvul", "cvefixes"], help="Dataset to process")
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size ratio (default: 0.2)")
    parser.add_argument("--random-state", type=int, default=42, help="Random state for reproducibility (default: 42)")
    parser.add_argument("--similarity-threshold", type=float, default=0.95, 
                       help="Similarity threshold for content deduplication (default: 0.95)")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    try:
        # Create preprocessor
        preprocessor = DatasetPreprocessor(args.dataset, args.similarity_threshold)
        
        # Process dataset
        train_df, test_df = preprocessor.process_dataset(
            args.input_file, 
            args.output_dir, 
            args.test_size, 
            args.random_state
        )
        
        print("\n" + "=" * 50)
        print("Preprocessing completed successfully!")
        print(f"Train set: {len(train_df)} rows")
        print(f"Test set: {len(test_df)} rows")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
