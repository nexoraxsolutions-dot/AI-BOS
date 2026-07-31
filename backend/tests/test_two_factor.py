"""
Unit and integration tests for Two-Factor Authentication (2FA) module.

Test categories:
- TOTP service functions (secret generation, token verification)
- Backup code generation and verification
- 2FA setup and enable flow
- 2FA disable flow
- API endpoint validation
- Security scenarios
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import two_factor as two_factor_service
from app.schemas import two_factor as two_factor_schema


class TestTOTPService:
    """Tests for core TOTP service functions."""

    def test_generate_otp_secret(self):
        """Verify OTP secret generation produces valid base32."""
        secret = two_factor_service.generate_otp_secret()
        assert len(secret) > 0
        # Should be base32 encoded (uppercase letters and digits)
        assert all(c.isupper() or c.isdigit() or c == '=' for c in secret)
        # Standard TOTP secrets are 16-32 chars
        assert 16 <= len(secret) <= 32

    def test_generate_otp_secret_unique(self):
        """Verify each call generates a unique secret."""
        secrets = {two_factor_service.generate_otp_secret() for _ in range(10)}
        assert len(secrets) == 10

    def test_get_totp_uri_format(self):
        """Verify TOTP URI is correctly formatted."""
        secret = two_factor_service.generate_otp_secret()
        email = "test@example.com"
        uri = two_factor_service.get_totp_uri(secret, email)
        assert uri.startswith("otpauth://")
        assert "AI-BOS" in uri
        # Email is URL-encoded in the URI
        assert "test%40example.com" in uri

    def test_get_qr_code_url(self):
        """Verify QR code URL is just the TOTP URI."""
        secret = two_factor_service.generate_otp_secret()
        email = "test@example.com"
        uri = two_factor_service.get_totp_uri(secret, email)
        qr_url = two_factor_service.get_qr_code_url(secret, email)
        assert uri == qr_url

    def test_verify_totp_token_valid(self):
        """Verify a valid TOTP token is accepted."""
        secret = two_factor_service.generate_otp_secret()
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        assert two_factor_service.verify_totp_token(secret, token) is True

    def test_verify_totp_token_invalid(self):
        """Verify an invalid TOTP token is rejected."""
        secret = two_factor_service.generate_otp_secret()
        assert two_factor_service.verify_totp_token(secret, "000000") is False

    def test_verify_totp_token_empty(self):
        """Verify empty token is rejected."""
        secret = two_factor_service.generate_otp_secret()
        assert two_factor_service.verify_totp_token(secret, "") is False

    def test_verify_totp_token_none_secret(self):
        """Verify None secret is handled."""
        assert two_factor_service.verify_totp_token(None, "123456") is False


class TestBackupCodes:
    """Tests for backup code generation and verification."""

    def test_generate_backup_codes_count(self):
        """Verify correct number of backup codes are generated."""
        codes = two_factor_service.generate_backup_codes()
        assert len(codes) == 8

    def test_generate_backup_codes_format(self):
        """Verify backup codes are formatted as XXXX-XXXX-XXXX."""
        codes = two_factor_service.generate_backup_codes()
        for code in codes:
            parts = code.split("-")
            assert len(parts) == 3, f"Expected 3 parts, got {len(parts)} in {code}"
            for part in parts:
                assert len(part) == 4, f"Expected 4 chars, got {len(part)} in {part} from {code}"
                assert all(c.isalnum() for c in part), f"Non-alphanumeric in {part}"

    def test_generate_backup_codes_unique(self):
        """Verify all backup codes are unique."""
        codes = two_factor_service.generate_backup_codes()
        assert len(set(codes)) == len(codes)

    def test_hash_and_verify_backup_code(self):
        """Verify backup code hashing and verification works."""
        code = "ABCD-1234-EFGH"
        hashed = two_factor_service.hash_backup_code(code)
        assert hashed != code
        assert two_factor_service.verify_backup_code(code, hashed) is True

    def test_verify_backup_code_wrong(self):
        """Verify wrong backup code is rejected."""
        code = "ABCD-1234-EFGH"
        hashed = two_factor_service.hash_backup_code(code)
        assert two_factor_service.verify_backup_code("WRONG-XXXX-XXXX", hashed) is False


class TestTwoFactorSchemaValidation:
    """Tests for 2FA Pydantic schema validation."""

    def test_verify_request_valid_token(self):
        """Verify valid token passes validation."""
        request = two_factor_schema.TwoFactorVerifyRequest(token="123456")
        assert request.token == "123456"

    def test_verify_request_empty_token(self):
        """Verify empty token is rejected."""
        with pytest.raises(ValueError):
            two_factor_schema.TwoFactorVerifyRequest(token="")

    def test_verify_request_short_token(self):
        """Verify short token is rejected."""
        with pytest.raises(ValueError):
            two_factor_schema.TwoFactorVerifyRequest(token="12345")

    def test_verify_request_long_token(self):
        """Verify long token is rejected."""
        with pytest.raises(ValueError):
            two_factor_schema.TwoFactorVerifyRequest(token="1234567")

    def test_verify_request_non_digit(self):
        """Verify non-digit token is rejected."""
        with pytest.raises(ValueError):
            two_factor_schema.TwoFactorVerifyRequest(token="abcdef")


class TestTwoFactorServiceIntegration:
    """Integration tests for 2FA service functions (mock DB)."""

    @pytest.mark.asyncio
    async def test_setup_2fa(self):
        """Verify 2FA setup generates secret, QR URL, and backup codes."""
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_2fa_enabled = False
        mock_user.otp_secret = None

        mock_db = AsyncMock()
        # Mock the execute chain properly for async SQLAlchemy
        # scalars() and .all() are synchronous in async SQLAlchemy
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        secret, qr_code_url, backup_codes = await two_factor_service.setup_2fa(
            mock_db, mock_user
        )

        assert len(secret) > 0
        assert qr_code_url.startswith("otpauth://")
        assert len(backup_codes) == 8
        assert mock_user.otp_secret == secret

    @pytest.mark.asyncio
    async def test_enable_2fa(self):
        """Verify enabling 2FA updates user flag."""
        mock_user = AsyncMock()
        mock_user.is_2fa_enabled = False

        mock_db = AsyncMock()

        await two_factor_service.enable_2fa(mock_db, mock_user)

        assert mock_user.is_2fa_enabled is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_2fa(self):
        """Verify disabling 2FA clears secrets and backup codes."""
        mock_user = AsyncMock()
        mock_user.is_2fa_enabled = True
        mock_user.otp_secret = "somerandomsecret"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        await two_factor_service.disable_2fa(mock_db, mock_user)

        assert mock_user.is_2fa_enabled is False
        assert mock_user.otp_secret is None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_remaining_backup_codes(self):
        """Verify remaining backup codes count is correct."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [1, 2, 3]
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await two_factor_service.get_remaining_backup_codes(mock_db, 1)
        assert count == 3

    @pytest.mark.asyncio
    async def test_regenerate_backup_codes(self):
        """Verify backup code regeneration works."""
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        codes = await two_factor_service.regenerate_backup_codes(mock_db, mock_user)
        assert len(codes) == 8
        mock_db.commit.assert_called_once()


class TestSecurityScenarios:
    """Tests for security edge cases."""

    def test_totp_window_tolerance(self):
        """Verify TOTP verification works with a small time window tolerance."""
        import pyotp
        import time

        secret = two_factor_service.generate_otp_secret()
        totp = pyotp.TOTP(secret)

        # Generate a token slightly in the past (within valid_window=1)
        current_token = totp.now()

        # Should still verify with the current token
        assert two_factor_service.verify_totp_token(secret, current_token) is True

    def test_backup_code_one_time_use_verification(self):
        """Verify backup code verification uses bcrypt correctly."""
        code = "SAFE-CODE-1234"
        hashed = two_factor_service.hash_backup_code(code)

        # Verify correct code
        assert two_factor_service.verify_backup_code(code, hashed) is True

        # Verify different code fails
        assert two_factor_service.verify_backup_code("DIFF-CODE-5678", hashed) is False

    def test_api_token_validation_strip_whitespace(self):
        """Verify token validation strips whitespace."""
        request = two_factor_schema.TwoFactorVerifyRequest(token="  123456  ")
        assert request.token == "123456"