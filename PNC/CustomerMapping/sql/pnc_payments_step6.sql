-- VIEW Payments That have not Been Applied --

SELECT
	pnc.ID, 
	pnc.AsOfDate, 
	pnc.Reference, 
	pnc.applied
FROM
	pnc_currentday_split AS pnc
	INNER JOIN
	payments_az AS paz
	ON 
		pnc.Reference = paz.payment_id
WHERE
	pnc.AsOfDate >= '2024-01-01'
  AND applied != 2
ORDER BY 
  pnc.AsOfDate DESC;
  
  -- UPDATE Payments That have not Been Applied --
UPDATE pnc_currentday_split pnc
	INNER JOIN
	payments_az AS paz
	ON 
		pnc.Reference = paz.payment_id
SET applied = 2
 
WHERE
	pnc.AsOfDate >= '2024-01-01'
  AND applied != 2
