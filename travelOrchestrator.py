import os
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool,CodeInterpreterTool

from hotelAgent import HotelSearchAgentBuilder
from weatherAgent import WeatherSearchAgentBuilder
from localEventsAgent import LocalEventsSearchAgentBuilder
from contentSerializerAgent import ContentSerializerAgentBuilder
from flightsAgent import FlightsSearchAgentBuilder

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

os.environ["PROJECT_CONNECTION_STRING"] = "eastus.api.azureml.ms;63881738-85bc-43fc-bfca-f55eee0444ca;gen-ai-lab-dminchew;project-demo-bk6v"
os.environ["BING_CONNECTION_NAME"] = "bing_api"
os.environ["AOI_ENDPOINT"]  = "https://agent-ai-servicesbk6v.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-08-01-preview"


az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o-mini",
    api_version="2024-05-01-preview",
    model = "gpt-4o-mini",
    azure_endpoint=os.environ["AOI_ENDPOINT"],
    azure_ad_token_provider=token_provider, 
)

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

bing_connection = project_client.connections.get(connection_name=os.environ["BING_CONNECTION_NAME"])
conn_id = bing_connection.id

 
hotel_search_agent = HotelSearchAgentBuilder(
    project_client=project_client
    , model_client=az_model_client
    , bingConnection=conn_id).getAgent()

flight_search_agent = FlightsSearchAgentBuilder(
    project_client=project_client
    , model_client=az_model_client
    , bingConnection=conn_id).getAgent()


weather_search_agent = WeatherSearchAgentBuilder(
    project_client=project_client
    , model_client=az_model_client
    , bingConnection=conn_id).getAgent()


local_events_search_agent = LocalEventsSearchAgentBuilder(
    project_client=project_client
    , model_client=az_model_client
    , bingConnection=conn_id).getAgent()


save_content_agent = ContentSerializerAgentBuilder(
     project_client=project_client
    , model_client=az_model_client
    , bingConnection=conn_id).getAgent()


format_agent = AssistantAgent(
    name="format_agent",
    model_client=az_model_client,
    system_message="""
        You are a text formatter, please help me write concise and formatted answers based on search results from other agents."
    """
)

text_termination = TextMentionTermination("Saved")
max_message_termination = MaxMessageTermination(16)
termination = text_termination | max_message_termination

groupChat = RoundRobinGroupChat(
        [
             hotel_search_agent
            #,local_events_search_agent
            #,weather_search_agent
            ,flight_search_agent
            ,format_agent
            ,save_content_agent
        ]
        ,termination_condition=termination
        ,max_turns=8)



async def run_task():
    user_input = input("What are your travel plans? ")
    async for result in groupChat.run_stream(task=user_input):
        pass #print(result)
        


async def main():
    await run_task()

asyncio.run(main())