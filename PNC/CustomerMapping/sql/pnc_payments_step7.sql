-- ========================================
-- Daily Payment Sync Script (pnc_payments_step7)
-- Temporarily disables triggers to avoid commit issues
-- ========================================

-- Step 1: Disable the triggers on payments_az table
DROP TRIGGER IF EXISTS after_payment_insert;
DROP TRIGGER IF EXISTS after_payment_update;
DROP TRIGGER IF EXISTS after_payment_delete;

-- Step 2: Run your payment sync INSERT
INSERT INTO spider_sync.payments_az (dev_id, clientID, PmtDate, amount, Notes, payment_type, payment_id)
SELECT
    devpaz.ID, 
    devpaz.clientID, 
    devpaz.PmtDate, 
    devpaz.amount, 
    devpaz.Notes, 
    devpaz.payment_type, 
    devpaz.payment_id
FROM
    spider_sync_DEV.payments_az AS devpaz
    LEFT JOIN
    spider_sync.payments_az AS prod_paz
    ON 
        devpaz.payment_id = prod_paz.payment_id
WHERE
    devpaz.PmtDate >= '2025-05-01' AND
    prod_paz.payment_id IS NULL;

-- Step 3: Recreate the triggers
-- INSERT Trigger
DELIMITER $$
CREATE TRIGGER after_payment_insert
    AFTER INSERT ON payments_az
    FOR EACH ROW
BEGIN
    DECLARE v_customer_id INT;
    
    -- Find the customer associated with this client
    SELECT cm.CustomerID INTO v_customer_id
    FROM customer_client_mapping cm
    WHERE cm.ClientID = NEW.clientID
    LIMIT 1;
    
    -- If a customer is found, update the payment summary
    IF v_customer_id IS NOT NULL THEN
        CALL UpdatePaymentSummary(v_customer_id);
    END IF;
END$$

-- UPDATE Trigger
CREATE TRIGGER after_payment_update
    AFTER UPDATE ON payments_az
    FOR EACH ROW
BEGIN
    DECLARE v_customer_id INT;
    
    -- Only proceed if relevant fields were changed
    IF NEW.amount != OLD.amount OR 
       NEW.PmtDate != OLD.PmtDate OR 
       NEW.payment_type != OLD.payment_type OR
       NEW.clientID != OLD.clientID THEN
       
        -- If the client ID changed, update both the old and new customer
        IF NEW.clientID != OLD.clientID THEN
            -- Handle old client ID
            SELECT cm.CustomerID INTO v_customer_id
            FROM customer_client_mapping cm
            WHERE cm.ClientID = OLD.clientID
            LIMIT 1;
            
            IF v_customer_id IS NOT NULL THEN
                CALL UpdatePaymentSummary(v_customer_id);
            END IF;
        END IF;
        
        -- Handle new/current client ID
        SELECT cm.CustomerID INTO v_customer_id
        FROM customer_client_mapping cm
        WHERE cm.ClientID = NEW.clientID
        LIMIT 1;
        
        IF v_customer_id IS NOT NULL THEN
            CALL UpdatePaymentSummary(v_customer_id);
        END IF;
    END IF;
END$$

-- DELETE Trigger
CREATE TRIGGER after_payment_delete
    AFTER DELETE ON payments_az
    FOR EACH ROW
BEGIN
    DECLARE v_customer_id INT;
    
    -- Find the customer associated with this client
    SELECT cm.CustomerID INTO v_customer_id
    FROM customer_client_mapping cm
    WHERE cm.ClientID = OLD.clientID
    LIMIT 1;
    
    -- If a customer is found, update the payment summary
    IF v_customer_id IS NOT NULL THEN
        CALL UpdatePaymentSummary(v_customer_id);
    END IF;
END$$

DELIMITER ;

-- Step 4: Optional - Manually update payment summaries for affected customers
-- (Only run if you want to ensure summaries are current after the sync)

-- Option A: Call UpdatePaymentSummary procedure for each affected customer
/*
DELIMITER $
CREATE TEMPORARY PROCEDURE RefreshAffectedCustomers()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE customer_id INT;
    
    -- Cursor to get all customers who had payments synced
    DECLARE customer_cursor CURSOR FOR
        SELECT DISTINCT ccm.CustomerID
        FROM customer_client_mapping ccm
        JOIN payments_az p ON ccm.ClientID = p.clientID
        WHERE p.PmtDate >= '2025-05-01'
        AND p.dev_id IS NOT NULL;  -- Only newly synced records
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN customer_cursor;
    
    read_loop: LOOP
        FETCH customer_cursor INTO customer_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Call the payment summary update for this customer
        CALL UpdatePaymentSummary(customer_id);
    END LOOP;
    
    CLOSE customer_cursor;
END$

-- Execute the refresh procedure
CALL RefreshAffectedCustomers()$

-- Clean up
DROP PROCEDURE RefreshAffectedCustomers$
DELIMITER ;

-- Option B: Simple timestamp update (if Option A doesn't work)
/*
UPDATE payment_summary ps
JOIN customer_client_mapping ccm ON ps.CustomerID = ccm.CustomerID
JOIN payments_az p ON ccm.ClientID = p.clientID
SET ps.LastUpdated = '2000-01-01 00:00:00'
WHERE p.PmtDate >= '2025-05-01'
AND p.dev_id IS NOT NULL;
*/