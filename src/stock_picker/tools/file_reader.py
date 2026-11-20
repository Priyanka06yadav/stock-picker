
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Define the inputs accepted by the tool
class FileReaderInput(BaseModel):
    file_path: str = Field(
        ...,
        description="Relative path of the file inside the workspace."
    )


# Create the custom tool
class FileReaderTool(BaseTool):
    name: str = "File Reader"
    description: str = (
        "Reads the contents of an existing file inside the project workspace. "
        "Use this tool to inspect source code, configuration files, and tests."
    )

    args_schema: type[BaseModel] = FileReaderInput

    workspace: Path = Path("workspace")

    def _run(self, file_path: str) -> str:

        try:
            # Resolve the workspace directory
            workspace = self.workspace.resolve()

            # Resolve the requested file path
            target_file = (workspace / file_path).resolve()

            # Prevent accessing files outside the workspace
            if not target_file.is_relative_to(workspace):
                return "Error: Access outside the workspace is not allowed."

            # Check whether the file exists
            if not target_file.is_file():
                return f"Error: File not found: {file_path}"

            # Read the file
            content = target_file.read_text(encoding="utf-8")

            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"
