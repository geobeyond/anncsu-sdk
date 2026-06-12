# SPDX-FileCopyrightText: 2025-present Geobeyond <info@geobeyond.it>
# SPDX-License-Identifier: MIT
"""Validated Odonimo model with ANNCSU business rules.

This module provides a validated version of the Richiesta model that
enforces the business rules of the ANNCSU "Aggiornamento odonimi" API.

Rules (derived from the OAS spec):

1. ``tipo_operazione`` must be one of ``"I"`` (inserimento), ``"R"``
   (aggiornamento), ``"S"`` (soppressione). Enforced via enum.
2. ``codcom`` is mandatory for every operation.
3. ``progr_nazionale`` is mandatory for ``R`` and ``S``, assigned by
   ANNCSU for ``I``.
4. ``dug`` is mandatory for ``I`` and ``R``; NOT allowed for ``S``.
5. ``maxLength`` constraints from the OAS spec are enforced explicitly
   (Pydantic does not enforce ``maxLength`` from OpenAPI by default).
   The OAS quirk ``denom_localita: 151`` (off-by-one vs 150) is
   preserved as-is.
6. If ``provvedimento.flag_delibera`` is ``"0"`` or ``"1"``, then
   ``provvedimento.data`` and ``provvedimento.protocollo`` are required.
7. ``aut_prefettura.data_pref`` and ``protocollo_pref`` are mutually
   required: if one is set, the other must be set too.

8. ``provvedimento.flag_delibera``, when set, must be one of ``"0"``
   .. ``"4"`` (OAS: "valori numerici da 0 a 4").
9. Date fields (``provvedimento.data``, ``aut_prefettura.data_pref``,
   ``data_valid_amm``), when set, must be valid ``dd/MM/yyyy`` calendar
   dates (OAS examples: "10/10/2023").
10. ``data_valid_amm`` must not be in the future, for every operation
    (OAS: "minore o uguale della data corrente per inserimento e
    soppressione. Per aggiornamento anche >= della precedente" —
    'anche' is additive). The R-only half ("≥ della precedente") is
    delegated to the server: it requires the historical value.
"""

from __future__ import annotations

import datetime
import re
from typing import Optional

from pydantic import model_validator

from anncsu.odonimi.errors.odonimo_validation import (
    CodcomRequiredError,
    DataValidAmmInFutureError,
    DugNotAllowedForDeleteError,
    DugRequiredError,
    FlagDeliberaInvalidValueError,
    FlagDeliberaMissingFieldsError,
    InvalidDateFormatError,
    OdonimoMaxLengthError,
    PrefetturaMutexError,
    ProgrNazionaleRequiredError,
    TipoOperazioneError,
)
from anncsu.odonimi.models.richiestaoperazione import Richiesta, TipoOperazione

VALID_OPERAZIONI = {"I", "R", "S"}

# maxLength constraints from OAS spec (in characters).
# Note: denom_localita is 151 (off-by-one OAS quirk, preserved as-is).
MAX_LENGTHS: dict[str, int] = {
    "progr_nazionale": 10,
    "codice_comunale": 30,
    "dug": 30,
    "denom_delibera": 120,
    "denom_in_lingua_1": 150,
    "denom_in_lingua_2": 150,
    "denom_localita": 151,
}

# maxLength constraints for nested objects (validated separately).
PROVVEDIMENTO_MAX_LENGTHS: dict[str, int] = {"protocollo": 70}
AUT_PREFETTURA_MAX_LENGTHS: dict[str, int] = {"protocollo_pref": 70}

VALID_FLAG_DELIBERA = {"0", "1", "2", "3", "4"}

# Strict dd/MM/yyyy: strptime alone accepts non-zero-padded dates.
_DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


