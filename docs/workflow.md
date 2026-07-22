# Workflow: SC-022 Initial Assessment

## 1. Business Process Overview
The **Initial Assessment (SC-022)** is the critical 3rd step in the New Admission Flow. It captures the baseline health, functional, and cognitive status of a Resident upon admission to the Nursing Home. 

This workflow ensures compliance with clinical standards and triggers downstream operational and financial processes.

## 2. Step-by-Step Flow
1. **Initiation**: 
   - A Nurse or Admission Coordinator accesses the resident's profile.
   - The user selects "New Admission Flow" -> "Step 3: Initial Assessment".
2. **Data Collection**:
   - **Activities of Daily Living (ADL)**: 8 items scored 0-4.
   - **Instrumental ADL (IADL)**: 8 items scored 0-1 (Lawton scale for personalization).
   - **Clinical Data**: Vitals, Cognitive Status, Diagnoses (ICD-10), and Allergies.
3. **Submission & E-Signature**:
   - User reviews the inputs and clicks `Save Assessment -> triggers LOC calc`.
   - The system validates all inputs. 
   - The assessment is finalized and cryptographically e-signed by the user.

## 3. Operational Cascade
As per the Business Requirements Document (BRD), submitting this assessment triggers the following automated cascade:
- **Level of Care (LOC) Tier Calculation**: The ADL Subtotal directly drives the LOC Tier (M1-US-08).
- **Care Plan Personalization**: IADL scores and Diagnoses inform the personalized care plan.
- **Staffing Acuity Update**: The newly calculated LOC is pushed to the Staffing module to adjust required nurse-to-patient ratios.
- **Billing Engine Integration**: The LOC tier determines the base per-diem rate for the resident's billing cycle.

## 4. Compliance & Immutability (BR-05 / NFR-02)
- **Chart Lock**: Once the assessment is submitted and e-signed, it becomes **immutable**. Any future changes require a formal "Amendment" process with strict audit trails. 
- The initial assessment record cannot be altered or deleted.
