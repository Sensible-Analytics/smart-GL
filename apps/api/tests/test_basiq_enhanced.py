"""
Tests for DSPY-generated BasiqClient (basiq_enhanced.py)
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.basiq_enhanced import BasiqClient


class TestBasiqClient:
    @pytest.fixture
    def client(self):
        return BasiqClient("test-api-key")

    @pytest.mark.asyncio
    async def test_get_token(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-token-123", "expires_in": 3600}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response
            MockClient.return_value = mock_client

            token = await client.get_token()
            assert token == "test-token-123"
            assert client.access_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_create_user(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "user-123"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response
            MockClient.return_value = mock_client

            user_id = await client.create_user("test@example.com", "+61412345678")
            assert user_id == "user-123"

    @pytest.mark.asyncio
    async def test_get_user(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "user-123", "email": "test@example.com"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.return_value = mock_response
            MockClient.return_value = mock_client

            user = await client.get_user("user-123")
            assert user["id"] == "user-123"

    @pytest.mark.asyncio
    async def test_delete_user(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.delete.return_value = mock_response
            MockClient.return_value = mock_client

            result = await client.delete_user("user-123")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_accounts(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "acc-1", "name": "Account 1"},
                {"id": "acc-2", "name": "Account 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.return_value = mock_response
            MockClient.return_value = mock_client

            accounts = await client.get_accounts("user-123")
            assert len(accounts) == 2

    @pytest.mark.asyncio
    async def test_get_transactions(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "txn-1", "amount": 100.00},
                {"id": "txn-2", "amount": -50.00},
            ],
            "links": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.return_value = mock_response
            MockClient.return_value = mock_client

            txns = await client.get_transactions("user-123", from_date="2024-01-01")
            assert len(txns) == 2

    @pytest.mark.asyncio
    async def test_get_identity(self, client):
        client.access_token = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "John Doe",
            "verified": True
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.return_value = mock_response
            MockClient.return_value = mock_client

            identity = await client.get_identity("user-123")
            assert identity["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_token_auto_fetch(self, client):
        assert client.access_token is None
        
        async def mock_post(url, **kwargs):
            if "/token" in url:
                m = MagicMock()
                m.json.return_value = {"access_token": "auto-token"}
                m.raise_for_status = MagicMock()
                return m
            m = MagicMock()
            m.json.return_value = {"id": "user-123"}
            m.raise_for_status = MagicMock()
            return m
        
        async def mock_get(url, **kwargs):
            m = MagicMock()
            m.json.return_value = {"data": []}
            m.raise_for_status = MagicMock()
            return m

        with patch("services.basiq_enhanced.httpx.AsyncClient") as MockClient:
            mock = AsyncMock()
            mock.post.side_effect = mock_post
            mock.get.side_effect = mock_get
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            
            MockClient.return_value = mock
            
            user_id = await client.create_user("test@example.com", "+61412345678")
            assert user_id == "user-123"
            assert client.access_token == "auto-token"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])