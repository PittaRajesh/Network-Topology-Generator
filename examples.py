"""
Example usage of the Networking Automation Engine.

This script demonstrates how to use the engine to generate topologies,
create configurations, and export them in various formats.
"""

import json
from app.generator import TopologyGenerator
from app.core import ConfigurationGenerator
from app.deployment import DeploymentExporter
from app.utils import generate_router_id


def example_basic_topology_generation():
    """Example: Generate a basic network topology."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Topology Generation")
    print("="*60)

    # Create generator with fixed seed for reproducibility
    generator = TopologyGenerator(seed=42)

    # Generate a topology with 4 routers and 2 switches
    topology = generator.generate(
        topology_name="production-lab",
        num_routers=4,
        num_switches=2
    )

    print(f"\nGenerated Topology: {topology.name}")
    print(f"Total Devices: {len(topology.devices)}")
    print(f"  - Routers: {topology.num_routers}")
    print(f"  - Switches: {topology.num_switches}")
    print(f"Total Links: {len(topology.links)}\n")

    # Display device information
    print("Devices:")
    for device in topology.devices:
        print(f"  - {device.name} ({device.device_type.value})")
        if device.router_id:
            print(f"    Router ID: {device.router_id}")

    # Display link information
    print("\nLinks:")
    for i, link in enumerate(topology.links, 1):
        print(f"  {i}. {link.source_device}:{link.source_interface} "
              f"({link.source_ip}) <--> "
              f"{link.destination_device}:{link.destination_interface} "
              f"({link.destination_ip})")

    return topology


def example_configuration_generation(topology):
    """Example: Generate OSPF configurations."""
    print("\n" + "="*60)
    print("EXAMPLE 2: OSPF Configuration Generation")
    print("="*60)

    config_generator = ConfigurationGenerator()
    routing_config = config_generator.generate_ospf_configs(topology)

    print(f"\nGenerated OSPF Configurations for {len(routing_config.ospf_configs)} devices\n")

    # Display configuration for each router
    for ospf_config in routing_config.ospf_configs:
        print(f"Device: {ospf_config.device_name}")
        print(f"  Router ID: {ospf_config.router_id}")
        print(f"  Process ID: {ospf_config.ospf_process_id}")
        print(f"  Interfaces:")
        for iface in ospf_config.interfaces:
            print(f"    - {iface.interface_name}: {iface.ip_address}")
        print(f"  OSPF Networks:")
        for network in ospf_config.networks:
            print(f"    - {network['network']} {network['netmask']} area {network['area']}")
        print()

    return routing_config


def example_containerlab_export(topology):
    """Example: Export to Containerlab format."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Containerlab Export")
    print("="*60)

    exporter = DeploymentExporter()
    containerlab_config = exporter.export_containerlab_topology(
        topology,
        image="frrouting/frr:latest"
    )

    print(f"\nContainerlab Topology: {containerlab_config['name']}\n")
    print("Nodes:")
    for node_name, node_config in containerlab_config['topology']['nodes'].items():
        print(f"  - {node_name}")
        print(f"    Image: {node_config['image']}")

    print(f"\nLinks: {len(containerlab_config['topology']['links'])}")
    for link in containerlab_config['topology']['links']:
        print(f"  - {link['endpoints'][0]} <--> {link['endpoints'][1]}")

    return containerlab_config


def example_yaml_export(topology):
    """Example: Export topology to YAML format."""
    print("\n" + "="*60)
    print("EXAMPLE 4: YAML Export")
    print("="*60)

    exporter = DeploymentExporter()
    yaml_content = exporter.export_to_yaml(topology)

    print("\nGenerated YAML:")
    print("-" * 60)
    # Print first 1000 characters
    print(yaml_content[:1000])
    if len(yaml_content) > 1000:
        print(f"\n... ({len(yaml_content) - 1000} more characters)")
    print("-" * 60)

    return yaml_content


def example_configuration_rendering(routing_config):
    """Example: Render device configurations."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Configuration Rendering")
    print("="*60)

    exporter = DeploymentExporter()
    device_configs = exporter.generate_all_device_configs(routing_config)

    for device_name, config in device_configs.items():
        print(f"\nDevice: {device_name}")
        print("-" * 60)
        # Print first 500 characters of config
        print(config[:500])
        if len(config) > 500:
            print(f"\n... ({len(config) - 500} more characters)")
        print("-" * 60)


def example_multiple_topologies():
    """Example: Generate multiple topologies for testing."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Multiple Test Topologies")
    print("="*60)

    generator = TopologyGenerator()
    topologies = []

    test_configs = [
        ("small-lab", 2, 0),
        ("medium-lab", 5, 2),
        ("large-lab", 10, 5),
    ]

    for topo_name, num_routers, num_switches in test_configs:
        print(f"\nGenerating {topo_name}...")
        topo = generator.generate(topo_name, num_routers, num_switches)
        topologies.append(topo)
        print(f"  ✓ Generated {num_routers} routers + {num_switches} switches, "
              f"{len(topo.links)} links")

    return topologies


def example_reproducible_topology():
    """Example: Generate reproducible topology using seed."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Reproducible Topology Generation")
    print("="*60)

    seed = 12345
    print(f"\nGenerating topology with seed: {seed}")

    # First generation
    gen1 = TopologyGenerator(seed=seed)
    topo1 = gen1.generate("reproducible-test", 5, 2)

    # Second generation with same seed
    gen2 = TopologyGenerator(seed=seed)
    topo2 = gen2.generate("reproducible-test", 5, 2)

    print(f"\nFirst run: {len(topo1.devices)} devices, {len(topo1.links)} links")
    print(f"Second run: {len(topo2.devices)} devices, {len(topo2.links)} links")

    # Verify they're the same
    same_devices = all(
        d1.name == d2.name
        for d1, d2 in zip(topo1.devices, topo2.devices)
    )
    same_links = len(topo1.links) == len(topo2.links)

    if same_devices and same_links:
        print("✓ Topologies are identical (reproducible)")
    else:
        print("✗ Topologies differ")


def main():
    """Run all examples."""
    print("\n" + "🚀 " * 20)
    print("NETWORKING AUTOMATION ENGINE - EXAMPLES")
    print("🚀 " * 20)

    # Run examples
    topology = example_basic_topology_generation()
    routing_config = example_configuration_generation(topology)
    containerlab_config = example_containerlab_export(topology)
    yaml_export = example_yaml_export(topology)
    example_configuration_rendering(routing_config)
    topologies = example_multiple_topologies()
    example_reproducible_topology()

    print("\n" + "="*60)
    print("All examples completed successfully! ✓")
    print("="*60)
    print("\nNext steps:")
    print("1. Run the API server: python3 -m uvicorn app.main:app --reload")
    print("2. Visit API docs: http://localhost:8000/docs")
    print("3. Check the README.md for more examples and API requests")
    print()


if __name__ == "__main__":
    main()
