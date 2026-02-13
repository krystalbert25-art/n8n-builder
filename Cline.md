# n8n Workflow Builder with Claude

## Project Purpose
This project leverages Claude AI to assist in creating high-quality, production-ready workflows in n8n automation platform. By combining natural language requests with n8n tools, we can rapidly design, build, and optimize automation workflows.

## Available Tools & Integration

### 1. n8n MCP Server
The n8n Model Context Protocol (MCP) server provides programmatic access to your n8n instance, enabling:
- Workflow creation and modification
- Node configuration and management
- Workflow deployment and testing
- Access to node types and credentials
- Workflow execution and monitoring

### 2. n8n Skills
Pre-built skill functions that streamline common workflow patterns and operations:
- Data transformation utilities
- Integration helpers
- Conditional logic builders
- Error handling patterns
- Performance optimization techniques

## Workflow Creation Guidelines

### Quality Standards
1. **Clarity & Maintainability**
   - Use descriptive node names that reflect their purpose
   - Implement clear data flow and logical sequences
   - Add comments/descriptions to complex sections
   - Follow naming conventions consistently

2. **Error Handling**
   - Include error handlers for external API calls
   - Implement retry logic where appropriate
   - Create fallback paths for edge cases
   - Validate input data before processing

3. **Performance Optimization**
   - Minimize unnecessary data transformations
   - Use batch operations when available
   - Implement proper pagination for large datasets
   - Cache static data appropriately

4. **Security Best Practices**
   - Use credentials/environment variables instead of hardcoding secrets
   - Validate and sanitize all external inputs
   - Implement rate limiting and throttling
   - Log sensitive operations securely

## Workflow Development Process

### Request Handling
1. **Understand Requirements**: Clarify the workflow's objectives and scope
2. **Design Architecture**: Plan node structure and data flow
3. **Implement Workflow**: Build using n8n tools and skills
4. **Test & Validate**: Verify functionality across various scenarios
5. **Deploy & Monitor**: Activate workflow and monitor execution

### Best Practices
- Start with workflow templates when available
- Test with sample data before production deployment
- Document workflow purpose and key logic
- Version control workflow configurations
- Monitor workflow performance and error rates

## Communication Style
- Ask clarifying questions if workflow requirements are ambiguous
- Provide explanations of workflow logic and design decisions
- Suggest optimizations and improvements proactively
- Report any issues or limitations encountered

## Success Criteria
Workflows should be:
✓ Functional and tested across multiple scenarios
✓ Well-structured and maintainable
✓ Properly documented
✓ Secure and efficient
✓ Aligned with user requirements
