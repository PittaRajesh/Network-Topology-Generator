"""Topology generator module for creating network topologies."""
import random
from typing import Set, Tuple, List
from app.models import Device, Link, Topology, DeviceType
from app.utils import generate_ip_subnet, allocate_ips_for_link, generate_router_id


class TopologyGenerator:
    """
    Generates valid network topologies with routers and switches.
    
    Features:
    - Random but valid topology generation
    - Ensures connectivity between devices
    - Proper IP address allocation
    """

    def __init__(self, seed: int = None):
        """
        Initialize the topology generator.
        
        Args:
            seed: Random seed for reproducible generation. If None, uses current time.
        """
        if seed is not None:
            random.seed(seed)
        
        self.ip_subnet_index = 0
        self.interface_counter = {}

    def generate(
        self,
        topology_name: str,
        num_routers: int,
        num_switches: int
    ) -> Topology:
        """
        Generate a complete network topology.
        
        Args:
            topology_name: Name for the topology
            num_routers: Number of routers (2-20)
            num_switches: Number of switches (0-10)
        
        Returns:
            Topology object with devices and links
        """
        if num_routers < 2:
            raise ValueError("Topology must have at least 2 routers")
        if num_routers > 20:
            raise ValueError("Topology cannot have more than 20 routers")
        if num_switches < 0 or num_switches > 10:
            raise ValueError("Switches must be between 0 and 10")

        # Reset counters
        self.ip_subnet_index = 0
        self.interface_counter = {}

        # Create devices
        devices = []
        devices.extend(self._create_routers(num_routers))
        devices.extend(self._create_switches(num_switches))

        # Create links with valid topology
        links = self._create_links(devices, num_routers, num_switches)

        return Topology(
            name=topology_name,
            num_routers=num_routers,
            num_switches=num_switches,
            devices=devices,
            links=links,
            routing_protocol="ospf"
        )

    def _create_routers(self, count: int) -> List[Device]:
        """
        Create router devices.
        
        Args:
            count: Number of routers to create
        
        Returns:
            List of Device objects
        """
        routers = []
        for i in range(count):
            router_name = f"R{i + 1}"
            router_id = generate_router_id(i)
            
            router = Device(
                name=router_name,
                device_type=DeviceType.ROUTER,
                router_id=router_id,
                asn=65000 + i  # Unique ASN for each router
            )
            routers.append(router)
        
        return routers

    def _create_switches(self, count: int) -> List[Device]:
        """
        Create switch devices.
        
        Args:
            count: Number of switches to create
        
        Returns:
            List of Device objects
        """
        switches = []
        for i in range(count):
            switch_name = f"SW{i + 1}"
            switch = Device(
                name=switch_name,
                device_type=DeviceType.SWITCH
            )
            switches.append(switch)
        
        return switches

    def _create_links(
        self,
        devices: List[Device],
        num_routers: int,
        num_switches: int
    ) -> List[Link]:
        """
        Create links between devices ensuring valid topology.
        
        Strategy:
        - Create a backbone between routers (linear or partial mesh)
        - Connect switches to routers
        - Add some random links for redundancy
        
        Args:
            devices: List of all devices
            num_routers: Number of routers
            num_switches: Number of switches
        
        Returns:
            List of Link objects
        """
        links = []
        connected_pairs: Set[Tuple[str, str]] = set()

        # Extract routers and switches
        routers = [d for d in devices if d.device_type == DeviceType.ROUTER]
        switches = [d for d in devices if d.device_type == DeviceType.SWITCH]

        # Phase 1: Create backbone links between routers (linear chain + some extra)
        for i in range(num_routers - 1):
            source = routers[i]
            destination = routers[i + 1]
            link = self._create_link(source, destination)
            if link:
                links.append(link)
                connected_pairs.add((source.name, destination.name))

        # Phase 2: Add additional router-to-router links for redundancy
        # Create partial mesh with some random links
        num_extra_links = min(num_routers - 1, random.randint(1, max(1, num_routers // 2)))
        attempts = 0
        max_attempts = 50

        while len([l for l in links if l.source_device != l.destination_device and 
                   l.source_device in [r.name for r in routers] and
                   l.destination_device in [r.name for r in routers]]) - (num_routers - 1) < num_extra_links:
            if attempts > max_attempts:
                break
            
            source = random.choice(routers)
            destination = random.choice(routers)
            
            if source.name != destination.name:
                pair = tuple(sorted([source.name, destination.name]))
                if pair not in connected_pairs:
                    link = self._create_link(source, destination)
                    if link:
                        links.append(link)
                        connected_pairs.add(pair)
            
            attempts += 1

        # Phase 3: Connect switches to routers
        for switch in switches:
            # Connect each switch to one or two routers
            num_connections = random.randint(1, min(2, num_routers))
            selected_routers = random.sample(routers, num_connections)
            
            for router in selected_routers:
                link = self._create_link(router, switch)
                if link:
                    links.append(link)

        return links

    def _create_link(self, source_device: Device, dest_device: Device) -> Link:
        """
        Create a link between two devices.
        
        Args:
            source_device: Source device
            dest_device: Destination device
        
        Returns:
            Link object
        """
        # Generate unique subnet for this link
        source_ip, dest_ip = allocate_ips_for_link(f"10.{100 + self.ip_subnet_index}.1.0/24")
        self.ip_subnet_index += 1

        # Get interface names
        source_iface = self._get_next_interface(source_device.name)
        dest_iface = self._get_next_interface(dest_device.name)

        # Determine OSPF cost (lower for router-to-router, higher for switch connections)
        cost = 1 if source_device.device_type == DeviceType.ROUTER and \
                    dest_device.device_type == DeviceType.ROUTER else 100

        link = Link(
            source_device=source_device.name,
            source_interface=source_iface,
            destination_device=dest_device.name,
            destination_interface=dest_iface,
            source_ip=source_ip,
            destination_ip=dest_ip,
            subnet_mask="255.255.255.0",
            cost=cost
        )

        return link

    def _get_next_interface(self, device_name: str) -> str:
        """
        Get the next available interface name for a device.
        
        Args:
            device_name: Name of the device
        
        Returns:
            Interface name (e.g., eth0, eth1)
        """
        if device_name not in self.interface_counter:
            self.interface_counter[device_name] = 0
        
        interface = f"eth{self.interface_counter[device_name]}"
        self.interface_counter[device_name] += 1
        
        return interface
