"""Unit tests for networking automation engine."""
import pytest
from app.generator import TopologyGenerator
from app.core import ConfigurationGenerator
from app.deployment import DeploymentExporter
from app.models import DeviceType, TopologyRequest
from app.utils import (
    generate_ip_subnet,
    allocate_ips_for_link,
    get_network_address,
    get_subnet_mask,
    get_wildcard_mask,
    generate_router_id,
)


class TestTopologyGenerator:
    """Tests for topology generation."""

    def test_generate_basic_topology(self):
        """Test generating a basic topology."""
        generator = TopologyGenerator(seed=42)
        topology = generator.generate(
            topology_name="test",
            num_routers=3,
            num_switches=1
        )

        assert topology.name == "test"
        assert len([d for d in topology.devices if d.device_type == DeviceType.ROUTER]) == 3
        assert len([d for d in topology.devices if d.device_type == DeviceType.SWITCH]) == 1
        assert len(topology.links) > 0

    def test_topology_connectivity(self):
        """Test that generated topology is connected."""
        generator = TopologyGenerator(seed=123)
        topology = generator.generate(
            topology_name="test",
            num_routers=5,
            num_switches=2
        )

        # Extract routers
        routers = [d.name for d in topology.devices if d.device_type == DeviceType.ROUTER]

        # Check that routers are connected
        connected_routers = set()
        for link in topology.links:
            if link.source_device in routers and link.destination_device in routers:
                connected_routers.add(link.source_device)
                connected_routers.add(link.destination_device)

        # At least most routers should be connected
        assert len(connected_routers) >= len(routers) - 1

    def test_reproducible_generation(self):
        """Test that same seed produces same topology."""
        seed = 999

        gen1 = TopologyGenerator(seed=seed)
        topo1 = gen1.generate("test", 4, 1)

        gen2 = TopologyGenerator(seed=seed)
        topo2 = gen2.generate("test", 4, 1)

        # Topologies should have same structure
        assert len(topo1.devices) == len(topo2.devices)
        assert len(topo1.links) == len(topo2.links)

    def test_invalid_router_count(self):
        """Test validation of router count."""
        generator = TopologyGenerator()

        with pytest.raises(ValueError):
            generator.generate("test", 1, 0)  # Less than 2 routers

        with pytest.raises(ValueError):
            generator.generate("test", 25, 0)  # More than 20 routers

    def test_invalid_switch_count(self):
        """Test validation of switch count."""
        generator = TopologyGenerator()

        with pytest.raises(ValueError):
            generator.generate("test", 3, -1)  # Negative switches

        with pytest.raises(ValueError):
            generator.generate("test", 3, 15)  # Too many switches


class TestConfigurationGenerator:
    """Tests for configuration generation."""

    def test_ospf_config_generation(self):
        """Test OSPF configuration generation."""
        generator = TopologyGenerator(seed=42)
        topology = generator.generate("test", 3, 0)

        config_gen = ConfigurationGenerator()
        routing_config = config_gen.generate_ospf_configs(topology)

        assert routing_config.topology_name == "test"
        assert routing_config.routing_protocol == "ospf"
        assert len(routing_config.ospf_configs) == 3  # 3 routers

    def test_ospf_config_includes_interfaces(self):
        """Test that OSPF configs include all interfaces."""
        generator = TopologyGenerator(seed=55)
        topology = generator.generate("test", 2, 0)

        config_gen = ConfigurationGenerator()
        routing_config = config_gen.generate_ospf_configs(topology)

        # Check that interfaces are configured
        for ospf_config in routing_config.ospf_configs:
            assert len(ospf_config.interfaces) > 0
            assert ospf_config.router_id is not None


class TestDeploymentExporter:
    """Tests for deployment export."""

    def test_containerlab_export(self):
        """Test Containerlab format export."""
        generator = TopologyGenerator(seed=77)
        topology = generator.generate("test", 3, 1)

        exporter = DeploymentExporter()
        containerlab_config = exporter.export_containerlab_topology(topology)

        assert "name" in containerlab_config
        assert "topology" in containerlab_config
        assert "nodes" in containerlab_config["topology"]
        assert "links" in containerlab_config["topology"]
        assert len(containerlab_config["topology"]["nodes"]) == 4  # 3 routers + 1 switch

    def test_yaml_export(self):
        """Test YAML format export."""
        generator = TopologyGenerator(seed=88)
        topology = generator.generate("test", 2, 0)

        exporter = DeploymentExporter()
        yaml_content = exporter.export_to_yaml(topology)

        assert "test" in yaml_content
        assert len(yaml_content) > 0


class TestUtilities:
    """Tests for utility functions."""

    def test_subnet_mask_calculation(self):
        """Test subnet mask calculation."""
        assert get_subnet_mask(24) == "255.255.255.0"
        assert get_subnet_mask(25) == "255.255.255.128"
        assert get_subnet_mask(16) == "255.255.0.0"
        assert get_subnet_mask(8) == "255.0.0.0"

    def test_wildcard_mask_calculation(self):
        """Test wildcard mask calculation."""
        assert get_wildcard_mask(24) == "0.0.0.255"
        assert get_wildcard_mask(16) == "0.0.255.255"
        assert get_wildcard_mask(25) == "0.0.0.127"

    def test_router_id_generation(self):
        """Test router ID generation."""
        rid1 = generate_router_id(0)
        rid2 = generate_router_id(1)
        rid3 = generate_router_id(100)

        assert rid1 != rid2
        assert rid2 != rid3
        assert rid1.count(".") == 3  # Valid IP format

    def test_ip_allocation(self):
        """Test IP address allocation."""
        source_ip, dest_ip = allocate_ips_for_link("10.1.1.0/24")

        assert source_ip != dest_ip
        assert source_ip.startswith("10.1.1.")
        assert dest_ip.startswith("10.1.1.")

    def test_network_address_extraction(self):
        """Test network address extraction."""
        network = get_network_address("10.1.1.129", 24)
        assert network == "10.1.1.0"

        network = get_network_address("192.168.1.100", 25)
        assert network == "192.168.1.0"


class TestModels:
    """Tests for Pydantic models."""

    def test_topology_request_validation(self):
        """Test TopologyRequest validation."""
        valid_request = TopologyRequest(
            name="test",
            num_routers=5,
            num_switches=2
        )
        assert valid_request.num_routers == 5

        # Invalid: too few routers
        with pytest.raises(ValueError):
            TopologyRequest(name="test", num_routers=1)

        # Invalid: too many routers
        with pytest.raises(ValueError):
            TopologyRequest(name="test", num_routers=25)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
