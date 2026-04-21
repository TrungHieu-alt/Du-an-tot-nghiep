import os
import chromadb
import numpy as np
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
VECTOR_DB_PATH = os.path.join(ROOT_DIR, "vector_store")

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

# ============================
# COLLECTIONS (Simplified to 2)
# ============================
cv_full = client.get_or_create_collection("cv_full")
jd_full = client.get_or_create_collection("jd_full")


# ============================
# STORE CV
# ============================
def store_cv(cv_id, emb, cv_data):
    """
    Store CV with all embeddings in metadata.
    
    Args:
        cv_id: Unique CV identifier
        emb: Dictionary of embeddings from embed_cv()
        cv_data: Dictionary with CV fields (summary, skills, full_text, etc.)
    """
    # Convert numpy arrays to lists for JSON serialization
    embeddings_dict = {}
    for key, value in emb.items():
        if isinstance(value, np.ndarray):
            embeddings_dict[key] = value.tolist()
        elif value is None:
            embeddings_dict[key] = None
        else:
            embeddings_dict[key] = value
    
    # Serialize embeddings dict to JSON string for ChromaDB compatibility
    # ChromaDB only accepts str, int, float, bool, None in metadata
    metadata = {
        "embeddings": json.dumps(embeddings_dict),  # ✅ Serialize to string
        "full_text": cv_data.get("full_text", ""),
        "summary": cv_data.get("summary", ""),
        "experience": cv_data.get("experience", ""),
        "skills": json.dumps(cv_data.get("skills", [])),  # ✅ Serialize list
        "job_title": cv_data.get("job_title", ""),
        "location": cv_data.get("location", ""),
    }
    
    cv_full.add(
        ids=[cv_id],
        embeddings=[emb["emb_full"]],
        metadatas=[metadata]
    )


# ============================
# STORE JD
# ============================
def store_jd(jd_id, emb, jd_data):
    """
    Store JD with all embeddings in metadata.
    
    Args:
        jd_id: Unique JD identifier
        emb: Dictionary of embeddings from embed_jd()
        jd_data: Dictionary with JD fields (job_description, skills, full_text, etc.)
    """
    # Convert numpy arrays to lists for JSON serialization
    embeddings_dict = {}
    for key, value in emb.items():
        if isinstance(value, np.ndarray):
            embeddings_dict[key] = value.tolist()
        elif value is None:
            embeddings_dict[key] = None
        else:
            embeddings_dict[key] = value
    
    # Serialize embeddings dict to JSON string for ChromaDB compatibility
    metadata = {
        "embeddings": json.dumps(embeddings_dict),  # ✅ Serialize to string
        "full_text": jd_data.get("full_text", ""),
        "job_description": jd_data.get("job_description", ""),
        "job_requirement": jd_data.get("job_requirement", ""),
        "skills": json.dumps(jd_data.get("skills", [])),  # ✅ Serialize list
        "job_title": jd_data.get("job_title", ""),
        "location": jd_data.get("location", ""),
    }
    
    jd_full.add(
        ids=[jd_id],
        embeddings=[emb["emb_full"]],
        metadatas=[metadata]
    )


# ============================
# DELETE CV
# ============================
def delete_cv(cv_id):
    """Delete CV by ID"""
    cv_full.delete(ids=[cv_id])


# ============================
# DELETE JD
# ============================
def delete_jd(jd_id):
    """Delete JD by ID"""
    jd_full.delete(ids=[jd_id])


def debug_collection(collection, name):
    print(f"\n==================== {name} ====================")
    print(f"Total records: {collection.count()}")

    if collection.count() == 0:
        print("No records found.")
        return

    # get all records
    res = collection.get(include=["embeddings", "metadatas", "documents"])

    for i in range(len(res["ids"])):
        print(f"\n---- Record {i+1} | ID = {res['ids'][i]} ----")

        # Full Embedding
        print("\n[EMBEDDING]")
        emb = res["embeddings"][i]
        if isinstance(emb, np.ndarray):
            emb = emb.tolist()
        print(json.dumps(emb, indent=2))

        # Full Metadata
        print("\n[METADATA]")
        print(json.dumps(res["metadatas"][i], indent=2))

        # Document (if any)
        print("\n[DOCUMENT]")
        print(res["documents"][i] if res["documents"] else None)
    print(f"\n==================== {name} ====================")
    print(f"Total records: {collection.count()}")

    if collection.count() == 0:
        print("No records found.")
        return

    # get all records
    res = collection.get(include=["embeddings", "metadatas", "documents"])

    for i in range(len(res["ids"])):
        print(f"\n---- Record {i+1} | ID = {res['ids'][i]} ----")

        # Full Embedding (converted to python list)
        print("\n[EMBEDDING]")
        print(json.dumps(res["embeddings"][i], indent=2))

        # Full Metadata
        print("\n[METADATA]")
        print(json.dumps(res["metadatas"][i], indent=2))

        # Document (if any)
        print("\n[DOCUMENT]")
        print(res["documents"][i] if res["documents"] else None)


def main():
    delete_cv("test_cv_001")
    delete_jd("test_jd_001")
    print("=== ChromaDB Summary ===")

    # CV COLLECTION
    print("\n[CV_FULL]")
    cv_count = cv_full.count()
    print(f"Total records: {cv_count}")

    if cv_count > 0:
        res = cv_full.get(include=["embeddings"])
        print("IDs:")
        for _id in res["ids"]:
            print(f" - { _id }")

    # JD COLLECTION
    print("\n[JD_FULL]")
    jd_count = jd_full.count()
    print(f"Total records: {jd_count}")

    if jd_count > 0:
        res = jd_full.get(include=["embeddings"])
        print("IDs:")
        for _id in res["ids"]:
            print(f" - { _id }")


if __name__ == "__main__":
    main()
