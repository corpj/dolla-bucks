-- THIS QUERY inserts and updates all the the pnc_compid for mappings --

INSERT IGNORE INTO pnc_compid_company_mapping (pnc_comp_id, pnc_comp_name, internal_company_id, internal_company_name, employer_id, employer_name, mapped_by, mapped_on, mapping_notes, active)
SELECT DISTINCT
    s.canonical_compid, 
    s.canonical_compname, 
    s.companyID, 
    s.company_name, 
    s.employerID, 
    s.employer_name,
    'JEREMY' AS mapped_by,
    CURRENT_TIMESTAMP AS mapped_on,
    'cleaned and unique, matched lower, trim on hash' AS mapping_notes,
    1 AS active
FROM
    standardized_pnc_mapping s
    LEFT JOIN pnc_compid_company_mapping p
    ON 
        MD5(CONCAT(
            IFNULL(TRIM(s.canonical_compid), ''),
            IFNULL(LOWER(TRIM(s.canonical_compname)), ''),
            IFNULL(CAST(s.companyID AS CHAR), ''),
            IFNULL(LOWER(TRIM(s.company_name)), ''),
            IFNULL(CAST(s.employerID AS CHAR), ''),
            IFNULL(LOWER(TRIM(s.employer_name)), '')
        )) = p.hash_fields
WHERE 
    p.hash_fields IS NULL 
    AND (
        s.canonical_compid IS NOT NULL 
        AND s.canonical_compname IS NOT NULL 
        AND s.companyid IS NOT NULL 
        AND s.company_name IS NOT NULL 
        AND s.employerID IS NOT NULL 
        AND s.employer_name IS NOT NULL
    );