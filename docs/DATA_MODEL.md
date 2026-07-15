# Data Model — MedCloud (MongoDB)

MongoDB is a **NoSQL, document** database. Hierarchy: a **Database** holds **Collections**,
each Collection holds **Documents** (JSON-like objects). We use one database (`medcloud`)
with the collections below. In demo mode the same shapes live in an in-memory mongomock DB.

> Schema note: MongoDB is flexible (schema-on-read-ish), but we keep consistent shapes in
> the models. We store the patient **birth_date** and calculate age on read, so age never
> goes stale.

## Collections

### users
```json
{ "_id": ObjectId, "full_name": "Dr. Dana Cohen", "email": "doctor@example.com",
  "password_hash": "<werkzeug hash>", "role": "admin|doctor|pharmacist",
  "created_at": ISODate }
```
Index: unique `email`. Passwords stored only as salted hashes.

### patients
```json
{ "_id": ObjectId, "national_id": "312345678", "first_name": "Yael", "last_name": "Bar",
  "gender": "female|male|other", "pregnancy_status": false, "lactation_status": false,
  "birth_date": "1990-05-14", "photo": "patients/<uuid>.png",
  "email": "...", "phone": "...", "created_at": ISODate, "updated_at": ISODate }
```
Index: unique `national_id`. Derived on read: `age`.

### visits
```json
{ "_id": ObjectId, "patient_id": "...", "patient_national_id": "312345678",
  "patient_name": "Yael Bar", "doctor_id": "...", "doctor_name": "Dr. Dana Cohen",
  "complaints": "...", "diagnosis": "...", "created_at": ISODate }
```

### prescriptions
```json
{ "_id": ObjectId, "patient_id": "...", "patient_national_id": "312345678",
  "patient_name": "Yael Bar", "doctor_id": "...", "doctor_name": "...",
  "visit_id": "...", "diagnosis": "...",
  "items": [ { "drug_name": "Amoxicillin", "dosage": "500 mg",
               "frequency": "3x/day", "duration": "7 days", "notes": "after meals" } ],
  "status": "open|dispensed|cancelled", "source": "digital|handwritten_upload",
  "pdf_path": "generated_pdfs/prescription_<id>.pdf",
  "pdf_url": "https://res.cloudinary.com/...", "pdf_storage": "cloudinary|local",
  "ocr_text": null, "ai_document_validation_result": null,
  "created_at": ISODate, "dispensed_at": null, "dispensed_by": null }
```
Indexes: `patient_national_id`, `status`. **PrescriptionItem** is an *embedded* document
(no separate collection) — a natural fit for MongoDB.

### uploaded_prescriptions
```json
{ "_id": ObjectId, "patient_national_id": "312345678", "patient_name": "...",
  "image_path": "prescriptions_rx/<uuid>.png",
  "ai_document_validation_result": { "valid": true, "method": "heuristic|hosted_vision",
      "message": "...", "details": { ... } },
  "ocr_text": "Ibuprofen 200mg ...", "ocr_source": "Cloud OCR|Tesseract (local)|manual",
  "ocr_message": null, "status": "open|dispensed", "source": "handwritten_upload",
  "uploaded_by": "Pharmacist Noa Levi", "created_at": ISODate,
  "dispensed_at": null, "dispensed_by": null }
```

### service_query_logs
```json
{ "_id": ObjectId, "service": "diagnosis_search|clinical_trials|side_effects",
  "query": "acute bronchitis", "source": "Tavily|OpenFDA|ClinicalTrials.gov",
  "result_count": 5, "user_id": "...", "user_name": "...", "created_at": ISODate }
```
Index: `created_at`. Audit trail of every external consultation.

## Entity relationships
- A **Patient** has many **Visits** and many **Prescriptions** (linked by `patient_national_id`).
- A **Visit** may lead to a **Prescription** (`visit_id`).
- A **Prescription** embeds many **PrescriptionItems**.
- An **UploadedPrescription** is an independent, pharmacist-created handwritten record.
- **ServiceQueryLog** records consultations by any user.

## Enumerations
- Prescription status: `open`, `dispensed`, `cancelled`.
- Prescription source: `digital`, `handwritten_upload`.
- Roles: `admin`, `doctor`, `pharmacist`.

## Future (Kafka bonus)
`PrescriptionDispensedEvent` — published when a prescription is dispensed
(`{type: "prescription.dispensed", prescription_id, patient_national_id, source}`). Currently
logged to the console by `kafka_service.py` (documented stub).
