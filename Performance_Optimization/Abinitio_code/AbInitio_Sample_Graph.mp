
# Ab Initio Sample Graph Specification (NOT a GDE-importable production MP file)
# Generated for design/reference purposes only.

GRAPH: CUSTOMER_ORDER_REGION_PROCESSING

INPUT_FILE CUSTOMER
 -> NORMALIZE_CUSTOMER
 -> SORT_CUSTOMER (key=customer_id)

INPUT_FILE ORDERS
 -> SORT_ORDERS (key=customer_id)

JOIN CUSTOMER_ORDERS
 left=SORT_CUSTOMER
 right=SORT_ORDERS
 condition=customer_id

INPUT_TABLE REGION_MASTER
 -> SORT_REGION (key=REGION_ID)

JOIN REGION_ENRICHMENT
 left=CUSTOMER_ORDERS
 right=SORT_REGION
 condition=region_id=REGION_ID

REFORMAT ADD_TAX

ROLLUP CUSTOMER_TOTAL
 group_by=customer_id

DEDUP_SORTED CUSTOMER_DEDUP
 key=customer_id

OUTPUT_FILE CUSTOMER_SUMMARY
