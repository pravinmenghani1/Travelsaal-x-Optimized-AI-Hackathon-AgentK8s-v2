# agents/agentk8s.py

from openai import OpenAI
from typing import List, Dict
import json
import os
import re
from .tools.base import Tool

REACT_AGENT_SYSTEM_PROMPT = """
You are an expert in EKS cluster operations. Based on the user's answers, generate a prescriptive action plan for improving the EKS environment. Your recommendations should be divided into three categories:

1. **Short-Term (0–3 months)**: Immediate actions
2. **Medium-Term (3–6 months)**: Actions requiring moderate effort
3. **Long-Term (6–18 months)**: Strategic goals

Use the following format:

Question: [Question from the agent to the user]
Thought: [How the agent will approach this question]
Action: [Action to take, e.g., call a tool]
Action Input: [Input data for the action]
Observation: [Result from the tool or action]
...
Final Answer: [The final action plan with risks and recommendations]

Begin!
"""

class AgentK8s:
    def __init__(self, llm=None, tools: List[Tool] = [], system_prompt: str = None, react_prompt: str = REACT_AGENT_SYSTEM_PROMPT):
        self.client = llm if llm else OpenAI()
        self.tools = self.format_tools(tools)
        # Inject tool descriptions (if any) into the prompt.
        self.react_prompt = react_prompt.format(
            tools="\n\n".join(map(lambda tool: tool.get_tool_description(), tools)),
            tool_names=", ".join(map(lambda tool: tool.name, tools))
        )
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        self.messages.append({"role": "system", "content": self.react_prompt})

    def format_tools(self, tools: List[Tool]) -> Dict:
        tool_names = list(map(lambda tool: tool.name, tools))
        return dict(zip(tool_names, tools))

    def parse_action_string(self, text):
        """
        A simple parser using regular expressions.
        It extracts the first occurrence of 'Action:' and 'Action Input:' content.
        """
        action_match = re.search(r"Action:\s*(.*)", text)
        input_match = re.search(r"Action Input:\s*(.*)", text)
        action = action_match.group(1).strip() if action_match else None
        action_input = input_match.group(1).strip() if input_match else None

        # Try converting input to JSON if possible
        try:
            action_input = json.loads(action_input)
        except Exception:
            pass

        return action, action_input

    def tool_call(self, response):
        """
        Calls a tool if the response contains a valid action.
        """
        action, action_input = self.parse_action_string(response)
        try:
            # Lookup in a case-insensitive way.
            for tool_name, tool in self.tools.items():
                if action and action.strip().lower() == tool_name.lower():
                    tool_observation = tool.run(action_input)
                    return f"Observation: {tool_observation}"
            return f"Observation: Tool '{action}' not found. Available tools: {list(self.tools.keys())}"
        except Exception as e:
            return f"Observation: Error executing tool: {e}"

    def add_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str):
        self.messages.append({"role": "assistant", "content": message})

    def generate_prescriptive_report(self):
        risks = []
        recommendations = []

        for msg in self.messages:
            if msg["role"] == "assistant":
                if "Risk:" in msg["content"]:
                    extracted = msg["content"].split("Risk:")[-1].strip()
                    if extracted:
                        risks.append(extracted)
                if "Recommendation:" in msg["content"]:
                    extracted = msg["content"].split("Recommendation:")[-1].strip()
                    if extracted:
                        recommendations.append(extracted)

        if not risks:
            risks = ["No significant risks identified based on the provided information."]
        if not recommendations:
            recommendations = ["No specific recommendations at this time. Please consult with a DevOps engineer."]

        summary = "### EKS Operational Report\n\n"
        summary += "\U0001F6A8 **Risks Identified**\n\n"
        summary += "\n".join([f"- {r}" for r in risks])
        summary += "\n\n\u2705 **Recommendations**\n\n"
        summary += "\n".join([f"- {r}" for r in recommendations])

        return summary


    def __call__(self, prompt, max_iterations=5):
        """
        Handles a conversation with the LLM. Loops up to max_iterations,
        sending conversation history until a final answer is generated or
        the iteration limit is reached.
        """
        self.add_user_message(prompt)
        response = ""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
        iteration = 0
        try:
            if openrouter_api_key:
                print(f"Using OpenRouter with model: {model_name}")
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)
                while iteration < max_iterations:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=self.messages,
                        max_tokens=8000
                    ).choices[0].message.content.strip()
                    self.add_assistant_message(response)
                    print("="*80)
                    print(response)
                    print("="*80)
                    if "Final Answer:" in response:
                        return response.split("Final Answer:")[-1].strip()
                    if "Action:" in response and "Action Input:" in response:
                        observation = self.tool_call(response)
                        self.add_assistant_message(observation)
                    iteration += 1
                # If no final answer was given within max_iterations, return the last response.
                return self.messages[-1]["content"]
            else:
                print("OpenRouter API key not found, using default OpenAI client with gpt-4o-mini")
                while iteration < max_iterations:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.messages,
                        max_tokens=8000
                    ).choices[0].message.content.strip()
                    self.add_assistant_message(response)
                    print("="*80)
                    print(response)
                    print("="*80)
                    if "Final Answer:" in response:
                        return response.split("Final Answer:")[-1].strip()
                    if "Action:" in response and "Action Input:" in response:
                        observation = self.tool_call(response)
                        self.add_assistant_message(observation)
                    iteration += 1
                return self.messages[-1]["content"]
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"
