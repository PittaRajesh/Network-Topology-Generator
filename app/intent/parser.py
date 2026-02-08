"""
Intent Parser Module

Converts high-level networking intent into topology constraints that guide generation.
This module bridges the gap between what users want and how the system builds it.
"""

import logging
from typing import Dict, Any
from app.models.intent import (
    IntentRequest, TopologyConstraint, IntentConstraints, 
    RedundancyLevel, TopologyType, DesignGoal
)

logger = logging.getLogger(__name__)


class IntentParser:
    """
    Parses user intent and converts it into topology constraints.
    
    The parser takes high-level intent specifications and translates them into
    measurable constraints that guide topology generation and validation.
    
    Constraints are derived from:
    - Redundancy level (affects minimum connections per device)
    - Topology type (affects structural patterns)
    - Max hops (affects diameter)
    - Design goals (affects optimization trade-offs)
    """
    
    # Mapping of redundancy levels to minimum edge-disjoint paths
    REDUNDANCY_PATH_MAPS = {
        RedundancyLevel.MINIMUM: 1,
        RedundancyLevel.STANDARD: 2,
        RedundancyLevel.HIGH: 3,
        RedundancyLevel.CRITICAL: 4,
    }
    
    # Mapping of redundancy levels to minimum connections per device
    REDUNDANCY_CONNECTION_MAPS = {
        RedundancyLevel.MINIMUM: 1,
        RedundancyLevel.STANDARD: 2,
        RedundancyLevel.HIGH: 3,
        RedundancyLevel.CRITICAL: 4,
    }
    
    def __init__(self):
        """Initialize the intent parser."""
        logger.info("Initializing Intent Parser")
    
    def parse(self, intent: IntentRequest) -> IntentConstraints:
        """
        Parse user intent into constraints.
        
        Args:
            intent: User's high-level intent specification
        
        Returns:
            IntentConstraints: Set of measurable constraints
        
        Raises:
            ValueError: If intent is invalid or unsupported
        """
        logger.info(f"Parsing intent: {intent.intent_name}")
        
        # Validate the intent first
        self._validate_intent(intent)
        
        # Extract constraints from each aspect of intent
        redundancy_constraint = self._parse_redundancy(intent)
        path_diversity_constraint = self._parse_path_diversity(intent)
        hop_count_constraint = self._parse_hop_count(intent)
        spof_constraint = self._parse_spof_requirement(intent)
        topology_constraint = self._parse_topology_type(intent)
        scalability_constraint = self._parse_scalability(intent)
        custom_constraints = self._parse_custom_constraints(intent)
        
        constraints = IntentConstraints(
            redundancy_constraint=redundancy_constraint,
            path_diversity_constraint=path_diversity_constraint,
            hop_count_constraint=hop_count_constraint,
            spof_constraint=spof_constraint,
            topology_pattern_constraint=topology_constraint,
            scalability_constraint=scalability_constraint,
            custom_constraints=custom_constraints,
        )
        
        logger.info(f"Successfully parsed intent into {len(constraints.get_all_constraints())} constraints")
        return constraints
    
    def _validate_intent(self, intent: IntentRequest) -> None:
        """
        Validate that intent is logically consistent.
        
        Args:
            intent: Intent to validate
        
        Raises:
            ValueError: If intent has contradictions
        """
        # Check that min connections per site doesn't exceed network size
        if intent.minimum_connections_per_site >= intent.number_of_sites:
            raise ValueError(
                f"Minimum connections per site ({intent.minimum_connections_per_site}) "
                f"cannot be >= number of sites ({intent.number_of_sites})"
            )
        
        # Check max links is reasonable if specified
        if intent.max_links is not None:
            # In a full mesh of N devices, max edges = N*(N-1)/2
            max_possible = intent.number_of_sites * (intent.number_of_sites - 1) / 2
            min_required = (intent.number_of_sites * intent.minimum_connections_per_site) / 2
            
            if intent.max_links < min_required:
                raise ValueError(
                    f"Max links ({intent.max_links}) is less than minimum required "
                    f"({min_required}) for desired redundancy"
                )
        
        # Hub-spoke with high redundancy is contradictory
        if (intent.topology_type == TopologyType.HUB_SPOKE and 
            intent.redundancy_level in [RedundancyLevel.HIGH, RedundancyLevel.CRITICAL]):
            logger.warning(
                "Hub-speak topology with high/critical redundancy is contradictory. "
                "Hub-spoke inherently has SPOF at the hub. Consider FULL_MESH instead."
            )
        
        logger.info("Intent validation passed")
    
    def _parse_redundancy(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse redundancy level into constraint.
        
        Maps redundancy levels to minimum connection requirements.
        """
        min_paths = self.REDUNDANCY_PATH_MAPS[intent.redundancy_level]
        min_connections = self.REDUNDANCY_CONNECTION_MAPS[intent.redundancy_level]
        
        return TopologyConstraint(
            constraint_name="redundancy_requirement",
            constraint_type="redundancy",
            min_value=min_paths,
            max_value=None,
            required=True,
            description=f"Redundancy level {intent.redundancy_level}: minimum {min_paths} edge-disjoint paths",
            severity="high"
        )
    
    def _parse_path_diversity(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse design goal into path diversity constraint.
        
        Redundancy focused means maximizing diverse paths.
        """
        # Redundancy focused implies maximal path diversity
        if intent.design_goal == DesignGoal.REDUNDANCY_FOCUSED:
            min_diverse_paths = self.REDUNDANCY_PATH_MAPS[intent.redundancy_level]
        else:
            min_diverse_paths = 1
        
        return TopologyConstraint(
            constraint_name="path_diversity_requirement",
            constraint_type="path_diversity",
            min_value=min_diverse_paths,
            max_value=None,
            required=True,
            description=f"Minimum path diversity: {min_diverse_paths} edge-disjoint paths between major paths",
            severity="high"
        )
    
    def _parse_hop_count(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse max hops into constraint.
        
        This directly constrains the network diameter.
        """
        return TopologyConstraint(
            constraint_name="hop_count_limit",
            constraint_type="hop_count",
            min_value=None,
            max_value=intent.max_hops,
            required=True,
            description=f"Maximum hops between any two devices: {intent.max_hops}",
            severity="high"
        )
    
    def _parse_spof_requirement(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse SPOF elimination requirement.
        """
        return TopologyConstraint(
            constraint_name="spof_elimination",
            constraint_type="spof",
            min_value=0,  # 0 SPOFs allowed if enabled
            max_value=0,
            required=intent.minimize_spof,
            description="Eliminate single points of failure (critical devices)" if intent.minimize_spof 
                       else "SPOFs allowed",
            severity="critical" if intent.minimize_spof else "low"
        )
    
    def _parse_topology_type(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse topology type into structural constraint.
        """
        topology_descriptions = {
            TopologyType.FULL_MESH: "All devices must connect to all other devices",
            TopologyType.HUB_SPOKE: "Central hub with radial spokes",
            TopologyType.RING: "Ring topology - devices in circular arrangement",
            TopologyType.TREE: "Hierarchical tree with core, aggregation, edge layers",
            TopologyType.LEAF_SPINE: "Data center topology - leaves connect to all spines",
            TopologyType.HYBRID: "Mix of topology patterns"
        }
        
        return TopologyConstraint(
            constraint_name="topology_pattern",
            constraint_type="topology_pattern",
            required=True,
            description=topology_descriptions.get(intent.topology_type, "Custom topology"),
            severity="high"
        )
    
    def _parse_scalability(self, intent: IntentRequest) -> TopologyConstraint:
        """
        Parse scalability goal into growth constraint.
        """
        if intent.design_goal == DesignGoal.SCALABILITY:
            return TopologyConstraint(
                constraint_name="scalability_requirement",
                constraint_type="scalability",
                min_value=intent.number_of_sites,
                required=True,
                description=f"Topology must support at least {intent.number_of_sites} devices with growth headroom",
                severity="medium"
            )
        else:
            return TopologyConstraint(
                constraint_name="scalability_requirement",
                constraint_type="scalability",
                min_value=intent.number_of_sites,
                required=False,
                description="No specific scalability requirement",
                severity="low"
            )
    
    def _parse_custom_constraints(self, intent: IntentRequest) -> list:
        """
        Parse any custom constraints provided.
        """
        custom = []
        
        if intent.custom_constraints:
            for name, value in intent.custom_constraints.items():
                constraint = TopologyConstraint(
                    constraint_name=name,
                    constraint_type="custom",
                    min_value=value.get("min_value") if isinstance(value, dict) else None,
                    max_value=value.get("max_value") if isinstance(value, dict) else None,
                    required=value.get("required", True) if isinstance(value, dict) else True,
                    description=value.get("description", str(value)) if isinstance(value, dict) else str(value),
                    severity=value.get("severity", "medium") if isinstance(value, dict) else "medium"
                )
                custom.append(constraint)
        
        return custom
    
    def constraints_to_dict(self, constraints: IntentConstraints) -> Dict[str, Any]:
        """
        Convert constraints to dictionary for documentation.
        
        Useful for logging and reporting what constraints will govern generation.
        """
        return {
            "redundancy": {
                "type": constraints.redundancy_constraint.constraint_type,
                "min_value": constraints.redundancy_constraint.min_value,
                "description": constraints.redundancy_constraint.description,
            },
            "path_diversity": {
                "type": constraints.path_diversity_constraint.constraint_type,
                "min_value": constraints.path_diversity_constraint.min_value,
                "description": constraints.path_diversity_constraint.description,
            },
            "hop_count": {
                "max_value": constraints.hop_count_constraint.max_value,
                "description": constraints.hop_count_constraint.description,
            },
            "spof": {
                "required": constraints.spof_constraint.required,
                "description": constraints.spof_constraint.description,
            },
            "topology_pattern": {
                "description": constraints.topology_pattern_constraint.description,
            },
        }
