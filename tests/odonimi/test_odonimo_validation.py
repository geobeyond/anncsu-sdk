# SPDX-FileCopyrightText: 2025-present Geobeyond <info@geobeyond.it>
# SPDX-License-Identifier: MIT
"""Tests for Odonimo model validation.

Business rules from OAS spec (tipo_operazione ∈ {I, R, S}):

1. tipo_operazione must be one of "I", "R", "S" (enum)
2. codcom is required for every operation
3. progr_nazionale is required for R and S
4. dug is required for I and R, NOT allowed for S
5. maxLength constraints from OAS:
   - progr_nazionale: 10        codice_comunale: 30
   - dug: 30                    denom_delibera: 120
   - denom_in_lingua_1: 150     denom_in_lingua_2: 150
   - denom_localita: 151
   - provvedimento.protocollo: 70
   - aut_prefettura.protocollo_pref: 70
6. If provvedimento.flag_delibera ∈ {"0","1"}, then
   provvedimento.data and provvedimento.protocollo are required.
7. aut_prefettura.data_pref and protocollo_pref are mutex:
   if one is set, the other must be set too.

8. provvedimento.flag_delibera, when set, must be one of "0".."4".
9. Date fields (provvedimento.data, aut_prefettura.data_pref,
   data_valid_amm) must be valid dd/MM/yyyy calendar dates.
10. data_valid_amm must not be in the future for I/S. The R rule
    ("≥ della precedente") stays server-side: it needs the previous
    historical value.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anncsu.odonimi.errors.odonimo_validation import (
    CodcomRequiredError,
    DataValidAmmInFutureError,
    DugNotAllowedForDeleteError,
    DugRequiredError,
    FlagDeliberaInvalidValueError,
    FlagDeliberaMissingFieldsError,
    InvalidDateFormatError,
    OdonimoMaxLengthError,
    OdonimoValidationError,
    PrefetturaMutexError,
    ProgrNazionaleRequiredError,
    TipoOperazioneError,
)
from anncsu.odonimi.models.validated import ValidatedOdonimo


def get_validation_error_cause(exc_info) -> Exception:
    """Extract the original error from Pydantic's ValidationError."""
    errors = exc_info.value.errors()
    if errors and "ctx" in errors[0] and "error" in errors[0]["ctx"]:
        return errors[0]["ctx"]["error"]
    return exc_info.value


# Default kwargs to instantiate a minimal valid odonimo for each operation.
# Tests override only the fields under examination.
_VALID_INSERT = dict(
    codcom="A062",
    tipo_operazione="I",
    dug="VIA",
    denom_delibera="DELLE ORCHIDEE",
)

_VALID_REPLACE = dict(
    codcom="A062",
    tipo_operazione="R",
    progr_nazionale="2000449",
    dug="VIA",
    denom_delibera="DELLE ORCHIDEE",
)

_VALID_DELETE = dict(
    codcom="A062",
    tipo_operazione="S",
    progr_nazionale="2000449",
)


# ---------------------------------------------------------------------------
# 1. tipo_operazione validation
# ---------------------------------------------------------------------------


class TestOdonimoTipoOperazioneValidation:
    """Tests for tipo_operazione field validation."""

    def test_tipo_operazione_I_valid(self) -> None:
        odonimo = ValidatedOdonimo(**_VALID_INSERT)
        assert odonimo.tipo_operazione == "I"

    def test_tipo_operazione_R_valid(self) -> None:
        odonimo = ValidatedOdonimo(**_VALID_REPLACE)
        assert odonimo.tipo_operazione == "R"

    def test_tipo_operazione_S_valid(self) -> None:
        odonimo = ValidatedOdonimo(**_VALID_DELETE)
        assert odonimo.tipo_operazione == "S"

    def test_tipo_operazione_invalid_value_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", tipo_operazione="X", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        # Pydantic enum validation may fire before our custom check.
        assert isinstance(cause, (TipoOperazioneError, ValidationError))

    def test_tipo_operazione_missing_invalid(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, TipoOperazioneError)


