# cdk-scripts
Various scripts for Charmed Kubernetes management

## Setup

```bash
virtualenv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

### Github
For scripts that interact with Github, you'll need a
`GITHUB_ACCESS_TOKEN` defined. You can create a personal access token at
https://github.com/settings/tokens.

Example:
```bash
GITHUB_ACCESS_TOKEN=<your access token> ./list-charmed-kubernetes-repos.py
```

