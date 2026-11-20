from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from stock_picker.tools.file_reader import FileReaderTool
from stock_picker.tools.file_writer import FileWriterTool
from stock_picker.tools.docker_executor import DockerExecutorTool
from stock_picker.tools.stock_price_tool import StockPriceTool

@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], # type: ignore[index]
            verbose=True
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            tools = [
                FileReaderTool(),
                FileWriterTool(),
                StockPriceTool()
            ]
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            tools = [
                FileReaderTool(),
                FileWriterTool()
            ]
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'], 
            verbose=True,
            tools=[
            FileReaderTool(),
            DockerExecutorTool()
            ]
        )

    @task
    def backend_development_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_development_task"],
        )

    @task
    def frontend_development_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_development_task"],
            context=[self.backend_development_task()]
        )

    @task
    def application_testing_task(self) -> Task:
        return Task(
            config=self.tasks_config["application_testing_task"],
            context=[
                self.backend_development_task(),
                self.frontend_development_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        return Crew(
            agents=[
                self.backend_engineer(),
                self.frontend_engineer(),
                self.test_engineer()
            ], # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,
            manager_agent=self.engineering_lead()
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
