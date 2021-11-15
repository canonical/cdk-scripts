# cdk-scripts
Various scripts for Charmed Kubernetes management

## Setup

```bash
poetry install
```

### Configuration
Some of the scripts require configuration to use. The most recently developed scripts for automating the team scrum are in the scrum folder. These
scripts utilize utils.py to provide a common entry point to configure team specific values. This includes API Keys, Trello Boards, and several
other parameters. This script is using python confuse for yaml configuration input. The search path for the configuration is documented [on the
webiste][https://confuse.readthedocs.io/en/latest/usage.html#search-paths]. The application name is `cdk-scripts`, therefore a configuration file
for linux would be located at `~/.config/cdk-scripts/config.yaml`.

An example configuration file is:

```yaml
Github:
  # This needs to be a Personal Access Token (PAT) with read access to all relevant orgs and repos
  api_key: REDACTED
Jira:
    api_key: REDACTED
    email: REDACTED
    server: https://warthogs.atlassian.net
CDK:
    feedback_product: Charmed Kubernetes
    github_org: "charmed-kubernetes"
    repo_sources:
      - github_org: "charmed-kubernetes"
    jira_project: "CK"
    product_categories:
      - "Charmed Kubernetes"
MicroK8s:
    feedback_product: MicroK8s
    github_org: Canonical
    github_team: MicroK8s
    repo_sources:
      - github_org: Ubuntu
        github_repos:
          - "microk8s"
      - github_org: Canonical
        github_team: MicroK8s
    jira_project: "MK"
    product_categories:
        - "MicroK8s"
Kubeflow:
    feedback_product: Kubeflow
    github_org: Canonical
    github_team: Kubeflow
    repo_sources:
      - github_org: Canonical
        github_team: Kubeflow
    jira_project: "KF"
    product_categories:
        - "General"
Test:
    # feedback_product:
    product_categories:
      - "Quality/Release"
```

Not all configuration is necessary for all scripts, configuration is loaded when needed and teams that you are not running the script for can be
left unconfigured.

### Github
For scripts that interact with Github, you'll need a personal access token. You can generate these for your account at:
https://github.com/settings/tokens

### Jira
Jira requires the use of an API key and email. You can generate these for your account at:
https://id.atlassian.com/manage-profile/security/api-tokens

## Running

You should use Poetry to run the scripts as well:

```bash
poetry run scrum/check-pr.py --teams CDK Kubeflow
```
