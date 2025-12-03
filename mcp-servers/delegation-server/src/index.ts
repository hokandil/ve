#!/usr/bin/env node

/**
 * Delegation MCP Server
 * Provides delegate_to_agent tool for KAgent agents
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

const API_URL = process.env.API_URL || 'http://localhost:8000/api';
const AUTH_TOKEN = process.env.DELEGATION_AUTH_TOKEN || '';

const server = new Server(
  {
    name: 'delegation-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'delegate_to_agent',
        description: 'Delegate a task to another agent in your team. Use this when you need a tool or capability you don\'t have.',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: {
              type: 'string',
              description: 'The ID of the agent to delegate to (from Your Team context)',
            },
            task_description: {
              type: 'string',
              description: 'Clear description of what you need the agent to do',
            },
            customer_id: {
              type: 'string',
              description: 'The Customer ID (provided in your system prompt)',
            },
          },
          required: ['agent_id', 'task_description', 'customer_id'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'delegate_to_agent') {
    const { agent_id, task_description, customer_id: arg_customer_id } = request.params.arguments as {
      agent_id: string;
      task_description: string;
      customer_id?: string;
    };

    try {
      // Get customer_id from arguments or environment
      const customer_id = arg_customer_id || process.env.CUSTOMER_ID;

      if (!customer_id) {
        throw new Error('CUSTOMER_ID not provided in arguments or environment');
      }

      // Call backend delegation endpoint
      const response = await fetch(`${API_URL}/messages/delegate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${AUTH_TOKEN}`,
        },
        body: JSON.stringify({
          customer_id,
          target_agent_id: agent_id,
          task: task_description,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Delegation failed: ${error}`);
      }

      const result = await response.json() as { target_agent_name: string; response: string };

      return {
        content: [
          {
            type: 'text',
            text: `Delegation successful. ${result.target_agent_name} responded:\n\n${result.response}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Delegation failed: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Delegation MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
