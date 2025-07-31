# System Interaction Diagram

## Overview
This diagram illustrates how the AI Native Telecom Analytics system components interact with each other, including external systems (Webex, Salesforce, Office 365) and internal components (MCP Server, Dashboard UI, Langgraph).

## Interaction Diagram

```mermaid
graph TB
    %% External Systems
    subgraph "External Systems"
        WX[Webex Platform]
        SF[Salesforce CRM]
        O365[Office 365]
    end
    
    %% User Interface Layer
    subgraph "User Interface Layer"
        UI[Dashboard UI]
        LG[Langgraph System]
    end
    
    %% Integration Layer
    subgraph "Integration Layer"
        MCPC[MCP Connector]
    end
    
    %% Core Processing Layer
    subgraph "MCP Server"
        subgraph "MCP Tools"
            WXT[Webex Connector Tool]
            SFT[Salesforce Connector Tool]
            O365T[Office 365 Connector Tool]
            TGT[Transcript Generator Tool]
            CAT[Call Analysis Tool]
            RGT[Report Generator Tool]
        end
    end
    
    %% User Interactions
    UI -->|Analytics Queries| MCPC
    LG -->|Natural Language Queries| MCPC
    MCPC -->|Route Requests| WXT
    MCPC -->|Route Requests| SFT
    MCPC -->|Route Requests| O365T
    MCPC -->|Route Requests| CAT
    MCPC -->|Route Requests| RGT
    
    %% External System Interactions
    WX -->|Webhook Triggers| WXT
    WXT -->|API Calls for Recordings| WX
    SFT -->|Push Call Data & Insights| SF
    O365T -->|Retrieve Supplementary Data| O365
    
    %% Internal Tool Interactions
    WXT -->|Call Recordings| TGT
    TGT -->|Transcripts| CAT
    CAT -->|Analysis Results| RGT
    RGT -->|JSON & Markdown Reports| UI
    CAT -->|Call Insights| SFT
    
    %% Response Flow
    MCPC -->|Analytics Data| UI
    MCPC -->|Query Results| LG
    
    %% Styling
    classDef external fill:#e1f5fe
    classDef ui fill:#f3e5f5
    classDef integration fill:#fff3e0
    classDef tools fill:#e8f5e8
    
    class WX,SF,O365 external
    class UI,LG ui
    class MCPC integration
    class WXT,SFT,O365T,TGT,CAT,RGT tools
```

## Component Descriptions

### External Systems
- **Webex Platform**: Source of call recordings and metadata, provides webhook notifications
- **Salesforce CRM**: Target system for call insights and customer record updates
- **Office 365**: Supplementary data source for additional context

### User Interface Layer
- **Dashboard UI**: Primary visualization interface for analytics and reports
- **Langgraph System**: Natural language query interface for intelligent system interaction

### Integration Layer
- **MCP Connector**: Middleware that routes requests between UI components and MCP Server

### MCP Tools (Core Processing)
- **Webex Connector Tool**: Handles Webex API interactions and call data retrieval
- **Salesforce Connector Tool**: Manages Salesforce integration and data push operations
- **Office 365 Connector Tool**: Retrieves supplementary data from Office 365
- **Transcript Generator Tool**: Converts audio recordings to text transcripts
- **Call Analysis Tool**: Performs AI-driven analysis on call transcripts
- **Report Generator Tool**: Creates structured JSON and markdown reports

## Key Interaction Patterns

1. **Event-Driven Collection**: Webex webhooks trigger automatic call data collection
2. **API-Based Integration**: REST APIs enable seamless data exchange with external systems
3. **Centralized Processing**: MCP Server serves as the central hub for all tool operations
4. **Multi-Channel Output**: Results are delivered via both structured APIs and user interfaces
5. **Intelligent Querying**: Natural language interface enables intuitive system interaction

## Security Considerations
- All external API communications use secure authentication mechanisms
- Data flows through controlled integration points
- Sensitive call data is processed within the secure MCP Server environment