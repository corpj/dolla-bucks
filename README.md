# dolla-bucks

## **PNC PAYMENTS:** To Run PNC Payments 

1. Activate the venv

```bash
source venv/Scripts/activate
```

2. Add Payments Files 
- Move files from X:\WF AND X:\pnc\_new_ to WSL directory

Move PNC payments into "\\wsl.localhost\Ubuntu\home\corpj\projects\dolla-bucks\PaymentFiles"


3. RUN PNC Payments

```bash
python PNC/import_pnc_payments.py
```


## **WF PAYMENTS:** To Run WF Payments 

1. python /home/corpj/projects/dolla-bucks/WF/wf_excel_importer.py

```bash
python WF/wf_excel_importer.py

```



## **EAA PAYMENTS:** To Run EAA Payments 

1. python /home/corpj/projects/dolla-bucks/WF/wf_excel_importer.py

```bash
python /EAA/process_eaa_payments.py 

```

