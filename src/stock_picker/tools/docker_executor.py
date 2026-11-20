
import subprocess
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Define the inputs accepted by the tool
class DockerExecutorInput(BaseModel):

    command: str = Field(
        ...,
        description=(
            "Command to execute inside the Docker container. "
            "For example: python -m pytest tests/"
        )
    )

    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Maximum execution time in seconds. Must be between 1 and 300."
    )


# Create the custom Docker execution tool
class DockerExecutorTool(BaseTool):

    name: str = "Docker Code Executor"

    description: str = (
        "Executes Python commands inside an isolated Docker container. "
        "The project workspace is mounted into the container. "
        "Use this tool to run Python programs and automated tests."
    )

    args_schema: type[BaseModel] = DockerExecutorInput

    workspace: Path = Path("workspace")

    def _run(
        self,
        command: str,
        timeout_seconds: int = 60
    ) -> str:

        try:
            # Resolve the project workspace
            workspace = self.workspace.resolve()

            if not workspace.is_dir():
                return "Error: Workspace directory does not exist."

            if not command.strip():
                return "Error: Command cannot be empty."

            # Build the Docker command
            docker_command = [
                "docker",
                "run",
                "--rm",
                "--init",

                # Resource restrictions
                "--memory=512m",
                "--cpus=1.0",
                "--pids-limit=128",

                # Security restrictions
                "--network=none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--read-only",

                # Temporary writable directory
                "--tmpfs=/tmp:rw,nosuid,nodev,size=64m",

                # Mount the project workspace
                "--mount",
                f"type=bind,source={workspace},target=/workspace",

                # Set the working directory
                "--workdir=/workspace",

                # Python execution environment
                "stock-picker-runner:latest",

                # Execute the requested command inside the container
                "sh",
                "-lc",
                command
            ]

            # Execute Docker from the host machine
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False
            )

            # Collect execution results
            output = result.stdout
            errors = result.stderr

            return (
                f"Exit code: {result.returncode}\n\n"
                f"Standard Output:\n{output}\n\n"
                f"Standard Error:\n{errors}"
            )

        except subprocess.TimeoutExpired:
            return (
                f"Error: Execution exceeded the "
                f"{timeout_seconds}-second time limit."
            )

        except FileNotFoundError:
            return (
                "Error: Docker CLI was not found. "
                "Check that Docker Desktop is installed "
                "and available in PATH."
            )

        except Exception as e:
            return f"Error executing Docker command: {str(e)}"
