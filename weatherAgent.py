import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool,CodeInterpreterTool

import random
from datetime import datetime, timedelta

class WeatherSearchAgentBuilder:
    
    def __init__(self, project_client: AIProjectClient, model_client: AzureOpenAIChatCompletionClient, bingConnection: str):
        self.projectClient = project_client
        self.modelClient = model_client
        self.bingConnection = bingConnection


    async def webSearchTool(self, location: str) -> str:
        print("Weather Agent is working .......")
      
        dates_temps = [
            f"{(datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')}: {random.randint(-10, 35)}°C"
            for i in range(15)
        ]

        result_string = ", ".join(dates_temps)

        return f"Weather forecast in {location} is as follows: " + result_string
    
    
    
    def getAgent(self):
        return AssistantAgent(
            name="weather_agent",
            model_client=self.modelClient,
            tools=[self.webSearchTool],
            system_message="You are a weather expert, help me use tools to find relevant knowledge",
        )