# ---------------------------------------------------------------------------
# 2. codcom required (always)
# ---------------------------------------------------------------------------


class TestOdonimoCodcomRequired:
    """Tests that codcom is required for every operation."""

    def test_insert_without_codcom_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(tipo_operazione="I", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, CodcomRequiredError)

    def test_replace_without_codcom_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(tipo_operazione="R", progr_nazionale="2000449", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, CodcomRequiredError)

    def test_delete_without_codcom_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(tipo_operazione="S", progr_nazionale="2000449")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, CodcomRequiredError)


# ---------------------------------------------------------------------------
# 3. progr_nazionale required for R/S
# ---------------------------------------------------------------------------


class TestOdonimoProgrNazionaleDependency:
    """Tests for progr_nazionale requirement based on tipo_operazione."""

    def test_insert_without_progr_nazionale_valid(self) -> None:
        """I does not require progr_nazionale (assigned by API)."""
        odonimo = ValidatedOdonimo(**_VALID_INSERT)
        assert odonimo.progr_nazionale is None

    def test_replace_requires_progr_nazionale(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", tipo_operazione="R", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, ProgrNazionaleRequiredError)
        assert "R" in str(cause)

    def test_delete_requires_progr_nazionale(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", tipo_operazione="S")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, ProgrNazionaleRequiredError)
        assert "S" in str(cause)


# ---------------------------------------------------------------------------
# 4. dug required for I/R, NOT allowed for S
# ---------------------------------------------------------------------------


class TestOdonimoDugDependency:
    """Tests for dug requirement / prohibition based on tipo_operazione."""

    def test_insert_requires_dug(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", tipo_operazione="I")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DugRequiredError)
        assert "I" in str(cause)

    def test_replace_requires_dug(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                codcom="A062", tipo_operazione="R", progr_nazionale="2000449"
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DugRequiredError)
        assert "R" in str(cause)

    def test_delete_rejects_dug(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                codcom="A062",
                tipo_operazione="S",
                progr_nazionale="2000449",
                dug="VIA",
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DugNotAllowedForDeleteError)

    def test_delete_minimal_valid_without_dug(self) -> None:
        """S with only the identifying fields (codcom + progr_nazionale) is valid."""
        odonimo = ValidatedOdonimo(**_VALID_DELETE)
        assert odonimo.tipo_operazione == "S"
        assert odonimo.dug is None


# ---------------------------------------------------------------------------
# 5. maxLength constraints
# ---------------------------------------------------------------------------


class TestOdonimoMaxLengthValidation:
    """Tests for maxLength enforcement on string fields."""

    def test_progr_nazionale_max_length_10_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_REPLACE, "progr_nazionale": "1" * 11})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "progr_nazionale"

    def test_progr_nazionale_at_max_length_valid(self) -> None:
        odonimo = ValidatedOdonimo(**{**_VALID_REPLACE, "progr_nazionale": "1" * 10})
        assert odonimo.progr_nazionale == "1" * 10

    def test_dug_max_length_30_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "dug": "V" * 31})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "dug"

    def test_codice_comunale_max_length_30_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "codice_comunale": "C" * 31})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "codice_comunale"

    def test_denom_delibera_max_length_120_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "denom_delibera": "X" * 121})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "denom_delibera"

    def test_denom_in_lingua_1_max_length_150_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "denom_in_lingua_1": "L" * 151})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "denom_in_lingua_1"

    def test_denom_in_lingua_2_max_length_150_exceeded(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "denom_in_lingua_2": "L" * 151})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "denom_in_lingua_2"

    def test_denom_localita_max_length_151_exceeded(self) -> None:
        """OAS quirk: denom_localita is 151 (off-by-one vs 150)."""
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**{**_VALID_INSERT, "denom_localita": "L" * 152})
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoMaxLengthError)
        assert cause.field_name == "denom_localita"
        assert cause.max_length == 151

    def test_denom_localita_at_151_valid(self) -> None:
        odonimo = ValidatedOdonimo(**{**_VALID_INSERT, "denom_localita": "L" * 151})
        assert odonimo.denom_localita == "L" * 151


