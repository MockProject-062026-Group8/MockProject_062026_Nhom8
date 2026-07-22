# Implementation: SC-022 Initial Assessment

## 1. Technical Stack & Location
- **Framework**: Django
- **Database**: MS SQL Server (SSMS 22)
- **App Module**: `apps/medical/`
- **Key Files**: 
  - `apps/medical/models.py` (Data Structures)
  - `apps/medical/views.py` (Controller Logic)
  - `apps/medical/templates/medical/sc_022.html` (Presentation)

## 2. Data Models (SSMS 22 Schema)
- **`Assessment`**: Core table storing `resident_id`, `assessment_type`, `assessment_date`, `cognitive_status`, `allergies`, `clinical_notes`, `total_adl_score`, `total_iadl_score`, `is_locked`, `e_signed_by`.
- **`AssessmentDetail`**: EAV (Entity-Attribute-Value) table for ADL/IADL/Vitals (`item_key`, `score`, `value`).
- **`AssessmentDiagnosis`**: Stores `diagnosis_name`, `icd10_code`, `is_primary`.

## 3. Logic & Controller (`views.py`)
- **Routing**: `path('initial-assessment/<int:pk>/', views.initial_assessment, name='initial_assessment')`
- **GET Request**: 
  - Fetches `Resident` data.
  - Renders `sc_022.html` with pre-populated form context (ADL, IADL, Vitals).
- **POST Request**:
  1. Checks RBAC permissions (`medical.add_assessment`).
  2. Parses ADL/IADL radio inputs and calculates subtotals.
  3. Parses JSON string for Diagnoses (`diagnoses_json`).
  4. Triggers `obj.recalculate_scores()` and LOC engine.
  5. Locks the record (`is_locked = True`).

## 4. Compliance & Security (NFR-01 / NFR-02)
- **HIPAA Compliance (NFR-01)**:
  - All views require `@login_required` and strict RBAC checks.
  - Queries filtering by Resident ID validate that the user's facility access level matches the resident's facility.
  - Logging utilizes `logging.getLogger('django')` but deliberately masks PII (e.g., `Resident ID: ***`).
- **Immutability (BR-05 / NFR-02)**:
  - Before processing a POST request, the view checks `if existing_assessment.is_locked: raise PermissionDenied("Record is locked.")`.
  - Database triggers in SSMS 22 are implemented to reject `UPDATE` statements on the `Assessment` table where `is_locked = 1`.

## 5. UI/UX Implementation
- Replaced traditional dropdowns with 5-point and 2-point horizontal radio button arrays for ADL and IADL to match clinical entry speed requirements.
- Uses vanilla JS to handle dynamic Diagnosis adding/removing via hidden JSON input to avoid complex formsets.
