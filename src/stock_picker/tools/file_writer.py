
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Define the inputs accepted by the tool
class FileWriterInput(BaseModel):
    file_path: str = Field(
        ...,
        description="Relative path of the file inside the workspace."
    )

    content: str = Field(
        ...,
        description="Complete content that should be written to the file."
    )

    overwrite: bool = Field(
        default=False,
        description="Set to true if an existing file should be overwritten."
    )


# Create the custom tool
class FileWriterTool(BaseTool):
    name: str = "File Writer"

    description: str = (
        "Creates new files or updates existing files inside the project workspace. "
        "Use this tool to save generated Python code, configuration files, and tests."
    )

    args_schema: type[BaseModel] = FileWriterInput

    workspace: Path = Path("workspace")

    def _run(
        self,
        file_path: str,
        content: str,
        overwrite: bool = False
    ) -> str:

        try:
            # Resolve the workspace directory
            workspace = self.workspace.resolve()

            # Resolve the requested file path
            target_file = (workspace / file_path).resolve()

            # Prevent writing outside the workspace
            if not target_file.is_relative_to(workspace):
                return "Error: Access outside the workspace is not allowed."

            # Prevent accidental overwriting
            if target_file.exists() and not overwrite:
                return (
                    f"Error: File already exists: {file_path}. "
                    "Set overwrite=true to replace it."
                )

            # Create parent directories if they don't exist
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Write the content to the file
            target_file.write_text(content, encoding="utf-8")

            return f"Successfully saved file: {file_path}"

        except Exception as e:
            return f"Error writing file: {str(e)}"