# ---------------------------------------------------------------------------
# 6. provvedimento.flag_delibera ∈ {"0","1"} → data+protocollo required
# ---------------------------------------------------------------------------


class TestOdonimoFlagDeliberaConditional:
    """Tests for flag_delibera conditional requirement of data + protocollo."""

    def test_flag_delibera_0_without_data_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **{
                    **_VALID_INSERT,
                    "provvedimento": {
                        "flag_delibera": "0",
                        "protocollo": "1234/abc",
                    },
                }
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, FlagDeliberaMissingFieldsError)
        assert "data" in cause.missing_fields

    def test_flag_delibera_1_without_protocollo_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **{
                    **_VALID_INSERT,
                    "provvedimento": {
                        "flag_delibera": "1",
                        "data": "10/10/2023",
                    },
                }
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, FlagDeliberaMissingFieldsError)
        assert "protocollo" in cause.missing_fields

    def test_flag_delibera_0_with_data_and_protocollo_valid(self) -> None:
        odonimo = ValidatedOdonimo(
            **{
                **_VALID_INSERT,
                "provvedimento": {
                    "flag_delibera": "0",
                    "data": "10/10/2023",
                    "protocollo": "1234/abc",
                },
            }
        )
        assert odonimo.provvedimento is not None
        assert odonimo.provvedimento.flag_delibera == "0"

    def test_flag_delibera_2_without_data_or_protocollo_valid(self) -> None:
        """flag_delibera != {0,1} → data/protocollo not enforced."""
        odonimo = ValidatedOdonimo(
            **{
                **_VALID_INSERT,
                "provvedimento": {"flag_delibera": "2"},
            }
        )
        assert odonimo.provvedimento.flag_delibera == "2"

    def test_no_provvedimento_valid(self) -> None:
        """provvedimento is optional."""
        odonimo = ValidatedOdonimo(**_VALID_INSERT)
        assert odonimo.provvedimento is None


# ---------------------------------------------------------------------------
# 7. aut_prefettura.data_pref ↔ protocollo_pref mutex
# ---------------------------------------------------------------------------


class TestOdonimoPrefetturaMutex:
    """Tests for aut_prefettura data_pref/protocollo_pref mutual requirement."""

    def test_data_pref_without_protocollo_pref_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **{
                    **_VALID_INSERT,
                    "aut_prefettura": {"data_pref": "10/10/2023"},
                }
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, PrefetturaMutexError)

    def test_protocollo_pref_without_data_pref_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **{
                    **_VALID_INSERT,
                    "aut_prefettura": {"protocollo_pref": "Prot.Gen.1234567"},
                }
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, PrefetturaMutexError)

    def test_both_fields_set_valid(self) -> None:
        odonimo = ValidatedOdonimo(
            **{
                **_VALID_INSERT,
                "aut_prefettura": {
                    "data_pref": "10/10/2023",
                    "protocollo_pref": "Prot.Gen.1234567",
                },
            }
        )
        assert odonimo.aut_prefettura is not None
        assert odonimo.aut_prefettura.data_pref == "10/10/2023"

    def test_no_aut_prefettura_valid(self) -> None:
        """aut_prefettura is optional."""
        odonimo = ValidatedOdonimo(**_VALID_INSERT)
        assert odonimo.aut_prefettura is None


# ---------------------------------------------------------------------------
# 8. Error hierarchy
# ---------------------------------------------------------------------------