class ValidatedOdonimo(Richiesta):
    """Odonimo Richiesta model with ANNCSU business rule validation.

    Extends the generated ``Richiesta`` model from Speakeasy to enforce
    the operation-aware rules (I/R/S) and maxLength constraints
    described in the OAS spec.

    Raises:
        TipoOperazioneError: ``tipo_operazione`` missing or not in {I,R,S}
        CodcomRequiredError: ``codcom`` missing
        ProgrNazionaleRequiredError: ``progr_nazionale`` missing for R or S
        DugRequiredError: ``dug`` missing for I or R
        DugNotAllowedForDeleteError: ``dug`` set for S operation
        OdonimoMaxLengthError: a string field exceeds its OAS maxLength
        FlagDeliberaMissingFieldsError: ``provvedimento.flag_delibera`` is
            "0" or "1" but ``data`` or ``protocollo`` are missing
        PrefetturaMutexError: ``aut_prefettura.data_pref`` and
            ``protocollo_pref`` are not both set or both unset
        FlagDeliberaInvalidValueError: ``provvedimento.flag_delibera``
            is set but not one of "0".."4"
        InvalidDateFormatError: a date field is not a valid dd/MM/yyyy
            calendar date
        DataValidAmmInFutureError: ``data_valid_amm`` is in the future
            for I or S
    """

    @model_validator(mode="after")
    def validate_odonimo_rules(self) -> "ValidatedOdonimo":
        """Apply ANNCSU business rules in a single pass."""
        op = self._operation_value()

        # Rule 1: tipo_operazione must be I / R / S
        if op is None or op not in VALID_OPERAZIONI:
            raise TipoOperazioneError(value=op)

        # Rule 5 first: maxLength constraints (precise per-field errors).
        self._validate_max_lengths()

        # Rule 2: codcom required (always)
        if not self._get_value(self.codcom):
            raise CodcomRequiredError()

        # Rule 3: progr_nazionale required for R/S
        if op in {"R", "S"} and not self._get_value(self.progr_nazionale):
            raise ProgrNazionaleRequiredError(operazione=op)

        # Rule 4: dug required for I/R, forbidden for S
        has_dug = self._get_value(self.dug) is not None
        if op in {"I", "R"} and not has_dug:
            raise DugRequiredError(operazione=op)
        if op == "S" and has_dug:
            raise DugNotAllowedForDeleteError(value=str(self.dug))

        # Rule 6: provvedimento.flag_delibera in {0,1} → data+protocollo required
        # Rule 8: flag_delibera range; Rule 9: data format
        if self.provvedimento is not None:
            self._validate_provvedimento()

        # Rule 7: aut_prefettura.data_pref ↔ protocollo_pref mutex
        # Rule 9: data_pref format
        if self.aut_prefettura is not None:
            self._validate_aut_prefettura()

        # Rules 9-10: data_valid_amm format and not-in-future for I/S
        self._validate_data_valid_amm(op)

        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _operation_value(self) -> Optional[str]:
        """Extract tipo_operazione as a plain string (handle enum/None)."""
        value = self.tipo_operazione
        if value is None:
            return None
        if isinstance(value, TipoOperazione):
            return value.value
        return str(value)

    def _get_value(self, field_value) -> Optional[str]:
        """Extract actual value, treating UNSET sentinel and None as missing."""
        from anncsu.common.sdk.types import UNSET
        from anncsu.common.sdk.types.basemodel import Unset

        if field_value is None:
            return None
        if isinstance(field_value, Unset) or field_value is UNSET:
            return None
        s = str(field_value)
        return s if s else None

    def _validate_max_lengths(self) -> None:
        """Enforce OAS maxLength on top-level string fields."""
        for field_name, max_length in MAX_LENGTHS.items():
            value = self._get_value(getattr(self, field_name, None))
            if value is not None and len(value) > max_length:
                raise OdonimoMaxLengthError(
                    field_name=field_name,
                    value=value,
                    max_length=max_length,
                )

        if self.provvedimento is not None:
            for field_name, max_length in PROVVEDIMENTO_MAX_LENGTHS.items():
                value = self._get_value(getattr(self.provvedimento, field_name, None))
                if value is not None and len(value) > max_length:
                    raise OdonimoMaxLengthError(
                        field_name=f"provvedimento.{field_name}",
                        value=value,
                        max_length=max_length,
                    )

        if self.aut_prefettura is not None:
            for field_name, max_length in AUT_PREFETTURA_MAX_LENGTHS.items():
                value = self._get_value(getattr(self.aut_prefettura, field_name, None))
                if value is not None and len(value) > max_length:
                    raise OdonimoMaxLengthError(
                        field_name=f"aut_prefettura.{field_name}",
                        value=value,
                        max_length=max_length,
                    )

    def _parse_date(
        self, field_name: str, value: Optional[str]
    ) -> Optional[datetime.date]:
        """Rule 9: parse a dd/MM/yyyy date, raising on invalid format."""
        if value is None:
            return None
        if not _DATE_PATTERN.match(value):
            raise InvalidDateFormatError(field_name=field_name, value=value)
        try:
            return datetime.datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            raise InvalidDateFormatError(field_name=field_name, value=value) from None

    def _validate_provvedimento(self) -> None:
        """Rules 6, 8, 9 on the nested provvedimento object."""
        self._parse_date("provvedimento.data", self._get_value(self.provvedimento.data))

        flag = self._get_value(self.provvedimento.flag_delibera)
        if flag is not None and flag not in VALID_FLAG_DELIBERA:
            raise FlagDeliberaInvalidValueError(value=flag)
        if flag not in {"0", "1"}:
            return

        missing: list[str] = []
        if self._get_value(self.provvedimento.data) is None:
            missing.append("data")
        if self._get_value(self.provvedimento.protocollo) is None:
            missing.append("protocollo")
        if missing:
            raise FlagDeliberaMissingFieldsError(
                flag_delibera=flag,
                missing_fields=tuple(missing),
            )

    def _validate_aut_prefettura(self) -> None:
        """Rules 7 and 9 on the nested aut_prefettura object."""
        self._parse_date(
            "aut_prefettura.data_pref",
            self._get_value(self.aut_prefettura.data_pref),
        )

        has_data = self._get_value(self.aut_prefettura.data_pref) is not None
        has_protocollo = (
            self._get_value(self.aut_prefettura.protocollo_pref) is not None
        )
        if has_data != has_protocollo:
            raise PrefetturaMutexError(
                has_data_pref=has_data,
                has_protocollo_pref=has_protocollo,
            )

    def _validate_data_valid_amm(self, op: str) -> None:
        """Rules 9-10: format always; never in the future (any operation).

        OAS: "minore o uguale della data corrente per inserimento e
        soppressione. Per aggiornamento anche >= della precedente" —
        'anche' is additive, so the <= today bound applies to R too.
        Only the '>= precedente' half is delegated to the server.
        """
        value = self._get_value(self.data_valid_amm)
        parsed = self._parse_date("data_valid_amm", value)
        if parsed is None:
            return
        if parsed > datetime.date.today():
            raise DataValidAmmInFutureError(operazione=op, value=value)


__all__ = ["ValidatedOdonimo"]
