import glob
import io
import os
import pandas as pd

def load_clean_csv(file_path):
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    bom_index = raw_bytes.find(b"\xef\xbb\xbf")
    if bom_index != -1:
        text_data = raw_bytes[bom_index:].decode("utf-8", errors="replace")
    else:
        text_data = raw_bytes.decode("utf-8", errors="replace")

    df = pd.read_csv(
        io.StringIO(text_data),
        sep=";",
        quotechar='"',
        on_bad_lines="skip",
        dtype=str
    )
    df.columns = [col.replace("\\", "").strip() for col in df.columns]
    df["source_file"] = os.path.basename(file_path)
    return df

def run_profiling(data_dir):
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        csv_files = glob.glob("*.csv")

    dataframes = [load_clean_csv(f) for f in csv_files]
    merged_df = pd.concat(dataframes, ignore_index=True)

    print("=== DATASET PROFILING SUMMARY ===")
    print(f"Total CSV files loaded: {len(csv_files)}")
    print(f"Total rows loaded: {len(merged_df)}")
    
    if "original_id" in merged_df.columns:
        dup_ids = merged_df.duplicated(subset=["original_id"]).sum()
        print(f"Duplicate rows by original_id: {dup_ids}")
    
    dup_content = merged_df.duplicated(subset=["title", "body"]).sum()
    print(f"Duplicate rows by title + body: {dup_content}")

    missing_titles = merged_df["title"].isna().sum()
    missing_bodies = merged_df["body"].isna().sum()
    print(f"Missing titles: {missing_titles}")
    print(f"Missing bodies: {missing_bodies}")

    print("\nLanguage distribution:")
    if "language" in merged_df.columns:
        print(merged_df["language"].value_counts(dropna=False))

    print("\nEntities column sample:")
    if "entities" in merged_df.columns:
        non_null_entities = merged_df["entities"].dropna()
        for sample in non_null_entities.iloc[:5]:
            print(f"- {sample}")

    clean_df = merged_df.dropna(subset=["title", "body"])
    clean_df = clean_df.drop_duplicates(subset=["original_id"] if "original_id" in clean_df.columns else ["title", "body"])
    print(f"\nUnique valid articles remaining: {len(clean_df)}")

    os.makedirs("data/processed", exist_ok=True)
    clean_df.to_csv("data/processed/unique_articles.csv", index=False)

if __name__ == "__main__":
    run_profiling("data/raw")
