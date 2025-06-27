# PNC Customer Mapping Workflow

This document outlines the process used to map the raw PNC transactions in the cloudclusters.spider_sync_DEV databse.

## Workflow

**Step 1:** Inserting payments via PNC/import_pnc_payments.py
**Step 2:** Count Number of Payments and see payments to insert
```sql
-- Count Number Of Payments

SELECT
  COUNT(*)
FROM
  pnc_currentday_split
WHERE
  AsOfDate >= '2025-05-28'
  AND applied != 2  
  AND BaiControl != 475 ;


SELECT
  *
FROM
  pnc_currentday_split
WHERE
  AsOfDate >= '2025-05-28'
  AND applied != 2  
    AND BaiControl != 475 ;
 
```
**Step 3:** Insert Standardardized Mapped Records into 'standardized_pnc_mapping'
This step takes the already mapped customers from pnc_customer_payid and updates the individual payment record in 'standardized_pnc_mapping'

```sql
-- VIEW Mapped Records
SELECT
	new.pnc_id, 
	new.AsOfDate, 
	new.pnc_reference, 
	new.matched_payid, 
	new.CompName, 
	new.CompID, 
	new.CustName
FROM
	NewStandardized_PNC_Mappings_to_insert AS new
	LEFT JOIN
	standardized_pnc_mapping AS map
	ON 
		new.pnc_id = map.pnc_id
WHERE
	map.pnc_id IS NULL

-- Insert New Standardized Records

INSERT INTO standardized_pnc_mapping (pnc_id, AsOfDate, pnc_reference, matched_payid, canonical_compname, canonical_compid, canonical_custname)
SELECT
	new.pnc_id, 
	new.AsOfDate, 
	new.pnc_reference, 
	new.matched_payid, 
	new.CompName, 
	new.CompID, 
	new.CustName
FROM
	NewStandardized_PNC_Mappings_to_insert AS new
	LEFT JOIN
	standardized_pnc_mapping AS map
	ON 
		new.pnc_id = map.pnc_id
WHERE
	map.pnc_id IS NULL

```

SELECT * FROM pnc_customer_payid WHERE clientID IS NULL;

