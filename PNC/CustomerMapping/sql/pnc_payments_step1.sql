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
 

-- Insert New standardized Mappings

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