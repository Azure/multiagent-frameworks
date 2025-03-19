# Multi-Agent Frameworks

Multi-Agent frameworks aide in developing powerful applications with the goal to improve accuracy, reduce hallucinations, handle complex user tasks by integrating Large Language Models into enterprise applications. 


This repository contains a collection of multi-agent frameworks that can be used to simulate and study multi-agent systems. The frameworks are implemented in Python and are designed to be easy to use and extend. The frameworks compared in this repository are:

- [Autogen v0.4](https://www.microsoft.com/en-us/research/blog/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/)
- [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
- [Azure AI Agent Service](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview?view=azure-python-preview)

This repo is designed to easily understand different frameworks and help developers with nuances and compare the different approaches. 

A simple scenario is used to demonstrate the capabilities of the frameworks. The scenario is a simple conversation between two agents for a fintech company helping users with Account and Transaction related questions.
These scenarios are addressed:

- Concurrency 
    
    Handling simulatneous conversations between users an agents.

- Agent routing

    Routing the user task to the correct agent based on the user query and enabling the agents to communicate with each other.

- LLM Swapping

    Swap the LLM models used by the agents based on task criticalility. For example, using a more powerful model for router and a simpler model for agents.

- Chat History and Memory Management

    Managing the chat history and memory of the agents and maintain chat history across multiple users and agents. 

- Function Calling

    Implementing function calling across agents and router.

- Observability

    Monitoring and tracing conversations between the agents and the users.

- Authentication

    Authenticating users with Microsoft Entra. 


Each framework is implemented in a separate folder. The folder contains the implementation of the framework and the scenario. Please refer to the README.md in each folder for more details on how to run the scenario using the framework.


## Common Installation Steps

- Azure OpenAI Service or AI Foundry Access is required. 
- AZ CLI is required and user should be logged in with az login. 
- Python 3.11 or higher is installed. 
- Clone the repository

    ```bash or cmd
    git clone https://github.com/Azure/multiagent-frameworks.git

- Python Steps:
    
    ```bash or cmd
    python -m venv venv

    # cmd 
    venv\Scripts\activate

    # bash
    source venv/bin/activate

    pip install -r requirements.txt


## Multi Agent Scenario 

The a multi agent scenario, the key concept is that the agents needs to be aware of other agents' tools and capabilities. The capabilities are defined in the system message for each agents and tools using python functions are made avaialble to each agent. 
The system message for the router agent will typically contain the list of agents and their capabilities. The system message for the agents will contain the list of tools and the capabilities of the agents.
The router agent will also have instructions on which agent to route the user question to based on the user question.

Now given a user questions, the router agent will decompose the questions and assign tasks to the agents. The agents will then use the tools to answer the questions and submit a resposne back to a common location which could be a chat history, and pub sub topic, or a thread in the case of Assistant API. 
Then a Final responder agent will inspect the chat history and determine whether the user questions has been answered or not. If the user question has been answered, the final responder will return the final answer to the user. Otherwise it will submit the question to the router agent for further processing.

The scenario that is implemented in this repository is a simple 2 agent and a router agent use case, who can answer user questions about accounts and transactions for a fictious company called Transify which is a Financial Services company.

This scenario is implemented in each of the frameworks and the implementation details are provided in the README.md in each of the framework folders.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
