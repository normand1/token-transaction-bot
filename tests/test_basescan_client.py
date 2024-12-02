import pytest
import requests
from unittest.mock import patch, MagicMock
from src.basescan_client import BaseScanClient


@pytest.fixture
def client():
    """Fixture for creating a BaseScanClient instance."""
    with patch.dict("os.environ", {"BASESCAN_API_KEY": "test_api_key", "BASE_SCAN_URL": "https://api.basescan.org", "BASE_RPC_URL": "https://base-mainnet.g.alchemy.com/v2/your-api-key"}):
        return BaseScanClient()


def test_init(client):
    """Test BaseScanClient initialization."""
    assert client.api_key == "test_api_key"
    assert client.url == "https://api.basescan.org/api"
    assert client.w3 is not None


@patch("requests.get")
def test_fetch_contract_abi_success(mock_get, client):
    """Test successful ABI fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "1", "result": '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"}]'}
    mock_get.return_value = mock_response

    abi = client.fetch_contract_abi("0x1234567890123456789012345678901234567890")

    assert isinstance(abi, list)
    assert len(abi) == 1
    assert abi[0]["name"] == "name"
    assert abi[0]["type"] == "function"


@patch("requests.get")
def test_fetch_contract_abi_api_error(mock_get, client):
    """Test ABI fetch with API error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "0", "result": "Contract source code not verified"}
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="BaseScan API error: Contract source code not verified"):
        client.fetch_contract_abi("0x1234567890123456789012345678901234567890")


@patch("requests.get")
def test_fetch_contract_abi_network_error(mock_get, client):
    """Test ABI fetch with network error."""
    mock_get.side_effect = requests.RequestException("Network error")

    with pytest.raises(ValueError, match="Failed to fetch ABI from BaseScan: Network error"):
        client.fetch_contract_abi("0x1234567890123456789012345678901234567890")


@patch.object(BaseScanClient, "fetch_contract_abi")
def test_load_contract_success(mock_fetch_abi, client):
    """Test successful contract loading."""
    mock_abi = [{"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
    mock_fetch_abi.return_value = mock_abi

    contract = client.load_contract("0x1234567890123456789012345678901234567890")

    assert contract is not None
    assert client.contract_address == "0x1234567890123456789012345678901234567890"
    assert client.contract_abi == mock_abi


@patch.object(BaseScanClient, "fetch_contract_abi")
def test_load_contract_empty_abi(mock_fetch_abi, client):
    """Test contract loading with empty ABI."""
    mock_fetch_abi.return_value = []

    with pytest.raises(ValueError, match="ABI is empty"):
        client.load_contract("0x1234567890123456789012345678901234567890")


@patch.object(BaseScanClient, "fetch_contract_abi")
def test_load_contract_fetch_error(mock_fetch_abi, client):
    """Test contract loading with ABI fetch error."""
    mock_fetch_abi.side_effect = ValueError("API error")

    with pytest.raises(ValueError, match="Failed to fetch ABI for contract"):
        client.load_contract("0x1234567890123456789012345678901234567890")
