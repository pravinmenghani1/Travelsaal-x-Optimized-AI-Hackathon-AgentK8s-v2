from openai import OpenAI
from typing import List, Dict
import json
import os
from .tools.base import Tool

REACT_AGENT_SYSTEM_PROMPT = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""

class AgentPro:
    def __init__(self, llm=None, tools: List[Tool] = [], system_prompt: str = None, react_prompt: str = REACT_AGENT_SYSTEM_PROMPT):
        super().__init__()
        self.client = llm if llm else OpenAI()
        self.tools = self.format_tools(tools)
        self.react_prompt = react_prompt.format(
            tools="\n\n".join(map(lambda tool: tool.get_tool_description(), tools)),
            tool_names=", ".join(map(lambda tool: tool.name, tools)))
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        self.messages.append({"role": "system", "content": self.react_prompt})

    def format_tools(self, tools: List[Tool]) -> Dict:
        tool_names = list(map(lambda tool: tool.name, tools))
        return dict(zip(tool_names, tools))

    def parse_action_string(self, text):
        lines = text.split('\n')
        action = None
        action_input = []
        is_action_input = False

        for line in lines:
            if line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
                continue

            if line.startswith('Action Input:'):
                is_action_input = True
                input_text = line.replace('Action Input:', '').strip()
                if input_text:
                    action_input.append(input_text)
                continue

            if line.startswith('Observation:'):
                is_action_input = False
                continue

            if is_action_input and line.strip():
                action_input.append(line.strip())

        action_input = '\n'.join(action_input)
        try:
            action_input = json.loads(action_input)
        except Exception:
            pass
        return action, action_input

    def tool_call(self, response):
        action, action_input = self.parse_action_string(response)
        try:
            if action.strip().lower() in self.tools:
                tool_observation = self.tools[action].run(action_input)
                return f"Observation: {tool_observation}"
            return f"Observation: Tool '{action}' not found. Available tools: {list(self.tools.keys())}"
        except Exception as e:
            return f"Observation: There was an error executing the tool\nError: {e}"

    def add_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str):
        self.messages.append({"role": "assistant", "content": message})

    def generate_prescriptive_report(self):
        user_messages = [m["content"] for m in self.messages if m["role"] == "user"]
        assistant_messages = [m["content"] for m in self.messages if m["role"] == "assistant"]

        risks = []
        recommendations = []

        for msg in assistant_messages:
            if "Risk:" in msg:
                risks.append(msg.split("Risk:")[-1].strip())
            if "Recommendation:" in msg:
                recommendations.append(msg.split("Recommendation:")[-1].strip())

        summary = """
### EKS Operational Report

🚨 **Risks Identified**

"""
        summary += "\n\n".join([f"- {r}" for r in risks]) if risks else "- No risks identified."
        summary += "\n\n✅ **Recommendations**\n\n"
        summary += "\n\n".join([f"- {r}" for r in recommendations]) if recommendations else "- No specific recommendations."

        return summary

    def __call__(self, prompt):
        self.add_user_message(prompt)
        response = ""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
        try:
            if openrouter_api_key:
                print(f"Using OpenRouter with model: {model_name} for agent conversation")
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)
                while True:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=self.messages,
                        max_tokens=8000
                    ).choices[0].message.content.strip()
                    self.add_assistant_message(response)
                    print("="*80)
                    print(response)
                    print("="*80)
                    if "Final Answer" in response:
                        return response.split("Final Answer:")[-1].strip()
                    if "Action" in response and "Action Input" in response:
                        observation = self.tool_call(response)
                        self.add_assistant_message(observation)
            else:
                print("OpenRouter API key not found, using default OpenAI client with gpt-4o-mini")
                while True:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.messages,
                        max_tokens=8000
                    ).choices[0].message.content.strip()
                    self.add_assistant_message(response)
                    print("="*80)
                    print(response)
                    print("="*80)
                    if "Final Answer" in response:
                        return response.split("Final Answer:")[-1].strip()
                    if "Action" in response and "Action Input" in response:
                        observation = self.tool_call(response)
                        self.add_assistant_message(observation)
        except Exception as e:
            print(f"Error with primary model: {e}")
            print("Falling back to default OpenAI client with gpt-4o-mini")
            try:
                while True:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.messages,
                        max_tokens=8000
                    ).choices[0].message.content.strip()
                    self.add_assistant_message(response)
                    print("="*80)
                    print(response)
                    print("="*80)
                    if "Final Answer" in response:
                        return response.split("Final Answer:")[-1].strip()
                    if "Action" in response and "Action Input" in response:
                        observation = self.tool_call(response)
                        self.add_assistant_message(observation)
            except Exception as e2:
                print(f"Critical error with all models: {e2}")
                return f"Error: Failed to generate response with both primary and fallback models. Details: {str(e2)}"
