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
```
Trello:
    api_key: string, trello api key
    api_secret: string, trello api secret
Github:
    api_key: string, github api key 
TEAM: The name of a team that all of the following parameters are for
    scrum_id: string, the short ID for the scrum board for this team
    sizing_id: string, the short ID for the sizing board for this team
    backlog_id: string, the short ID for the backlog board for this team
    feedback_product: string, tab from the feedback sheet or this team
    github_org: string, the github organization to use when looking up repos for this team
    github_team: string, the team in the org if not provided all repos in the org will be used
    product_categories: list of strings, the headings from the roadmap sheet which belong to this team
Roadmap:
    key: string, the document ID for the roadmap GDoc
    org: string, the organization (tab) this team belongs to
    team: string, the team (column name) for this teams roadmap items
Feedback:
    key: string, the docuemnt ID for the feedback GDoc
```

An example of this at the time of this writing, with keys redacted is
```yaml
Trello:
    api_key: REDACTED
    api_secret: REDACTED
Github:
    api_key: REDACTED
CDK:
    scrum_id: Ncvfetcy
    sizing_id: Usrca8sO
    backlog_id: WrN1ZaGD 
    feedback_product: Charmed Kubernetes
    github_org: "charmed-kubernetes"
    product_categories:
        - "Charmed Kubernetes"
Test:
    scrum_id: Lm8ECsCJ
    backlog_id: FG1MSdKc 
    sizing_id: 0wx1D61U
    product_categories:
        - "Quality/Release"
MicroK8s:
    scrum_id: xVYrUCPG 
    backlog_id: jptdFJws
    sizing_id: nwzp00z5 
    feedback_product: MicroK8s
    github_org: Canonical
    github_team: MicroK8s
    product_categories:
        - "MicroK8s"
Kubeflow:
    scrum_id: Kltuqovk 
    backlog_id: b3blqVPK
    sizing_id: ar0qMzyO
    feedback_product: Kubeflow
    github_org: Canonical
    github_team: Kubeflow
    product_categories:
        - "General"
Roadmap:
    key: REDACTED
    org: Cloud
    team: Kubernetes
Feedback:
    key: REDACTED
```

Not all configuration is necessary for all scripts, configuration is loaded when needed and teams that you are not running the script for can be
left unconfigured.

### Github
For scripts that interact with Github, you'll need a
`GITHUB_ACCESS_TOKEN` defined. You can create a personal access token at
https://github.com/settings/tokens.

Example:
```bash
GITHUB_ACCESS_TOKEN=<your access token> ./list-charmed-kubernetes-repos.py
```

### Trello
Trello requires the use of an API key and secret. You can generate these for your account at:
```
https://trello.com/app-key/
```
