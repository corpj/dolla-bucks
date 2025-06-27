-- See New Payments By Date --
-- See New Payments By Date --

SELECT
	s.clientID, 
	p.AsOfDate, 
  CASE
    WHEN p.CR_DR IN ('credit','cr') 
    THEN p.Amount
    ELSE p.Amount * - 1
    END AS amount,
	CONCAT_WS(' | ','Regular PNC Payment | pnc_id = ',s.pnc_id,s.matched_payid) AS Notes,
 	s.pnc_reference AS payment_id,
  4 AS payment_type 

FROM
	standardized_pnc_mapping AS s
	INNER JOIN
	pnc_currentday_split AS p
	ON 
		s.pnc_id = p.ID
	LEFT JOIN
	payments_az AS paz
	ON 
		s.pnc_reference = paz.payment_id
WHERE
	p.AsOfDate >= [$ASOFDATE] AND
  p.applied != 2 AND
	paz.payment_id IS NULL AND
  length(s.pnc_reference)= 14 AND
  s.clientID IS NOT NULL
ORDER BY 
  p.AsOfDate;

  
INSERT INTO payments_az ( clientID, PmtDate, amount, Notes, payment_id, payment_type)
SELECT
	s.clientID, 
	p.AsOfDate, 
  CASE
    WHEN p.CR_DR IN ('credit','cr') 
    THEN p.Amount
    ELSE p.Amount * - 1
    END AS amount,
	CONCAT_WS(' | ','Regular PNC Payment | pnc_id = ',s.pnc_id,s.matched_payid) AS Notes,
 	s.pnc_reference AS payment_id,
  4 AS payment_type 

FROM
	standardized_pnc_mapping AS s
	INNER JOIN
	pnc_currentday_split AS p
	ON 
		s.pnc_id = p.ID
	LEFT JOIN
	payments_az AS paz
	ON 
		s.pnc_reference = paz.payment_id
WHERE
	p.AsOfDate >= [$ASOFDATE] AND
  p.applied != 2 AND
	paz.payment_id IS NULL AND
  length(s.pnc_reference)= 14 AND
  s.clientID IS NOT NULL;
