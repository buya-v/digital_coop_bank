"""Repository for E-2 `KycSubmission` rows.

A KycSubmission carries a NOT-NULL `member_id` FK, so it is created only AT
PROMOTION — when a Member finally exists (DEC-4). The in-flight KYC handle
(`kyc_inquiry_id` / `kyc_status`) lives on the onboarding draft until then. This
layer only inserts the resolved submission; the promotion rules live in the KYC
service.
"""
from __future__ import annotations

import datetime
import uuid

from app.models.identity import (
    KycDocumentType,
    KycResult,
    KycScreeningResult,
    KycSubmission,
)
from app.repositories.base import BaseRepository


class KycSubmissionRepository(BaseRepository[KycSubmission]):
    model = KycSubmission

    def create(
        self,
        *,
        member_id: uuid.UUID,
        kyc_inquiry_id: str,
        document_type: KycDocumentType,
        ocr_extracted_fields: dict[str, object],
        screening_result: KycScreeningResult,
        result: KycResult,
        result_reasons: dict[str, object],
        evidence_refs: dict[str, object],
        submitted_at: datetime.datetime,
        resolved_at: datetime.datetime,
    ) -> KycSubmission:
        """Insert the resolved KYC submission and flush so its UUID PK populates."""
        submission = KycSubmission(
            member_id=member_id,
            kyc_inquiry_id=kyc_inquiry_id,
            document_type=document_type,
            ocr_extracted_fields=ocr_extracted_fields,
            screening_result=screening_result,
            result=result,
            result_reasons=result_reasons,
            evidence_refs=evidence_refs,
            submitted_at=submitted_at,
            resolved_at=resolved_at,
        )
        self.add(submission)
        self.flush()
        return submission
