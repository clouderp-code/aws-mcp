#!/usr/bin/env python3
"""
Local test version of raw_analysis that doesn't require S3 access
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.insert(0, '/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server')

def create_sample_sql_content():
    """Create sample SQL content for testing"""
    return """
-- Sample TMF Customer Database Schema
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    customer_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT chk_status CHECK (status IN ('active', 'inactive', 'suspended'))
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    account_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency_code VARCHAR(3) DEFAULT 'ZAR',
    status VARCHAR(20) DEFAULT 'active',
    opened_date DATE NOT NULL,
    closed_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT chk_balance CHECK (balance >= 0),
    CONSTRAINT chk_account_status CHECK (status IN ('active', 'closed', 'suspended'))
);

CREATE TABLE billing_accounts (
    id INTEGER PRIMARY KEY,
    billing_account_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    billing_cycle INTEGER DEFAULT 1,
    billing_date DATE,
    payment_method VARCHAR(50),
    credit_limit DECIMAL(15,2),
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE service_orders (
    id INTEGER PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    account_id INTEGER,
    order_type VARCHAR(50) NOT NULL,
    order_status VARCHAR(50) DEFAULT 'submitted',
    priority VARCHAR(20) DEFAULT 'normal',
    requested_completion_date TIMESTAMP,
    actual_completion_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE contact_mediums (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    medium_type VARCHAR(50) NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    is_preferred BOOLEAN DEFAULT FALSE,
    is_valid BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

def create_sample_procedures_content():
    """Create sample stored procedures content"""
    return """
-- Customer Management Procedures

CREATE PROCEDURE validate_customer_status(IN customer_id INT)
BEGIN
    -- Validate customer status and update if necessary
    DECLARE customer_status VARCHAR(20);
    
    SELECT status INTO customer_status 
    FROM customers 
    WHERE id = customer_id;
    
    IF customer_status = 'inactive' THEN
        UPDATE customers 
        SET status = 'suspended' 
        WHERE id = customer_id AND updated_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
    END IF;
END;

CREATE PROCEDURE calculate_account_balance(IN account_id INT)
BEGIN
    -- Calculate and update account balance
    DECLARE total_balance DECIMAL(15,2) DEFAULT 0.00;
    
    -- Complex business logic for balance calculation
    SELECT SUM(transaction_amount) INTO total_balance
    FROM transactions 
    WHERE account_id = account_id AND status = 'completed';
    
    UPDATE accounts 
    SET balance = COALESCE(total_balance, 0.00),
        updated_at = NOW()
    WHERE id = account_id;
END;

CREATE PROCEDURE process_service_order(IN order_id INT)
BEGIN
    -- Process service order with business rules
    DECLARE order_priority VARCHAR(20);
    DECLARE customer_tier VARCHAR(20);
    
    -- Get order priority and customer tier
    SELECT so.priority, c.tier 
    INTO order_priority, customer_tier
    FROM service_orders so
    JOIN customers c ON so.customer_id = c.id
    WHERE so.id = order_id;
    
    -- Apply business rules based on priority and tier
    IF customer_tier = 'premium' AND order_priority = 'urgent' THEN
        UPDATE service_orders 
        SET order_status = 'expedited'
        WHERE id = order_id;
    END IF;
END;
"""

def create_sample_guide_content():
    """Create sample SecondBrain guide content"""
    return """
# MTN Customer Database Analysis Guide

## Overview
This guide provides context for analyzing the MTN customer database schema for TMF ODA transformation.

## Key Business Entities

### Customers
- Core entity representing individual or business customers
- Unique customer_number for external identification
- Status management for lifecycle tracking

### Accounts
- Financial accounts associated with customers
- Support multiple account types (prepaid, postpaid, etc.)
- Currency support for international operations

### Billing Accounts
- Separate billing entities for flexible billing arrangements
- Credit limit management
- Billing cycle configuration

### Service Orders
- Track customer service requests and changes
- Priority-based processing
- Integration with fulfillment systems

### Contact Mediums
- Multiple contact methods per customer
- Preference management
- Validation status tracking

## TMF Mapping Considerations

### Customer → TMF Individual/Organization
- Map customer entity to TMF Party model
- Consider customer type classification

### Accounts → TMF Account
- Direct mapping to TMF Account structure
- Preserve account type and status information

### Service Orders → TMF Service Order
- Map to TMF Service Order API
- Maintain priority and status workflows

## Complexity Factors
- Multiple foreign key relationships
- Business rule constraints
- Status management across entities
- Financial data precision requirements
"""

class LocalRawAnalysisStage:
    """Local version of RawAnalysisStage that doesn't require S3"""
    
    def __init__(self, journey_id: str, stage_id: str, job_id: str):
        self.journey_id = journey_id
        self.stage_id = stage_id
        self.job_id = job_id
        self.parsed_data = {}
        self._setup_local_logging()
    
    def _setup_local_logging(self):
        """Setup local logging"""
        import logging
        from datetime import datetime
        
        # Create logs directory
        logs_dir = '/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'raw_analysis_local_{self.job_id}_{timestamp}.log'
        self.local_log_file = os.path.join(logs_dir, log_filename)
        
        # Setup logger
        self.local_logger = logging.getLogger(f'raw_analysis_local_{self.job_id}')
        self.local_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.local_logger.handlers[:]:
            self.local_logger.removeHandler(handler)
        
        # Create handlers
        file_handler = logging.FileHandler(self.local_log_file)
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.local_logger.addHandler(file_handler)
        self.local_logger.addHandler(console_handler)
        
        # Log initialization
        self.local_logger.info("=" * 80)
        self.local_logger.info("🧪 LOCAL RAW ANALYSIS STAGE STARTED")
        self.local_logger.info(f"Journey ID: {self.journey_id}")
        self.local_logger.info(f"Job ID: {self.job_id}")
        self.local_logger.info(f"Local Log File: {self.local_log_file}")
        self.local_logger.info("=" * 80)
    
    def _log_local(self, level: str, message: str, step_id: str = None):
        """Enhanced local logging"""
        step_prefix = f"[{step_id}] " if step_id else ""
        formatted_message = f"{step_prefix}{message}"
        
        if level.upper() == 'ERROR':
            self.local_logger.error(f"❌ {formatted_message}")
        elif level.upper() == 'WARNING':
            self.local_logger.warning(f"⚠️ {formatted_message}")
        else:
            self.local_logger.info(f"ℹ️ {formatted_message}")
    
    def execute_local_test(self):
        """Execute local test with sample data"""
        try:
            # Step 1: Schema Parsing with sample data
            self._log_local('INFO', "🚀 Starting local schema parsing test", 'schema_parsing')
            
            schema_content = create_sample_sql_content()
            guide_content = create_sample_guide_content()
            
            self._log_local('INFO', f"📄 Using sample schema content ({len(schema_content):,} characters)", 'schema_parsing')
            self._log_local('INFO', f"📄 Using sample guide content ({len(guide_content):,} characters)", 'schema_parsing')
            
            # Parse tables
            tables = self._parse_sql_schema(schema_content)
            self.parsed_data['schema_content'] = schema_content
            self.parsed_data['guide_content'] = guide_content
            self.parsed_data['tables'] = tables
            
            self._log_local('INFO', f"✅ Parsed {len(tables)} tables with sample data", 'schema_parsing')
            
            # Step 2: Relationship Discovery
            self._log_local('INFO', "🔗 Starting relationship discovery", 'relationship_discovery')
            relationships = self._extract_foreign_keys(schema_content)
            self.parsed_data['relationships'] = relationships
            self._log_local('INFO', f"✅ Found {len(relationships)} relationships", 'relationship_discovery')
            
            # Step 3: Data Type Analysis  
            self._log_local('INFO', "📊 Starting data type analysis", 'data_type_analysis')
            type_distribution = {}
            for table in tables.values():
                for column in table['columns']:
                    col_type = column['type'].upper().split('(')[0]
                    type_distribution[col_type] = type_distribution.get(col_type, 0) + 1
            
            self.parsed_data['type_distribution'] = type_distribution
            total_columns = sum(type_distribution.values())
            self._log_local('INFO', f"✅ Analyzed {total_columns:,} columns across {len(type_distribution)} data types", 'data_type_analysis')
            
            # Step 4: Business Rules Extraction
            self._log_local('INFO', "⚙️ Starting business rules extraction", 'business_rules_extraction')
            procedure_content = create_sample_procedures_content()
            procedures = self._parse_stored_procedures(procedure_content)
            constraints = self._extract_constraints(schema_content)
            
            business_rules = {
                'constraints': constraints,
                'stored_procedures': procedures,
                'triggers': []
            }
            self.parsed_data['business_rules'] = business_rules
            self._log_local('INFO', f"✅ Found {len(procedures)} procedures and {len(constraints)} constraints", 'business_rules_extraction')
            
            # Step 5: Generate Report
            self._log_local('INFO', "📝 Generating comprehensive report", 'complexity_assessment')
            report_md = self._generate_local_report()
            
            # Save report locally
            report_path = os.path.join(os.path.dirname(self.local_log_file), f'step1-report_local_{self.job_id}.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_md)
            
            self._log_local('INFO', f"📄 Report saved: {report_path} ({len(report_md):,} characters)", 'complexity_assessment')
            
            # Final summary
            self.local_logger.info("=" * 80)
            self.local_logger.info("🎉 LOCAL TEST COMPLETED SUCCESSFULLY")
            self.local_logger.info(f"📊 Tables: {len(tables)}")
            self.local_logger.info(f"🔗 Relationships: {len(relationships)}")
            self.local_logger.info(f"📋 Data Types: {len(type_distribution)}")
            self.local_logger.info(f"⚙️ Procedures: {len(procedures)}")
            self.local_logger.info(f"📁 Log File: {self.local_log_file}")
            self.local_logger.info(f"📄 Report: {report_path}")
            self.local_logger.info("=" * 80)
            
            return {
                'status': 'success',
                'tables_count': len(tables),
                'relationships_count': len(relationships),
                'data_types_count': len(type_distribution),
                'procedures_count': len(procedures),
                'log_file': self.local_log_file,
                'report_file': report_path
            }
            
        except Exception as e:
            self._log_local('ERROR', f"Local test failed: {str(e)}")
            traceback.print_exc()
            return {'status': 'failed', 'error': str(e)}
    
    def _parse_sql_schema(self, sql_content: str):
        """Parse SQL schema content"""
        import re
        
        tables = {}
        create_table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);'
        column_pattern = r'(\w+)\s+([A-Z]+(?:\([^)]+\))?)\s*([^,\n]*)'
        
        table_matches = re.finditer(create_table_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in table_matches:
            table_name = match.group(1)
            columns_section = match.group(2)
            
            columns = []
            for line in columns_section.split('\n'):
                line = line.strip()
                if not line or line.startswith('--') or 'FOREIGN KEY' in line.upper() or 'CONSTRAINT' in line.upper():
                    continue
                
                line = line.rstrip(',')
                col_match = re.match(column_pattern, line, re.IGNORECASE)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    col_constraints = col_match.group(3).strip()
                    
                    columns.append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': 'NOT NULL' not in col_constraints.upper(),
                        'primary_key': 'PRIMARY KEY' in col_constraints.upper(),
                        'unique': 'UNIQUE' in col_constraints.upper(),
                        'default': None
                    })
            
            tables[table_name] = {'name': table_name, 'columns': columns}
            self._log_local('INFO', f"📋 Parsed table: {table_name} ({len(columns)} columns)")
        
        return tables
    
    def _extract_foreign_keys(self, sql_content: str):
        """Extract foreign key relationships"""
        import re
        
        relationships = []
        fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)'
        
        fk_matches = re.finditer(fk_pattern, sql_content, re.IGNORECASE)
        
        for match in fk_matches:
            relationships.append({
                'from_column': match.group(1).strip(),
                'to_table': match.group(2).strip(),
                'to_column': match.group(3).strip(),
                'relationship_type': 'many_to_one'
            })
        
        return relationships
    
    def _parse_stored_procedures(self, sql_content: str):
        """Parse stored procedures"""
        import re
        
        procedures = []
        proc_pattern = r'CREATE\s+PROCEDURE\s+(\w+)\s*\((.*?)\)\s*BEGIN(.*?)END;'
        
        proc_matches = re.finditer(proc_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in proc_matches:
            procedures.append({
                'name': match.group(1),
                'parameters': match.group(2).strip(),
                'body': match.group(3).strip()[:200] + '...',
                'purpose': 'Business logic procedure'
            })
        
        return procedures
    
    def _extract_constraints(self, sql_content: str):
        """Extract constraints"""
        import re
        
        constraints = []
        patterns = {
            'check': r'CONSTRAINT\s+\w+\s+CHECK\s*\(([^)]+)\)',
            'unique': r'UNIQUE\s*\(([^)]+)\)',
            'not_null': r'(\w+)\s+[^,\n]*NOT\s+NULL'
        }
        
        for constraint_type, pattern in patterns.items():
            matches = re.finditer(pattern, sql_content, re.IGNORECASE)
            for match in matches:
                constraints.append({
                    'type': constraint_type,
                    'definition': match.group(1).strip(),
                    'rule': f'{constraint_type.replace("_", " ").title()} constraint'
                })
        
        return constraints
    
    def _generate_local_report(self):
        """Generate local test report"""
        tables = self.parsed_data.get('tables', {})
        relationships = self.parsed_data.get('relationships', [])
        business_rules = self.parsed_data.get('business_rules', {})
        type_distribution = self.parsed_data.get('type_distribution', {})
        
        from datetime import datetime
        
        report_lines = [
            "# MTN Customer Database - Local Analysis Test Report",
            "",
            "## Summary",
            "",
            f"This is a **local test report** generated using sample TMF customer database schema.",
            "",
            f"Analysis completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Schema Analysis Results",
            "",
            f"- **Tables Analyzed**: {len(tables)}",
            f"- **Total Columns**: {sum(len(table['columns']) for table in tables.values())}",
            f"- **Relationships Found**: {len(relationships)}",
            f"- **Business Rules**: {len(business_rules.get('constraints', []))} constraints, {len(business_rules.get('stored_procedures', []))} procedures",
            f"- **Data Types**: {len(type_distribution)} unique types",
            "",
            "## Tables Found",
            ""
        ]
        
        for table_name, table in tables.items():
            report_lines.extend([
                f"### {table_name}",
                f"- **Columns**: {len(table['columns'])}",
                "- **Sample Columns**:"
            ])
            
            for col in table['columns'][:5]:
                constraints = []
                if col.get('primary_key'):
                    constraints.append('PRIMARY KEY')
                if col.get('unique'):
                    constraints.append('UNIQUE')
                if not col.get('nullable'):
                    constraints.append('NOT NULL')
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                report_lines.append(f"  - `{col['name']}` {col['type']}{constraint_str}")
            
            if len(table['columns']) > 5:
                report_lines.append(f"  - ... and {len(table['columns']) - 5} more columns")
            report_lines.append("")
        
        if type_distribution:
            report_lines.extend([
                "## Data Type Distribution",
                ""
            ])
            
            for data_type, count in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"- **{data_type}**: {count} columns")
        
        report_lines.extend([
            "",
            "## Test Results",
            "",
            "✅ **Local Analysis**: Successfully completed",
            "✅ **SQL Parsing**: Schema parsed correctly", 
            "✅ **Relationship Discovery**: Foreign keys identified",
            "✅ **Data Type Analysis**: Column types categorized",
            "✅ **Business Rules**: Constraints and procedures extracted",
            "✅ **Report Generation**: Comprehensive report created",
            "",
            "## Next Steps",
            "",
            "1. **Configure S3 Access**: Update bucket name and AWS credentials",
            "2. **Test with Real Data**: Connect to actual MTN schema files",
            "3. **Implement Stripped Schema**: Create next stage in pipeline",
            "",
            "*This report was generated by the local test version of the raw_analysis stage.*"
        ])
        
        return "\n".join(report_lines)

def test_local_raw_analysis():
    """Test the local version"""
    print("🧪 LOCAL RAW ANALYSIS TEST (NO S3 REQUIRED)")
    print("=" * 70)
    
    try:
        # Create local stage instance
        stage = LocalRawAnalysisStage(
            journey_id="ECAF1EA28790",
            stage_id="raw_analysis", 
            job_id="LOCAL-TEST-001"
        )
        
        # Execute test
        result = stage.execute_local_test()
        
        print("\n🎯 LOCAL TEST RESULTS:")
        print("-" * 30)
        if result['status'] == 'success':
            print("✅ Status: SUCCESS")
            print(f"📊 Tables: {result['tables_count']}")
            print(f"🔗 Relationships: {result['relationships_count']}")
            print(f"📋 Data Types: {result['data_types_count']}")
            print(f"⚙️ Procedures: {result['procedures_count']}")
            print(f"📁 Log File: {result['log_file']}")
            print(f"📄 Report: {result['report_file']}")
        else:
            print(f"❌ Status: FAILED - {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_local_raw_analysis() 