class TestOdonimoValidationErrorHierarchy:
    """Tests that all errors inherit from OdonimoValidationError and ValueError."""

    def test_all_errors_inherit_from_odonimo_validation_error(self) -> None:
        for err_class in (
            TipoOperazioneError,
            CodcomRequiredError,
            ProgrNazionaleRequiredError,
            DugRequiredError,
            DugNotAllowedForDeleteError,
            OdonimoMaxLengthError,
            FlagDeliberaMissingFieldsError,
            PrefetturaMutexError,
        ):
            assert issubclass(err_class, OdonimoValidationError)

    def test_odonimo_validation_error_inherits_from_value_error(self) -> None:
        assert issubclass(OdonimoValidationError, ValueError)

    def test_catch_any_error_with_base_class(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(codcom="A062", dug="VIA")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, OdonimoValidationError)


# ---------------------------------------------------------------------------
# 9. Realistic integration scenarios
# ---------------------------------------------------------------------------


class TestOdonimoIntegration:
    """End-to-end realistic scenarios for I/R/S operations."""

    def test_insert_complete(self) -> None:
        odonimo = ValidatedOdonimo(
            codcom="A062",
            tipo_operazione="I",
            dug="VIA",
            denom_delibera="DELLE ORCHIDEE",
            denom_localita="CASAL PALOCCO",
            provvedimento={
                "data": "10/10/2023",
                "protocollo": "1234567/abc",
                "flag_delibera": "1",
            },
            aut_prefettura={
                "data_pref": "11/10/2023",
                "protocollo_pref": "Prot.Gen.1234567",
            },
            data_valid_amm="08/10/2024",
        )
        assert odonimo.tipo_operazione == "I"
        assert odonimo.dug == "VIA"
        assert odonimo.provvedimento.flag_delibera == "1"

    def test_replace_complete(self) -> None:
        odonimo = ValidatedOdonimo(
            codcom="A062",
            tipo_operazione="R",
            progr_nazionale="2000449",
            dug="VIA",
            denom_delibera="DEI TIGLI",
            provvedimento={"flag_delibera": "3"},
            data_valid_amm="08/10/2024",
        )
        assert odonimo.progr_nazionale == "2000449"

    def test_delete_minimal(self) -> None:
        odonimo = ValidatedOdonimo(
            codcom="A062",
            tipo_operazione="S",
            progr_nazionale="2000449",
            data_valid_amm="31/12/2025",
        )
        assert odonimo.tipo_operazione == "S"
        assert odonimo.data_valid_amm == "31/12/2025"


# ---------------------------------------------------------------------------
# 8. provvedimento.flag_delibera range (OAS: "valori numerici da 0 a 4")
# ---------------------------------------------------------------------------


class TestOdonimoFlagDeliberaRange:
    """flag_delibera, when set, must be one of '0'..'4'."""

    @pytest.mark.parametrize("flag", ["5", "9", "-1", "00", "01", " 1", "+1", "1.0"])
    def test_flag_delibera_out_of_range_raises(self, flag: str) -> None:
        """Strict set membership: numerically-plausible variants of valid
        values ('01', ' 1', '+1', ...) must be rejected too — pins the
        check against a future int()-based 'optimization'."""
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **_VALID_INSERT,
                provvedimento={"flag_delibera": flag},
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, FlagDeliberaInvalidValueError)

    def test_flag_delibera_non_numeric_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **_VALID_INSERT,
                provvedimento={"flag_delibera": "abc"},
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, FlagDeliberaInvalidValueError)

    @pytest.mark.parametrize("flag", ["0", "1", "2", "3", "4"])
    def test_flag_delibera_valid_values_accepted(self, flag: str) -> None:
        odonimo = ValidatedOdonimo(
            **_VALID_INSERT,
            provvedimento={
                "flag_delibera": flag,
                # data+protocollo always set: required anyway for 0/1
                "data": "10/10/2023",
                "protocollo": "1234567/abc",
            },
        )
        assert odonimo.provvedimento.flag_delibera == flag


