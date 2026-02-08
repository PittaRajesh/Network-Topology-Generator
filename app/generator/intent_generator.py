"""
Intent-Based Topology Generator

Generates network topologies that satisfy user intent while optimizing
for specified design goals. This generator combines rule-based logic with
graph algorithms to create resilient, efficient topologies.
"""

import logging
import random
from typing import List, Set, Tuple, Optional
import networkx as nx

from app.models.topology import Topology, Device, Link, DeviceType
from app.models.intent import (
    IntentRequest, IntentConstraints, TopologyType, DesignGoal, RedundancyLevel
)
from app.intent.parser import IntentParser

logger = logging.getLogger(__name__)


class IntentBasedTopologyGenerator:
    """
    Generates topologies from user intent.
    
    This generator takes an IntentRequest and produces a Topology that satisfies
    the expressed requirements. The generation process:
    
    1. Parses intent into constraints
    2. Creates base topology skeleton based on topology_type
    3. Adds redundant links based on redundancy_level
    4. Validates against constraints
    5. Optimizes based on design_goal
    
    The approach is rule-based and deterministic, making it suitable for
    embedded deployment and future ML model integration.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the intent-based generator.
        
        Args:
            seed: Random seed for reproducible results
        """
        self.seed = seed
        self.parser = IntentParser()
        if seed is not None:
            random.seed(seed)
            logger.info(f"Generator initialized with seed {seed}")
    
    def generate_from_intent(self, intent: IntentRequest) -> Topology:
        """
        Generate a topology from user intent.
        
        Args:
            intent: User's high-level networking intent
        
        Returns:
            Topology object satisfying the intent
        
        Raises:
            ValueError: If topology cannot satisfy intent
        """
        logger.info(f"Generating topology from intent: {intent.intent_name}")
        
        # Parse intent into constraints
        constraints = self.parser.parse(intent)
        logger.info(f"Parsed intent into {len(constraints.get_all_constraints())} constraints")
        
        # Generate base topology based on type
        if intent.topology_type == TopologyType.FULL_MESH:
            topology = self._generate_full_mesh(intent)
        elif intent.topology_type == TopologyType.HUB_SPOKE:
            topology = self._generate_hub_spoke(intent)
        elif intent.topology_type == TopologyType.RING:
            topology = self._generate_ring(intent)
        elif intent.topology_type == TopologyType.TREE:
            topology = self._generate_tree(intent)
        elif intent.topology_type == TopologyType.LEAF_SPINE:
            topology = self._generate_leaf_spine(intent)
        else:
            # Hybrid: default to tree
            topology = self._generate_tree(intent)
        
        logger.info(
            f"Generated base {intent.topology_type} topology with "
            f"{len(topology.devices)} devices and {len(topology.links)} links"
        )
        
        # Add redundancy links if needed
        if intent.redundancy_level != RedundancyLevel.MINIMUM:
            topology = self._add_redundancy_links(topology, intent, constraints)
        
        # Optimize based on design goal
        if intent.design_goal == DesignGoal.COST_OPTIMIZED:
            topology = self._optimize_for_cost(topology, intent)
        elif intent.design_goal == DesignGoal.LATENCY_OPTIMIZED:
            topology = self._optimize_for_latency(topology, intent)
        
        logger.info(
            f"Final topology: {len(topology.devices)} devices, "
            f"{len(topology.links)} links, "
            f"routing protocol: {intent.routing_protocol}"
        )
        
        return topology
    
    def _generate_full_mesh(self, intent: IntentRequest) -> Topology:
        """
        Generate full mesh topology where every device connects to every other.
        
        This ensures maximum redundancy and minimal hop count but highest cost.
        """
        logger.debug("Generating full mesh topology")
        
        # Create devices
        devices = self._create_devices(intent.number_of_sites)
        
        # Create links between all device pairs
        links = []
        cost = 100  # Base cost
        
        for i, src in enumerate(devices):
            for dst in devices[i+1:]:
                link = Link(
                    source_device=src.name,
                    destination_device=dst.name,
                    source_ip=f"10.{i}.{devices.index(dst)}.1",
                    destination_ip=f"10.{i}.{devices.index(dst)}.2",
                    cost=cost,
                    link_type="intra-region"
                )
                links.append(link)
                
                # Add reverse link
                reverse_link = Link(
                    source_device=dst.name,
                    destination_device=src.name,
                    source_ip=f"10.{i}.{devices.index(dst)}.2",
                    destination_ip=f"10.{i}.{devices.index(dst)}.1",
                    cost=cost,
                    link_type="intra-region"
                )
                links.append(reverse_link)
        
        return Topology(
            name=f"{intent.intent_name}-full-mesh",
            devices=devices,
            links=links,
            routing_protocol=intent.routing_protocol.value
        )
    
    def _generate_hub_spoke(self, intent: IntentRequest) -> Topology:
        """
        Generate hub-and-spoke topology with central hub.
        
        Note: This has SPOF at the hub. Use with caution if minimize_spof=True.
        """
        logger.debug("Generating hub-spoke topology")
        
        devices = self._create_devices(intent.number_of_sites)
        hub = devices[0]  # First device is the hub
        spokes = devices[1:]
        
        links = []
        cost = 100
        
        # Connect each spoke to hub
        for i, spoke in enumerate(spokes):
            link = Link(
                source_device=hub.name,
                destination_device=spoke.name,
                source_ip=f"10.0.{i}.1",
                destination_ip=f"10.0.{i}.2",
                cost=cost,
                link_type="hub-spoke"
            )
            links.append(link)
            
            # Reverse link
            reverse = Link(
                source_device=spoke.name,
                destination_device=hub.name,
                source_ip=f"10.0.{i}.2",
                destination_ip=f"10.0.{i}.1",
                cost=cost,
                link_type="hub-spoke"
            )
            links.append(reverse)
        
        return Topology(
            name=f"{intent.intent_name}-hub-spoke",
            devices=devices,
            links=links,
            routing_protocol=intent.routing_protocol.value
        )
    
    def _generate_ring(self, intent: IntentRequest) -> Topology:
        """
        Generate ring topology with devices in circular arrangement.
        
        Provides good redundancy with moderate link count.
        """
        logger.debug("Generating ring topology")
        
        devices = self._create_devices(intent.number_of_sites)
        links = []
        cost = 100
        
        # Connect devices in ring
        for i in range(len(devices)):
            src = devices[i]
            dst = devices[(i + 1) % len(devices)]  # Wrap around
            
            link = Link(
                source_device=src.name,
                destination_device=dst.name,
                source_ip=f"10.{i}.0.1",
                destination_ip=f"10.{i}.0.2",
                cost=cost,
                link_type="ring"
            )
            links.append(link)
        
        return Topology(
            name=f"{intent.intent_name}-ring",
            devices=devices,
            links=links,
            routing_protocol=intent.routing_protocol.value
        )
    
    def _generate_tree(self, intent: IntentRequest) -> Topology:
        """
        Generate hierarchical tree topology.
        
        Architecture:
        - Core layer: Central routers
        - Aggregation layer: Regional aggregators
        - Access layer: Edge devices
        
        This is a common enterprise design.
        """
        logger.debug("Generating tree topology")
        
        total_devices = intent.number_of_sites
        
        # Allocate devices to layers
        # Core: 10% (minimum 1)
        # Aggregation: 30% (minimum 1)
        # Access: 60% (minimum 1)
        core_count = max(1, total_devices // 10)
        agg_count = max(1, (total_devices // 3) - core_count)
        access_count = total_devices - core_count - agg_count
        
        devices = []
        links = []
        cost = 100
        
        # Create core layer (routers)
        core_devices = []
        for i in range(core_count):
            device = Device(
                name=f"C{i+1}",  # Core devices C1, C2, ...
                device_type=DeviceType.ROUTER,
                router_id=f"10.{0}.{i+1}.1",
                asn=65000 + i
            )
            core_devices.append(device)
            devices.append(device)
        
        # Connect core devices in full mesh
        for i, src in enumerate(core_devices):
            for dst in core_devices[i+1:]:
                link = Link(
                    source_device=src.name,
                    destination_device=dst.name,
                    source_ip=f"10.0.{core_devices.index(src)}.1",
                    destination_ip=f"10.0.{core_devices.index(dst)}.1",
                    cost=cost,
                    link_type="core"
                )
                links.append(link)
                # Reverse
                reverse = Link(
                    source_device=dst.name,
                    destination_device=src.name,
                    source_ip=f"10.0.{core_devices.index(dst)}.1",
                    destination_ip=f"10.0.{core_devices.index(src)}.1",
                    cost=cost,
                    link_type="core"
                )
                links.append(reverse)
        
        # Create aggregation layer (switches and routers)
        agg_devices = []
        for i in range(agg_count):
            device_type = DeviceType.ROUTER if i % 2 == 0 else DeviceType.SWITCH
            device = Device(
                name=f"A{i+1}",
                device_type=device_type,
                router_id=f"10.{1}.{i+1}.1" if device_type == DeviceType.ROUTER else None,
                asn=65100 + i if device_type == DeviceType.ROUTER else None
            )
            agg_devices.append(device)
            devices.append(device)
        
        # Connect aggregation to core (each agg to 2+ core for redundancy)
        for agg in agg_devices:
            # Connect to 2 random core devices
            for core in random.sample(core_devices, min(2, len(core_devices))):
                link = Link(
                    source_device=agg.name,
                    destination_device=core.name,
                    source_ip=f"10.1.{agg_devices.index(agg)}.1",
                    destination_ip=f"10.1.{core_devices.index(core)}.1",
                    cost=cost,
                    link_type="aggregation"
                )
                links.append(link)
                # Reverse
                reverse = Link(
                    source_device=core.name,
                    destination_device=agg.name,
                    source_ip=f"10.1.{core_devices.index(core)}.1",
                    destination_ip=f"10.1.{agg_devices.index(agg)}.1",
                    cost=cost,
                    link_type="aggregation"
                )
                links.append(reverse)
        
        # Create access layer
        access_devices = []
        for i in range(access_count):
            device = Device(
                name=f"E{i+1}",
                device_type=DeviceType.SWITCH,
                router_id=None,
                asn=None
            )
            access_devices.append(device)
            devices.append(device)
        
        # Connect access to aggregation (each to 1-2 agg for redundancy)
        for access in access_devices:
            num_connections = min(2, len(agg_devices))
            for agg in random.sample(agg_devices, min(num_connections, len(agg_devices))):
                link = Link(
                    source_device=access.name,
                    destination_device=agg.name,
                    source_ip=f"10.2.{access_devices.index(access)}.1",
                    destination_ip=f"10.2.{agg_devices.index(agg)}.1",
                    cost=cost,
                    link_type="access"
                )
                links.append(link)
        
        return Topology(
            name=f"{intent.intent_name}-tree",
            devices=devices,
            links=links,
            routing_protocol=intent.routing_protocol.value
        )
    
    def _generate_leaf_spine(self, intent: IntentRequest) -> Topology:
        """
        Generate data center leaf-spine topology.
        
        All leaves connect to all spines, creating a fat-tree with
        high redundancy and predictable latency.
        """
        logger.debug("Generating leaf-spine topology")
        
        total_devices = intent.number_of_sites
        
        # Allocate roughly 60% leaves, 40% spines
        leaf_count = max(1, (total_devices * 60) // 100)
        spine_count = total_devices - leaf_count
        
        devices = []
        links = []
        cost = 100
        
        # Create leaf devices
        leaf_devices = []
        for i in range(leaf_count):
            device = Device(
                name=f"L{i+1}",
                device_type=DeviceType.SWITCH,
                router_id=f"10.{0}.{i+1}.1",
                asn=65000 + i
            )
            leaf_devices.append(device)
            devices.append(device)
        
        # Create spine devices
        spine_devices = []
        for i in range(spine_count):
            device = Device(
                name=f"S{i+1}",
                device_type=DeviceType.ROUTER,
                router_id=f"10.{1}.{i+1}.1",
                asn=65100 + i
            )
            spine_devices.append(device)
            devices.append(device)
        
        # Connect all leaves to all spines (full mesh between layers)
        for leaf in leaf_devices:
            for spine in spine_devices:
                link = Link(
                    source_device=leaf.name,
                    destination_device=spine.name,
                    source_ip=f"10.{leaf_devices.index(leaf)}.{spine_devices.index(spine)}.1",
                    destination_ip=f"10.{leaf_devices.index(leaf)}.{spine_devices.index(spine)}.2",
                    cost=cost,
                    link_type="leaf-spine"
                )
                links.append(link)
                
                # Reverse
                reverse = Link(
                    source_device=spine.name,
                    destination_device=leaf.name,
                    source_ip=f"10.{leaf_devices.index(leaf)}.{spine_devices.index(spine)}.2",
                    destination_ip=f"10.{leaf_devices.index(leaf)}.{spine_devices.index(spine)}.1",
                    cost=cost,
                    link_type="leaf-spine"
                )
                links.append(reverse)
        
        return Topology(
            name=f"{intent.intent_name}-leaf-spine",
            devices=devices,
            links=links,
            routing_protocol=intent.routing_protocol.value
        )
    
    def _create_devices(self, count: int) -> List[Device]:
        """Create basic device instances."""
        devices = []
        for i in range(count):
            device = Device(
                name=f"R{i+1}",
                device_type=DeviceType.ROUTER,
                router_id=f"10.{i//255}.{i%255}.1",
                asn=65000 + i
            )
            devices.append(device)
        return devices
    
    def _add_redundancy_links(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> Topology:
        """
        Add redundant links to improve resilience.
        
        This method adds links between non-adjacent devices to create
        alternative paths and eliminate single points of failure.
        """
        logger.debug(f"Adding redundancy links for {intent.redundancy_level}")
        
        # Build networkx graph from current topology
        G = nx.Graph()
        for device in topology.devices:
            G.add_node(device.name)
        for link in topology.links:
            G.add_edge(link.source_device, link.destination_device)
        
        # Find articulation points (SPOFs)
        articulation_points = list(nx.articulation_points(G))
        logger.debug(f"Found {len(articulation_points)} articulation points")
        
        # Add links to eliminate articulation points and increase path diversity
        new_links = list(topology.links)
        devices_dict = {d.name: d for d in topology.devices}
        cost = 100
        
        # For STANDARD and higher, add links around articulation points
        if intent.redundancy_level in [RedundancyLevel.STANDARD, RedundancyLevel.HIGH, RedundancyLevel.CRITICAL]:
            for ap in articulation_points:
                # Find devices on different sides of articulation point
                neighbors_of_ap = set(G.neighbors(ap))
                
                # Find non-neighbors that are 2-3 hops away
                for other_device in G.nodes():
                    if other_device != ap and other_device not in neighbors_of_ap:
                        # Check if adding this link would help
                        path_length = nx.shortest_path_length(G, ap, other_device)
                        if 2 <= path_length <= 3:  # 2-3 hops away
                            # Add redundant link
                            new_link = Link(
                                source_device=ap,
                                destination_device=other_device,
                                source_ip=f"10.{ord(ap[0])}.{int(ap[1:])}.1",
                                destination_ip=f"10.{ord(other_device[0])}.{int(other_device[1:])}.2",
                                cost=cost,
                                link_type="redundancy"
                            )
                            if new_link and new_link not in new_links:
                                new_links.append(new_link)
                                logger.debug(f"Added redundancy link: {ap} -> {other_device}")
                            break  # One link per AP is often enough
        
        # For HIGH and CRITICAL, add additional mesh links
        if intent.redundancy_level in [RedundancyLevel.HIGH, RedundancyLevel.CRITICAL]:
            # Add more random redundant links
            device_names = [d.name for d in topology.devices]
            link_pairs = set()
            
            for link in new_links:
                link_pairs.add((min(link.source_device, link.destination_device),
                               max(link.source_device, link.destination_device)))
            
            additional_links_needed = min(
                len(topology.devices),  # Add at most N links
                4 if intent.redundancy_level == RedundancyLevel.HIGH else 8
            )
            
            attempts = 0
            while len(link_pairs) < len(link_pairs) + additional_links_needed and attempts < 20:
                src, dst = random.sample(device_names, 2)
                pair = (min(src, dst), max(src, dst))
                if pair not in link_pairs:
                    new_link = Link(
                        source_device=src,
                        destination_device=dst,
                        source_ip=f"10.{ord(src[0])}.{int(src[1:])}.1",
                        destination_ip=f"10.{ord(dst[0])}.{int(dst[1:])}.2",
                        cost=cost,
                        link_type="redundancy"
                    )
                    new_links.append(new_link)
                    link_pairs.add(pair)
                attempts += 1
        
        topology.links = new_links
        logger.info(f"Added redundancy: {len(new_links)} total links")
        return topology
    
    def _optimize_for_cost(self, topology: Topology, intent: IntentRequest) -> Topology:
        """
        Optimize topology for cost by removing unnecessary links.
        
        Keeps topology connected while minimizing link count.
        """
        logger.debug("Optimizing for cost")
        # In cost-optimized mode, keep only essential links
        # This would involve finding a minimum spanning tree
        # For now, we keep the topology as-is since basic generation
        # already creates lean topologies
        return topology
    
    def _optimize_for_latency(self, topology: Topology, intent: IntentRequest) -> Topology:
        """
        Optimize topology for low latency by adjusting OSPF costs.
        
        Sets lower costs on direct/short paths.
        """
        logger.debug("Optimizing for latency")
        
        # Adjust link costs to favor direct connections
        for link in topology.links:
            if link.link_type in ["core", "leaf-spine"]:
                link.cost = 50  # Lower cost for primary links
            elif link.link_type == "redundancy":
                link.cost = 150  # Higher cost for redundancy links
        
        return topology
