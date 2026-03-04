-- ==========================================
-- THE UNIVERSAL LOOKUP TABLE (ULT)
-- ==========================================
CREATE TABLE EntityLookup (
  lookup_id STRING(36) NOT NULL,    
  raw_value STRING(MAX) NOT NULL,   
  node_label STRING(MAX) NOT NULL,  
  property_name STRING(MAX) NOT NULL, 
  canonical_id STRING(MAX) NOT NULL,
  lookup_type STRING(20),           
  embedding ARRAY<FLOAT64>,
  -- Spanner requires a TOKENLIST generated column for full-text search
  raw_value_tokens TOKENLIST AS (TOKENIZE_SUBSTRING(raw_value)) HIDDEN
) PRIMARY KEY (lookup_id);

CREATE INDEX EntityLookup_PreFilter ON EntityLookup (node_label, property_name) STORING (canonical_id);

-- Native Search Index points to the TOKENLIST column
CREATE SEARCH INDEX EntityLookup_TextSearch ON EntityLookup (raw_value_tokens) STORING (canonical_id, node_label, property_name);

-- Vector Index syntax completed
CREATE VECTOR INDEX EntityLookupVectorIndex ON EntityLookup (embedding) OPTIONS (distance_type = 'COSINE', index_type = 'TREE_AH');

