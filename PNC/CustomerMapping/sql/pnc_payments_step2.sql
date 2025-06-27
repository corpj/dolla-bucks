
-- Then map the records in access --

SELECT
  s.id,
  s.matched_payid,
  p.clientID,
  p.CustomerID,
  p.CompanyID,
  p.company_name,
  p.EmployerID,
  p.employer_name
FROM
  standardized_pnc_mapping s
  LEFT JOIN pnc_customer_payid p ON s.matched_payid = p.matched_payid
WHERE
  p.matched_payid IS NULL;


--  View MAPPED the Records first --

SELECT
  s.id,
  s.matched_payid,
  p.clientID,
  p.CustomerID,
  p.CompanyID,
  p.company_name,
  p.EmployerID,
  p.employer_name
FROM
  standardized_pnc_mapping s
  INNER JOIN pnc_customer_payid p ON s.matched_payid = p.matched_payid
WHERE
  s.clientID IS NULL
  AND p.clientID IS NOT NULL;
  
-- This query will update the clientIDs to reflect what has already been mapped.
  
UPDATE standardized_pnc_mapping s
INNER JOIN pnc_customer_payid p ON s.matched_payid = p.matched_payid
SET s.clientID = p.clientID,
s.customerID = p.CustomerID,
s.companyID = p.CompanyID,
s.company_name = p.company_name,
s.employerID = p.EmployerID,
s.employer_name = p.employer_name
WHERE
  s.clientID IS NULL
  AND p.clientID IS NOT NULL;
  
  -- INSERT NEW pnc_customer_payIDs to be mapped
INSERT INTO pnc_customer_payid (matched_payid, CustName, CompName, CompID)
SELECT DISTINCT
	new.matched_payid, 
	new.CustName, 
	new.CompName, 
	new.CompID
FROM
	PNC_UnMapped_NewPayments_view AS new
	LEFT JOIN
	pnc_customer_payid AS payid
	ON 
		new.matched_payid = payid.matched_payid
WHERE
	payid.matched_payid IS NULL
