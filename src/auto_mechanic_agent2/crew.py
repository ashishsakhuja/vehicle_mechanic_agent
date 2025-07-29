# src/auto_mechanic_agent2/crew.py

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
import logging

from auto_mechanic_agent2.tools.custom_tool import ManualQATool, PartsScraperTool
from auto_mechanic_agent2.knowledge.vehicle_knowledge_source import ManualContentIndex

load_dotenv()

@CrewBase
class AutoMechanicAgent:
    """AutoMechanicAgent crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # register your new Pinecone Q&A and parts scraper tools
    tools = [
        ManualQATool(),
        PartsScraperTool(),
    ]

    def __init__(self):
        super().__init__()
        load_dotenv()
        logging.basicConfig(level=logging.INFO)

        # initialize the Pinecone-backed manual index
        self.manual_index = ManualContentIndex()

    # ───────────────────────────── Agents ──────────────────────────────

    @agent
    def text_parser(self) -> Agent:
        """Cleans up the user’s problem into a concise summary"""
        return Agent(
            config=self.agents_config["text_parser"],
            verbose=True,
        )

    @agent
    def manual_qa_agent(self) -> Agent:
        """Vector-search the manuals and answer via RetrievalQA"""
        qa_tool = ManualQATool(
            manual_index=self.manual_index,
            top_k=4,
            model_name="gpt-4.1-mini",
            temperature=0.0,
        )
        return Agent(
            config=self.agents_config["manual_qa_agent"],
            tools=[qa_tool],
            verbose=True,
        )

    @agent
    def mechanic_expert(self) -> Agent:
        """Provides expert advice on car issues (without manual lookup)"""
        return Agent(
            config=self.agents_config["mechanic_expert"],
            tools=[],
            verbose=True,
        )

    @agent
    def mechanic_supervisor(self) -> Agent:
        """Supervises the mechanic expert and ensures proper solution generation"""
        return Agent(
            config=self.agents_config["mechanic_supervisor"],
            tools=[],
            verbose=True,
        )

    @agent
    def formatter_agent(self) -> Agent:
        """Formats the solution into a PDF-friendly format"""
        return Agent(
            config=self.agents_config["formatter_agent"],
            verbose=True,
        )

    @agent
    def parts_scraper_agent(self) -> Agent:
        """Generates part search URLs"""
        return Agent(
            config=self.agents_config["parts_scraper_agent"],
            tools=[PartsScraperTool()],
            verbose=True,
        )

    # ───────────────────────────── Tasks ──────────────────────────────

    @task
    def parse_problem_task(self) -> Task:
        return Task(
            config=self.tasks_config["parse_problem_task"],
        )

    @task
    def lookup_manual_task(self) -> Task:
        """Retrieve and answer directly from Pinecone index"""
        return Task(
            config=self.tasks_config["lookup_manual_task"],
            tools=[
                ManualQATool(
                    manual_index=self.manual_index,
                    top_k=4,
                    model_name="gpt-4.1-mini",
                    temperature=0.0,
                ),
            ],
        )

    @task
    def generate_solution_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_solution_task"],
        )

    @task
    def scrape_parts_task(self) -> Task:
        return Task(
            config=self.tasks_config["scrape_parts_task"],
            tools=[PartsScraperTool()],
        )

    @task
    def enrichment_task(self) -> Task:
        return Task(
            config=self.tasks_config["enrichment_task"],
        )

    @task
    def format_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config["format_guide_task"],
        )

    # ───────────────────────────── Crew Definition ──────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.text_parser(),
                self.manual_qa_agent(),
                self.mechanic_expert(),
                self.mechanic_supervisor(),
                self.parts_scraper_agent(),
                self.formatter_agent(),
            ],
            tasks=[
                self.parse_problem_task(),
                self.lookup_manual_task(),
                self.generate_solution_task(),
                self.scrape_parts_task(),
                self.enrichment_task(),
                self.format_guide_task(),
            ],
            process=Process.sequential,
            tools=[
                ManualQATool(
                    manual_index=self.manual_index,
                    top_k=4,
                    model_name="gpt-4.1-mini",
                    temperature=0.0,
                ),
                PartsScraperTool(),
            ],
            verbose=True,
        )