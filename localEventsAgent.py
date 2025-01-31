import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool,CodeInterpreterTool

class LocalEventsSearchAgentBuilder:
    
    def __init__(self, project_client: AIProjectClient, model_client: AzureOpenAIChatCompletionClient, bingConnection: str):
        self.projectClient = project_client
        self.modelClient = model_client
        self.bingConnection = bingConnection


    async def localEventsSearchTool(self, query: str) -> str:
        print("Local Events Agent working .......")

        project_client = self.projectClient
        conn_id = self.bingConnection
        bing = BingGroundingTool(connection_id=conn_id)
        
        # with project_client:
        agent = project_client.agents.create_agent(
                model="gpt-4",
                name="my-assistant",
                instructions="""        
                    You are a web search agent for.
                    Your only tool is search_tool - use it to find information.
                    You can make up to 16 search calls at a time.
                    Once you have the results, you never do calculations based on them.
                """,
                tools=bing.definitions,
                headers={"x-ms-enable-preview": "true"}
            )
        #print(f"Created agent, ID: {agent.id}")

        # Create thread for communication
        thread = project_client.agents.create_thread()
        #print(f"Created thread, ID: {thread.id}")

        # Create message to thread
        message = project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query,
        )
        #print(f"SMS: {message}")
            # Create and process agent run in thread with tools
        run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
        #print(f"Run finished with status: {run.status}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")

            # Delete the assistant when done
        project_client.agents.delete_agent(agent.id)
        #print("Deleted agent")

            # Fetch and log all messages
        messages = project_client.agents.list_messages(thread_id=thread.id)
        #print("Messages:"+ messages["data"][0]["content"][0]["text"]["value"])

            # project_client.close()

        return messages["data"][0]["content"][0]["text"]["value"]
    
    def getAgent(self):
        return AssistantAgent(
            name="events_search_agent",
            model_client=self.modelClient,
            tools=[self.localEventsSearchTool],
            system_message="You are a search expert for local events at a given location, help me use tools to find relevant knowledge",
        )