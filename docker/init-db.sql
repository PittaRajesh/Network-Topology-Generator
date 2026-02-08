-- Initialize PostgreSQL database for Networking Automation Engine

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create topologies table
CREATE TABLE IF NOT EXISTS topologies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    num_routers INTEGER NOT NULL,
    num_switches INTEGER NOT NULL,
    routing_protocol VARCHAR(50) NOT NULL DEFAULT 'ospf',
    topology_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    metadata JSONB
);

-- Create configurations table
CREATE TABLE IF NOT EXISTS configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topology_id UUID NOT NULL REFERENCES topologies(id) ON DELETE CASCADE,
    device_name VARCHAR(100) NOT NULL,
    configuration_text TEXT NOT NULL,
    configuration_type VARCHAR(50) NOT NULL DEFAULT 'ospf',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create exports table
CREATE TABLE IF NOT EXISTS exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topology_id UUID NOT NULL REFERENCES topologies(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    export_data JSONB NOT NULL,
    file_path VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_by VARCHAR(255)
);

-- Create audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    user_ip VARCHAR(45),
    status VARCHAR(20) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_topologies_name ON topologies(name);
CREATE INDEX idx_topologies_created_at ON topologies(created_at);
CREATE INDEX idx_topologies_routing_protocol ON topologies(routing_protocol);
CREATE INDEX idx_configurations_topology_id ON configurations(topology_id);
CREATE INDEX idx_configurations_device_name ON configurations(device_name);
CREATE INDEX idx_exports_topology_id ON exports(topology_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);

-- Create full text search index
CREATE INDEX idx_topologies_search ON topologies USING GIN(
    to_tsvector('english', name || ' ' || COALESCE(routing_protocol, ''))
);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_topologies_updated_at BEFORE UPDATE
    ON topologies FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE
    ON configurations FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create views
CREATE OR REPLACE VIEW topology_summary AS
SELECT
    t.id,
    t.name,
    t.num_routers,
    t.num_switches,
    t.routing_protocol,
    COUNT(c.id) AS config_count,
    COUNT(e.id) AS export_count,
    t.created_at,
    t.updated_at
FROM topologies t
LEFT JOIN configurations c ON t.id = c.topology_id
LEFT JOIN exports e ON t.id = e.topology_id
GROUP BY t.id;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO automation;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO automation;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO automation;
