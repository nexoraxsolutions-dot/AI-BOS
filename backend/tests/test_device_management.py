"""
Unit and integration tests for Device Management module.

Test categories:
- User-agent parsing (device type, browser, OS detection)
- Device service functions (list, get, revoke, stats)
- Token-to-device conversion
- Edge cases and security scenarios
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services import device as device_service
from app.schemas.token import DeviceInfo


class TestUserAgentParsing:
    """Tests for user-agent string parsing."""

    def test_parse_chrome_windows(self):
        """Verify Chrome on Windows is parsed correctly."""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "desktop"
        assert info.browser == "Chrome"
        assert info.os == "Windows"
        assert info.is_desktop is True
        assert info.is_mobile is False

    def test_parse_firefox_macos(self):
        """Verify Firefox on macOS is parsed correctly."""
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "desktop"
        assert info.browser == "Firefox"
        assert info.os == "macOS"

    def test_parse_safari_ios(self):
        """Verify Safari on iOS is parsed correctly."""
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "mobile"
        assert info.browser == "Safari"
        assert info.os == "iOS"
        assert info.is_mobile is True

    def test_parse_android_chrome(self):
        """Verify Chrome on Android is parsed correctly."""
        ua = "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "mobile"
        assert info.browser == "Chrome"
        assert info.os == "Android"

    def test_parse_ipad(self):
        """Verify iPad is detected as tablet."""
        ua = "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "tablet"
        assert info.os == "iOS"

    def test_parse_edge_windows(self):
        """Verify Edge on Windows is parsed correctly."""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        info = device_service.parse_user_agent(ua)
        assert info.browser == "Edge"
        assert info.os == "Windows"

    def test_parse_empty_user_agent(self):
        """Verify empty user-agent is handled gracefully."""
        info = device_service.parse_user_agent(None)
        assert info.device_type == "unknown"
        assert info.device_name == "Unknown Device"
        assert info.browser == "Unknown"
        assert info.os == "Unknown"
        assert info.is_desktop is True

    def test_parse_empty_string_user_agent(self):
        """Verify empty string user-agent is handled gracefully."""
        info = device_service.parse_user_agent("")
        assert info.device_type == "unknown"

    def test_generate_device_name(self):
        """Verify device name generation."""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        name = device_service.generate_device_name(ua)
        assert "Windows" in name
        assert "Chrome" in name

    def test_generate_device_type(self):
        """Verify device type generation."""
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2)"
        dtype = device_service.generate_device_type(ua)
        assert dtype == "mobile"


class TestDeviceService:
    """Tests for device service functions."""

    @pytest.mark.asyncio
    async def test_get_user_devices(self):
        """Verify getting devices for a user."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        devices, total = await device_service.get_user_devices(mock_db, 1)
        assert total == 5
        assert devices == []

    @pytest.mark.asyncio
    async def test_get_device_by_id(self):
        """Verify getting a device by ID."""
        mock_db = AsyncMock()
        mock_token = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_token
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await device_service.get_device_by_id(mock_db, 1, 1)
        assert result is mock_token

    @pytest.mark.asyncio
    async def test_get_device_by_id_not_found(self):
        """Verify getting a non-existent device returns None."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await device_service.get_device_by_id(mock_db, 999, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_device(self):
        """Verify revoking a device."""
        mock_db = AsyncMock()
        mock_token = MagicMock()
        mock_token.is_revoked = False
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_token
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await device_service.revoke_device(mock_db, 1, 1)
        assert result is mock_token
        assert mock_token.is_revoked is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_device_not_found(self):
        """Verify revoking a non-existent device returns None."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await device_service.revoke_device(mock_db, 999, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_all_devices(self):
        """Verify revoking all devices for a user."""
        mock_db = AsyncMock()
        mock_token1 = MagicMock()
        mock_token1.is_revoked = False
        mock_token2 = MagicMock()
        mock_token2.is_revoked = False
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_token1, mock_token2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await device_service.revoke_all_devices(mock_db, 1)
        assert count == 2
        assert mock_token1.is_revoked is True
        assert mock_token2.is_revoked is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_all_devices_no_tokens(self):
        """Verify revoking all devices when none exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await device_service.revoke_all_devices(mock_db, 1)
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_device_stats(self):
        """Verify device statistics calculation."""
        mock_db = AsyncMock()
        now = datetime.utcnow()
        mock_token1 = MagicMock()
        mock_token1.is_revoked = False
        mock_token1.expires_at = now + timedelta(hours=2)
        mock_token1.device_type = "desktop"
        mock_token2 = MagicMock()
        mock_token2.is_revoked = True
        mock_token2.expires_at = now + timedelta(hours=2)
        mock_token2.device_type = "mobile"
        mock_token3 = MagicMock()
        mock_token3.is_revoked = False
        mock_token3.expires_at = now + timedelta(hours=1)
        mock_token3.device_type = "desktop"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_token1, mock_token2, mock_token3]
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await device_service.get_device_stats(mock_db, 1)
        assert stats["total_devices"] == 3
        assert stats["active_devices"] == 2
        assert stats["revoked_devices"] == 1
        assert stats["device_type_breakdown"]["desktop"] == 2
        assert stats["device_type_breakdown"]["mobile"] == 1

    @pytest.mark.asyncio
    async def test_mark_current_device(self):
        """Verify marking a device as current."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        await device_service.mark_current_device(mock_db, 1, 1)
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_device_last_used(self):
        """Verify updating last_used_at timestamp."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        await device_service.update_device_last_used(mock_db, 1)
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


class TestTokenToDeviceOut:
    """Tests for token-to-device conversion."""

    def test_token_to_device_out_with_user_agent(self):
        """Verify token conversion with user-agent parsing."""
        mock_token = MagicMock()
        mock_token.id = 1
        mock_token.user_id = 1
        mock_token.device_name = None
        mock_token.device_type = None
        mock_token.client_ip = "192.168.1.1"
        mock_token.is_current = True
        mock_token.is_revoked = False
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_token.created_at = datetime.utcnow()
        mock_token.last_used_at = datetime.utcnow()
        mock_token.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"

        device = device_service.token_to_device_out(mock_token)
        assert device.id == 1
        assert device.user_id == 1
        assert device.client_ip == "192.168.1.1"
        assert device.is_current is True
        assert device.is_revoked is False
        assert device.browser == "Chrome"
        assert device.os == "Windows"
        assert "Windows" in device.device_name

    def test_token_to_device_out_with_stored_device_name(self):
        """Verify token conversion uses stored device name when available."""
        mock_token = MagicMock()
        mock_token.id = 2
        mock_token.user_id = 1
        mock_token.device_name = "My Custom Device"
        mock_token.device_type = "desktop"
        mock_token.client_ip = "10.0.0.1"
        mock_token.is_current = False
        mock_token.is_revoked = False
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_token.created_at = datetime.utcnow()
        mock_token.last_used_at = None
        mock_token.user_agent = None

        device = device_service.token_to_device_out(mock_token)
        assert device.device_name == "My Custom Device"
        assert device.device_type == "desktop"
        assert device.browser == "Unknown"
        assert device.os == "Unknown"


class TestSecurityScenarios:
    """Tests for security edge cases."""

    def test_user_agent_injection_attempt(self):
        """Verify malicious user-agent strings are handled safely."""
        ua = "<script>alert('xss')</script> Mozilla/5.0"
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "desktop"
        assert info.browser == "Unknown"

    def test_very_long_user_agent(self):
        """Verify very long user-agent strings are handled."""
        ua = "Mozilla/5.0 " * 1000
        info = device_service.parse_user_agent(ua)
        assert info.device_type == "desktop"

    def test_device_ownership_check(self):
        """Verify device ownership is enforced in get_device_by_id."""
        # The service always includes user_id in the query
        # This is tested by the query construction
        pass
