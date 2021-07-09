from jira import JIRA
from roadmap.logging import Logger


class Project:
    STORY_POINT_FIELD = "customfield_10016"
    EPIC_NAME_FIELD = "customfield_10011"
    EPIC_LINK_FIELD = "customfield_10014"
    INCLUDE_LABELS = ["21.10"]

    def __init__(self, server, api_key, email, project):
        self._jira = JIRA(server, basic_auth=(email, api_key))
        self._project = project
        self.logger = Logger()

    @property
    def all_issues(self):
        return self.search()

    def search(self, jql="", sort="", sanitize=True):
        """Perofrm a JQL search on the project"""

        query = [f"project={self._project}"]

        if jql:
            query.append("AND")
            query.append(jql)
        if sort:
            query.append(sort)
        else:
            query.append("ORDER BY created DESC")

        query = " ".join(query)
        self.logger.debug(f"Performing Search: {query}")
        return self._jira.search_issues(query)

    def import_trello_issues(self, issues):
        """Create project issues given trello exports"""
        issues = list(issues)
        all_issues = self.search()
        for issue in issues:
            fields = {
                "summary": issue.name,
                "description": issue.description,
            }
            if issue.epic:
                # Epic only fields
                fields[self.EPIC_NAME_FIELD] = issue.name
            else:
                # Story only fields
                if issue.story_points:
                    fields[self.STORY_POINT_FIELD] = float(issue.story_points)
            labels = []
            for label in issue.labels:
                if label.name in self.INCLUDE_LABELS:
                    labels.append(label.name)
            if labels:
                fields["labels"] = labels

            # Update or create issue
            for existing_issue in all_issues:
                if existing_issue.fields.summary == issue.name:
                    self.logger.debug(f"Updating existing issue: {issue.name}")
                    existing_issue.update(fields)
                    break
            else:
                # Create new issue
                fields["issuetype"] = {"name": "Epic" if issue.epic else "Story"}
                self.create_issue(fields)

        self._link_trello_epics(epics=[issue for issue in issues if issue.epic])

    def _link_trello_epics(self, epics):
        for epic in epics:
            self.logger.debug(f"Adding links for epic: {epic.name}")
            epic_name = epic.name.replace("[", "")
            epic_name = epic_name.replace("]", "")
            jira_epics = self.search(jql=f'type="Epic" AND summary ~ "{epic_name}"')
            if jira_epics.total != 1:
                self.logger.error(
                    f"Found {jira_epics.total} epics "
                    f"instead of 1 searching for {epic.name} "
                    "Skipping linking this epic"
                )
                continue
            else:
                epic_key = jira_epics[0].key

            # Process attachments
            for attachment in epic.attachments:
                if not attachment.url.startswith("https://trello.com/c/"):
                    self.logger.debug(f"Skipping {attachment} not a trello card")
                    continue
                title_text = " ".join(attachment.url.split("-")[1:])
                # These are illegal in search text, only dealing with the ones I have
                title_text = title_text.replace("[", "")
                title_text = title_text.replace("]", "")
                jira_issues = self.search(
                    jql=f'type="Story" AND summary ~ "{title_text}"'
                )
                if jira_issues.total != 1:
                    self.logger.error(
                        f"Found {jira_issues.total} issues "
                        f"instead of 1 searching for {title_text} "
                        "Skipping linking this attachment"
                    )
                    continue
                else:
                    jira_issue = jira_issues[0]

                fields = {self.EPIC_LINK_FIELD: epic_key}
                jira_issue.update(fields)
                self.logger.info(f"Added {epic_key} to {jira_issue}")

    def create_issue(self, fields):
        """Create an issue with the provided fields"""
        fields["project"] = {"key": self._project}
        return self._jira.create_issue(fields=fields)
