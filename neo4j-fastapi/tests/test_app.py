import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver to avoid requiring a real database."""
    with patch("neo4j.GraphDatabase.driver") as mock_driver:
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.get.return_value = 1
        mock_record.single.return_value = mock_record
        mock_record.keys.return_value = ["ok"]
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value = mock_session
        mock_driver_instance.close = Mock()
        mock_driver.return_value = mock_driver_instance
        yield mock_driver


@pytest.fixture
def client(mock_neo4j_driver):
    """Create test client with mocked Neo4j."""
    # Set required env var before importing app
    os.environ["NEO4J_PASSWORD"] = "test_password"
    from app import app

    # Trigger startup event
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test the root HTML endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "neo4j-fastapi" in response.text.lower()


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "neo4j" in data
    assert data["status"] == "ok"
    assert data["neo4j"] is True


def test_cypher_endpoint_with_valid_query(client, mock_neo4j_driver):
    """Test executing a valid Cypher query."""
    # Mock the query result
    mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
    mock_record = Mock()
    mock_record.keys.return_value = ["count"]
    mock_record.get.return_value = 42
    mock_session.run.return_value = [mock_record]

    response = client.post(
        "/cypher",
        json={"query": "MATCH (n) RETURN count(n) AS count"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert "count" in data
    assert "capped" in data
    assert isinstance(data["rows"], list)


def test_cypher_endpoint_with_empty_query(client):
    """Test that empty queries are rejected."""
    response = client.post(
        "/cypher",
        json={"query": "   "}
    )
    assert response.status_code == 400
    assert "Empty query" in response.json()["detail"]


def test_cypher_endpoint_with_invalid_query(client, mock_neo4j_driver):
    """Test handling of Cypher errors."""
    # Mock a Cypher error
    mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.side_effect = Exception("Cypher syntax error")

    response = client.post(
        "/cypher",
        json={"query": "INVALID CYPHER"}
    )
    assert response.status_code == 400
    assert "Cypher error" in response.json()["detail"]


def test_missing_password_env_var():
    """Test that app fails to start without NEO4J_PASSWORD."""
    # Clear the environment variable
    if "NEO4J_PASSWORD" in os.environ:
        del os.environ["NEO4J_PASSWORD"]

    with pytest.raises(ValueError, match="NEO4J_PASSWORD environment variable is required"):
        import importlib
        import sys

        # Remove app from cache if it exists
        if "app" in sys.modules:
            del sys.modules["app"]

        # Import should raise ValueError
        import app