# ---------------------------------------------------------------------------
# 9. Date format dd/MM/yyyy (provvedimento.data, data_pref, data_valid_amm)
# ---------------------------------------------------------------------------


class TestOdonimoDateFormat:
    """Date fields, when set, must be valid dd/MM/yyyy calendar dates."""

    def test_provvedimento_data_iso_format_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **_VALID_INSERT,
                provvedimento={
                    "flag_delibera": "1",
                    "data": "2023-10-10",
                    "protocollo": "1234567/abc",
                },
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, InvalidDateFormatError)

    def test_provvedimento_data_invalid_calendar_date_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **_VALID_INSERT,
                provvedimento={
                    "flag_delibera": "1",
                    "data": "31/02/2024",
                    "protocollo": "1234567/abc",
                },
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, InvalidDateFormatError)

    def test_data_pref_invalid_format_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(
                **_VALID_INSERT,
                aut_prefettura={
                    "data_pref": "10-10-2023",
                    "protocollo_pref": "Prot.Gen.1234567",
                },
            )
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, InvalidDateFormatError)

    def test_data_valid_amm_invalid_format_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**_VALID_INSERT, data_valid_amm="08.10.2024")
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, InvalidDateFormatError)

    def test_valid_dates_accepted(self) -> None:
        odonimo = ValidatedOdonimo(
            **_VALID_INSERT,
            provvedimento={
                "flag_delibera": "1",
                "data": "10/10/2023",
                "protocollo": "1234567/abc",
            },
            aut_prefettura={
                "data_pref": "10/10/2023",
                "protocollo_pref": "Prot.Gen.1234567",
            },
            data_valid_amm="08/10/2024",
        )
        assert odonimo.data_valid_amm == "08/10/2024"

    def test_error_message_names_the_field(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**_VALID_INSERT, data_valid_amm="not-a-date")
        cause = get_validation_error_cause(exc_info)
        assert "data_valid_amm" in str(cause)


# ---------------------------------------------------------------------------
# 10. data_valid_amm <= current date for I and S (client-side computable).
#     The R rule (>= previous value) stays server-side: needs history lookup.
# ---------------------------------------------------------------------------


class TestOdonimoDataValidAmmNotFuture:
    """For I/S, data_valid_amm must not be in the future."""

    @staticmethod
    def _future_date() -> str:
        import datetime

        future = datetime.date.today() + datetime.timedelta(days=30)
        return future.strftime("%d/%m/%Y")

    @staticmethod
    def _today() -> str:
        import datetime

        return datetime.date.today().strftime("%d/%m/%Y")

    def test_insert_future_data_valid_amm_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**_VALID_INSERT, data_valid_amm=self._future_date())
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DataValidAmmInFutureError)

    def test_delete_future_data_valid_amm_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**_VALID_DELETE, data_valid_amm=self._future_date())
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DataValidAmmInFutureError)

    def test_insert_today_valid(self) -> None:
        odonimo = ValidatedOdonimo(**_VALID_INSERT, data_valid_amm=self._today())
        assert odonimo.data_valid_amm == self._today()

    def test_replace_future_data_valid_amm_raises(self) -> None:
        """OAS reading: the '<= data corrente' bound applies to R too
        ("Per aggiornamento anche >= della precedente" — 'anche' is
        additive). Only the '>= previous' half stays server-side."""
        with pytest.raises(ValidationError) as exc_info:
            ValidatedOdonimo(**_VALID_REPLACE, data_valid_amm=self._future_date())
        cause = get_validation_error_cause(exc_info)
        assert isinstance(cause, DataValidAmmInFutureError)

    def test_replace_today_valid(self) -> None:
        odonimo = ValidatedOdonimo(**_VALID_REPLACE, data_valid_amm=self._today())
        assert odonimo.data_valid_amm == self._today()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
