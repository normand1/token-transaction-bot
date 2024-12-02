"""Tests for the CLI interface."""

import pytest
from click.testing import CliRunner
from src.cli import cli
from unittest.mock import patch, MagicMock


@pytest.fixture
def runner():
    """Fixture for creating a CLI runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test the CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


@patch("src.cli.Web3Client")
@patch("src.cli.BaseScanClient")
def test_monitor_command_connection_error(mock_basescan, mock_web3, runner):
    """Test monitor command when connection fails."""
    # Setup mock
    mock_web3_instance = mock_web3.return_value
    mock_web3_instance.is_connected.return_value = False

    result = runner.invoke(cli, ["monitor", "--contract-address", "0x1234567890123456789012345678901234567890"])

    assert result.exit_code == 0
    assert "Error: Could not connect to Base L2" in result.output


@patch("src.cli.Web3Client")
@patch("src.cli.BaseScanClient")
def test_scan_command_connection_error(mock_basescan, mock_web3, runner):
    """Test scan command when connection fails."""
    # Setup mock
    mock_web3_instance = mock_web3.return_value
    mock_web3_instance.is_connected.return_value = False

    result = runner.invoke(cli, ["scan", "--contract-address", "0x1234567890123456789012345678901234567890"])

    assert result.exit_code == 0
    assert "Error: Could not connect to Base L2" in result.output


@patch("src.cli.Web3Client")
@patch("src.cli.BaseScanClient")
def test_scan_command_contract_error(mock_basescan, mock_web3, runner):
    """Test scan command when contract loading fails."""
    # Setup mocks
    mock_web3_instance = mock_web3.return_value
    mock_web3_instance.is_connected.return_value = True

    mock_basescan_instance = mock_basescan.return_value
    mock_basescan_instance.load_contract.side_effect = ValueError("Invalid contract")

    result = runner.invoke(cli, ["scan", "--contract-address", "0x1234567890123456789012345678901234567890"])

    assert result.exit_code == 0
    assert "Error loading contract ABI" in result.output


@patch("src.cli.Web3Client")
@patch("src.cli.BaseScanClient")
def test_scan_command_no_events(mock_basescan, mock_web3, runner):
    """Test scan command when no events are found."""
    # Setup mocks
    mock_web3_instance = mock_web3.return_value
    mock_web3_instance.is_connected.return_value = True
    mock_web3_instance.get_contract_transfers.return_value = []

    mock_basescan_instance = mock_basescan.return_value
    mock_basescan_instance.load_contract.return_value = MagicMock(address="0x1234")

    result = runner.invoke(cli, ["scan", "--contract-address", "0x1234567890123456789012345678901234567890"])

    assert result.exit_code == 0
    assert "No events found" in result.output
