"""Database layer - Models, repositories, and session management."""

from app.database.models import (
    Base,
    TopologyRecord,
    ValidationRecord,
    SimulationRecord,
    PerformanceMetrics,
    RecommendationHistory,
    OptimizationLog
)

from app.database.repository import (
    TopologyRepository,
    ValidationRepository,
    SimulationRepository,
    PerformanceMetricsRepository,
    RecommendationRepository,
    OptimizationRepository,
    DatabaseRepository
)

from app.database.db import Database, DatabaseConfig, get_db

__all__ = [
    # Models
    "Base",
    "TopologyRecord",
    "ValidationRecord",
    "SimulationRecord",
    "PerformanceMetrics",
    "RecommendationHistory",
    "OptimizationLog",
    # Repositories
    "TopologyRepository",
    "ValidationRepository",
    "SimulationRepository",
    "PerformanceMetricsRepository",
    "RecommendationRepository",
    "OptimizationRepository",
    "DatabaseRepository",
    # Database
    "Database",
    "DatabaseConfig",
    "get_db"
]
