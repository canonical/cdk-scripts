from jira import JIRA

from roadmap.logging import Logger


class Project:
    def __init__(self, server, api_key, email, project):
        self._jira = JIRA(server, basic_auth=(email, api_key))
        self._project = project
        self.logger = Logger()

    @property
    def all_issues(self):
        return self.search()

    def search(self, jql="", sort=""):
        """Perofrm a JQL search on the project"""

        query = [f"project={self._project}"]

        if jql:
            query.append(jql)
        if sort:
            query.append(sort)
        else:
            query.append("ORDER BY created DESC")

        query = ' '.join(query)
        self.logger.debug(f"Performing Search: {query}")
        return self._jira.search_issues(query)

    def import_trello_issues(self, issues):
        """Create project issues given trello exports"""
        issues = list(issues)
        test_issue = issues[0]
        import pprint
        pprint.pprint(vars(test_issue))
        fields = {"summary": test_issue.name,
                  "description": test_issue.description,
                  "issuetype": {'name': "Epic" if test_issue.epic else "Story"},
                  }
        self.create_issue(fields)

    def create_issue(self, fields):
        """Create an issue with the provided fields"""
        fields['project'] = {'id': self._project}
        return self._jira.create_issue(fields=fields)

