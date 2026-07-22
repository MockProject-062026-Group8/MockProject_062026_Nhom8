# Defects & Edge Cases: SC-022

## 1. Known Defects & Limitations
- **DEF-001**: Diagnoses input does not auto-complete ICD-10 codes. Users must manually type the ICD-10 code, which may lead to typos or invalid codes that the Billing engine might reject downstream.
- **DEF-002**: Vitals input fields lack strict client-side numeric validation. A user could enter "120/80" in the Systolic field instead of splitting it, which will cause a `ValueError` during POST processing.
- **DEF-003**: The UI does not explicitly show the user's e-signature name on the screen before they click save, potentially causing confusion about who is signing the document.

## 2. Edge Cases to Handle
- **Network Disconnection During Save**: 
  - *Risk*: If the request times out, the LOC cascade might trigger but the chart lock fails. 
  - *Mitigation*: The `views.py` save logic must be wrapped in a `with transaction.atomic():` block to ensure all cascade operations and the lock happen simultaneously or rollback completely.
- **Simultaneous Editing**:
  - *Risk*: Two nurses open the Initial Assessment for the same resident at the same time.
  - *Mitigation*: Implementation uses optimistic concurrency control. If Nurse A saves, the record is locked. Nurse B's subsequent save attempt will be rejected with a 403 Permission Denied.
- **Missing Vital Signs**:
  - *Risk*: Sometimes a resident refuses vitals upon admission.
  - *Mitigation*: The Vitals fields are technically nullable in the database, but the UI should prompt a warning modal if fields are empty: "Are you sure you want to proceed without vitals?"

## 3. Compliance Risks
- **Data Export**: If a database admin queries the `AssessmentDetail` table directly from SSMS, they can see PHI. Column-level encryption for clinical notes and diagnosis strings must be enforced at the SQL Server level using Always Encrypted.
