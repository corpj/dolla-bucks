-- Step3: Find and insert unmapped wf_payID ---- after this, map pnc then run it again.
SELECT
	v.matched_payid, 
	v.clientID, 
	v.customerID, 
	v.companyID, 
	v.company_name, 
	v.employerID, 
	v.employer_name, 
	v.CustName, 
	v.CompID, 
	v.CompName, 
	v.hashed_payid
FROM
	mapping_unique_pnc_customer_payid_all_view AS v
	LEFT JOIN
	pnc_customer_payid AS pid
	ON 
		v.hashed_payid = pid.hashed_payid
WHERE
	pid.matched_payid IS NULL;

-- TO INSERT --
INSERT INTO pnc_customer_payid (matched_payid, clientID, customerID, companyID, company_name, employerID, employer_name, CustName, CompID, CompName)
SELECT
	v.matched_payid, 
	v.clientID, 
	v.customerID, 
	v.companyID, 
	v.company_name, 
	v.employerID, 
	v.employer_name, 
	v.CustName, 
	v.CompID, 
	v.CompName
FROM
	mapping_unique_pnc_customer_payid_all_view AS v
	LEFT JOIN
	pnc_customer_payid AS pid
	ON 
		v.hashed_payid = pid.hashed_payid
WHERE
	pid.matched_payid IS NULL;
  
  
    -- INSERT NEW pnc_customer_payIDs to be mapped
INSERT INTO pnc_customer_payid (matched_payid, CustName, CompName, CompID)
SELECT
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
