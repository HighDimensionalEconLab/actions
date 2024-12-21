# Push Artifact Repo

This GitHub Action downloads an artifact from a previous workflow and pushes it to a specified repository. It automates transferring build artifacts or generated files to a target GitHub repository.

---

## Features

- Downloads an artifact from a specified workflow run.
- Clones the target repository.
- Copies the downloaded artifact to the target repository.
- Pushes changes to the specified branch of the target repository.

---

## Inputs

| Name               | Description                                              | Required | Default |
|--------------------|----------------------------------------------------------|----------|---------|
| `target_repo_name` | The name of the target repository to push to (e.g., `HighDimensionalEconLab/my-repo`). | **Yes** | N/A     |
| `branch_name`      | The branch name to push to.                              | No       | `main`  |
| `token`        | Token (e.g. PAT_TOKEN) for authentication.        | **Yes** | N/A     |
| `artifact_name`    | The name of the artifact to download from the workflow.  | **Yes** | N/A     |
| `workflow_name`    | The name of the workflow to download the artifact from (e.g., `deploy.yml`). | **Yes** | N/A     |

---

## Usage

Below is an example workflow demonstrating how to use this action.

```yaml
name: Push Artifact Workflow

on:
  workflow_run:
    workflows:
      - "Deploy Workflow"
    types:
      - completed

jobs:
  push-artifact:
    runs-on: ubuntu-latest

    permissions:
      contents: write
      actions: read

    steps:
      - name: Use Push Artifact Repo Action
        uses: HighDimensionalEconLab/actions/push_artifact_repo@v1
        with:
          target_repo_name: "HighDimensionalEconLab/my-target-repo"
          branch_name: "main"
          token: ${{ secrets.PAT_TOKEN }}
          artifact_name: "my-artifact"
          workflow_name: "deploy.yml"
```