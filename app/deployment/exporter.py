"""Deployment and export module for creating runnable topologies."""
import yaml
from typing import Dict, List, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
from app.models import Topology, RoutingConfig, OSPFConfiguration


class DeploymentExporter:
    """
    Exports topologies to various formats for deployment.
    
    Features:
    - Containerlab YAML export
    - Configuration rendering with Jinja2
    - Multi-format template support
    """

    def __init__(self, template_dir: str = None):
        """
        Initialize the deployment exporter.
        
        Args:
            template_dir: Path to Jinja2 templates directory
        """
        self.template_dir = template_dir
        if template_dir:
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.env = None

    def export_containerlab_topology(
        self,
        topology: Topology,
        image: str = "frrouting/frr:latest",
        binds: List[str] = None
    ) -> Dict[str, Any]:
        """
        Export topology in Containerlab format.
        
        Args:
            topology: Topology object
            image: Container image to use
            binds: Volume binds for containers
        
        Returns:
            Containerlab topology dictionary
        """
        nodes = {}
        links = []

        # Create nodes for each device
        for device in topology.devices:
            node_config = {
                "image": image,
                "kind": "linux",
            }
            
            if binds:
                node_config["binds"] = binds
            
            nodes[device.name] = node_config

        # Create links
        for link in topology.links:
            link_entry = {
                "endpoints": [
                    f"{link.source_device}:{link.source_interface}",
                    f"{link.destination_device}:{link.destination_interface}"
                ]
            }
            links.append(link_entry)

        # Create topology structure
        containerlab_topology = {
            "name": topology.name,
            "topology": {
                "nodes": nodes,
                "links": links
            }
        }

        return containerlab_topology

    def export_to_yaml(
        self,
        topology: Topology,
        output_path: str = None
    ) -> str:
        """
        Export topology to YAML format.
        
        Args:
            topology: Topology object
            output_path: Optional file path to write YAML
        
        Returns:
            YAML string representation
        """
        # Prepare data for YAML export
        topology_dict = {
            "name": topology.name,
            "metadata": {
                "num_routers": topology.num_routers,
                "num_switches": topology.num_switches,
                "routing_protocol": topology.routing_protocol,
                "generated_at": datetime.utcnow().isoformat(),
            },
            "devices": [
                {
                    "name": device.name,
                    "type": device.device_type.value,
                    "router_id": device.router_id,
                    "asn": device.asn,
                }
                for device in topology.devices
            ],
            "links": [
                {
                    "source": link.source_device,
                    "source_iface": link.source_interface,
                    "target": link.destination_device,
                    "target_iface": link.destination_interface,
                    "source_ip": link.source_ip,
                    "target_ip": link.destination_ip,
                    "cost": link.cost,
                }
                for link in topology.links
            ]
        }

        # Convert to YAML
        yaml_str = yaml.dump(
            topology_dict,
            default_flow_style=False,
            sort_keys=False
        )

        # Optionally write to file
        if output_path:
            with open(output_path, "w") as f:
                f.write(yaml_str)

        return yaml_str

    def render_device_config(
        self,
        routing_config: OSPFConfiguration,
        template_name: str = "ospf_router.j2"
    ) -> str:
        """
        Render device configuration using Jinja2 template.
        
        Args:
            routing_config: OSPF configuration for device
            template_name: Name of template to use
        
        Returns:
            Rendered configuration string
        """
        if not self.env:
            return self._render_default_config(routing_config)

        try:
            template = self.env.get_template(template_name)
        except:
            # Fallback to default rendering
            return self._render_default_config(routing_config)

        # Prepare context
        from app.utils import get_subnet_mask
        
        context = {
            "device_name": routing_config.device_name,
            "router_id": routing_config.router_id,
            "ospf_process_id": routing_config.ospf_process_id,
            "interfaces": routing_config.interfaces,
            "networks": routing_config.networks,
            "subnet_mask": "255.255.255.0",
            "generated_date": datetime.utcnow().isoformat(),
        }

        return template.render(context)

    def _render_default_config(
        self,
        routing_config: OSPFConfiguration
    ) -> str:
        """
        Render a basic configuration without templates.
        
        Args:
            routing_config: OSPF configuration
        
        Returns:
            Configuration string
        """
        config = f"""
! ============================================
! OSPF Router Configuration
! Device: {routing_config.device_name}
! Generated: {datetime.utcnow().isoformat()}
! ============================================

hostname {routing_config.device_name}

"""
        
        # Add interface configurations
        for interface in routing_config.interfaces:
            ip_addr = interface.ip_address.split("/")[0]
            config += f"""
interface {interface.interface_name}
 description {interface.description or 'Interface'}
 ip address {ip_addr} 255.255.255.0
 no shutdown
"""

        # Add OSPF configuration
        config += f"""
router ospf {routing_config.ospf_process_id}
 router-id {routing_config.router_id}
"""
        
        for network in routing_config.networks:
            config += f" network {network['network']} {network['netmask']} area {network['area']}\n"

        return config

    def generate_all_device_configs(
        self,
        routing_config: RoutingConfig,
        template_name: str = "ospf_router.j2"
    ) -> Dict[str, str]:
        """
        Generate configurations for all devices.
        
        Args:
            routing_config: Complete routing configuration
            template_name: Template to use for rendering
        
        Returns:
            Dictionary mapping device name to configuration
        """
        configs = {}

        for ospf_config in routing_config.ospf_configs:
            config = self.render_device_config(ospf_config, template_name)
            configs[ospf_config.device_name] = config

        return configs
