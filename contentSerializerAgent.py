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

class ContentSerializerAgentBuilder:
    
    def __init__(self, project_client: AIProjectClient, model_client: AzureOpenAIChatCompletionClient, bingConnection: str):
        self.projectClient = project_client
        self.modelClient = model_client
        self.bingConnection = bingConnection


    async def save_content_tool(self, response_content: str) -> str:

        print("Content Serializer is working .......")
        code_interpreter = CodeInterpreterTool()
            
        agent = self.projectClient.agents.create_agent(
                model="gpt-4o-mini",
                name="my-agent",
                instructions="You are helpful agent",
                tools=code_interpreter.definitions,
                # tool_resources=code_interpreter.resources,
        )

        thread = self.projectClient.agents.create_thread()

        message = self.projectClient.agents.create_message(
                thread_id=thread.id,
                role="user",
                content="""
            
                        You are my Python programming assistant. Generate code,save """+ response_content +
                        
                    """    
                        and execute it according to the following requirements

                        1. Save response content to response-{YYMMDDHHMMSS}.md

                        2. give me the download this file link
                    """,
        )
        # create and execute a run
        run = self.projectClient.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
       # print(f"Run finished with status: {run.status}")

        if run.status == "failed":
                # Check if you got "Rate limit is exceeded.", then you want to get more quota
            print(f"Run failed: {run.last_error}")

            # # delete the original file from the agent to free up space (note: this does not delete your version of the file)
            # self.projectClient.agents.delete_file(file.id)
            # print("Deleted file")

            # print the messages from the agent
        messages = self.projectClient.agents.list_messages(thread_id=thread.id)
        #print(f"Messages: {messages}")

            # get the most recent message from the assistant
        last_msg = messages.get_last_text_message_by_role("assistant")
        if last_msg:
            print(f"Last Message: {last_msg.text.value}")

            # print(f"File: {messages.file_path_annotations}")


        for file_path_annotation in messages.file_path_annotations:

            file_name = os.path.basename(file_path_annotation.text)

            self.projectClient.agents.save_file(file_id=file_path_annotation.file_path.file_id, file_name=file_name,target_dir="./responses")
            

        self.projectClient.agents.delete_agent(agent.id)
        #print("Deleted agent")


            # project_self.projectClientclient.close()


        return "Saved"
        
    
    
    def getAgent(self):
        return AssistantAgent(
            name="save_content_agent",
            model_client=self.modelClient,
            tools=[self.save_content_tool],
            system_message="""
                Save content. Respond with 'Saved' to when your contents are saved.
            """
        )