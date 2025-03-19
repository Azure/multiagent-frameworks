# Multi-agent Framework with Azure AI Agent Service

This repository contains the code for the multi-agent framework with Azure AI Agent Service. The framework is designed to support the development of multi-agent systems with the help of Azure AI Agent Service. The framework provides a set of APIs to interact with the Azure AI Agent Service and a set of tools to help developers to build multi-agent systems.

## Getting Started

Create a new Project in AI Foundry as described in the [Quick Start](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure).

Use the basic option to create the project. 


## Key Concepts

- Azure AI Agents uses the same wire protocol as Azure OpenAI Assistant API. So the conversation uses Threads, and messages are created in the thread and agents can see the complete conversation history in the thread.
- Azure AI Agent is created in the context of the AI Foundry Project which needs to be configured with necessary models and settings. The models could be Azure Open AI Models or models in the model catalog.  
- As more and more messages are added to the same thread, it can easliy fill up the context window of the model.

## Running Multi Agent Scenario with Azure AI Agent Service

- Update .env file with the AI Project Connection String. 

