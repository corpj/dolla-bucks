# Wells Fargo Payment Description Parsing Implementation
**Created:** 2025-04-03
**Modified:** 2025-04-03

## Overview
This documentation details the implementation of the Wells Fargo payment description parsing functionality in the `parse_wf_descriptions.py` script. The parser extracts structured data from WF payment description strings following a specific pattern.

## Description Pattern
Wells Fargo payment descriptions follow this pattern:
```
[CompName] [ALLOTMENT/SALARY] [MMDDYY] XXXXX[CustID] [CustName] FR [FRValue] #[Number] SUB [SUBValue] ACCT [ACCTValue]
```

Example:
```
DFAS-CLEVELAND ALLOTMENT 071516 XXXXX0745 MALONE CARY E FR 0000000003 #003 SUB ACCT 000004942806886
```

## Implementation Details

### Core Parsing Strategy
The implementation uses the 6-digit MMDDYY date as the central anchor point for parsing all other fields:

1. Extract the date using regex pattern matching
2. Split the description into text before and after the date
3. Extract fields from these sections using specific patterns

### Key Field Extraction Rules
- **Date**: 6-digit MMDDYY format in the middle of the string
- **desc_name**: The word right before the date (e.g., "ALLOTMENT", "SALARY")
- **CompName**: The text before desc_name, with special handling for known companies
- **CustID**: Numbers following the "XXXXX" pattern
- **CustName**: Text between CustID and "FR"
- **FullSubAccount**: Numbers between "FR" and "#"
- **SubAccount**: Numbers following "#"

### Special Handling
- **Company Names**: Special handling for known companies like "DFAS-CLEVELAND" and "MPLS USPS PDC MN FED"
- **Data Types**: Proper conversion to integers for numeric fields
- **SQL Compatibility**: Renamed MySQL reserved word 'Desc' to 'desc_name'

## Usage

### Basic Usage
```
python payments/parse_wf_descriptions.py
```

### Specific Record Testing
```
python payments/parse_wf_descriptions.py --record-id 1096 --verbose
```

### Date-Based Processing
```
python payments/parse_wf_descriptions.py --test-date "2016-07-15" --verbose
```

## Validation
The implementation was successfully tested with record ID 1096, confirming accurate parsing of all fields:
- CompName: DFAS-CLEVELAND
- desc_name: ALLOTMENT
- Date: 71516
- CustID: 0745
- CustName: MALONE CARY E
- FR: FR
- FullSubAccount: 3

## Database Integration
The parser updates the following fields in the `wf_payments_split` table:
- CompName
- desc_name
- Date
- CustID
- CustName
- FR
- FullSubAccount
- SubAccount
- SUB
- ACCT
- AcctNo

## Error Handling
- Verbose logging option for detailed debugging
- Proper error handling for date pattern matching
- Database connection error handling
- Record update failure detection

## Future Improvements
- Add batch processing for large datasets
- Implement pattern recognition for new company names
- Add statistical reporting on parsing success rates
