from operator import attrgetter


from jira import JIRA
from roadmap.logging import Logger


class Lanes:
    TODO = "To Do"
    DOING = "In Progress"
    REVIEW = "Needs Review"
    DONE = "Done"


class IssueTypes:
    TASK = "Task"
    SUBTASK = "Sub-Task"
    BUG = "Bug"
    STORY = "Story"
    EPIC = "Epic"


class Labels:
    EXT_PR = "external-pr"
    FOLLOW_UP = "follow-up"
    REVIEW_ACK = "approved"
    REVIEW_NAK = "changes-requested"
    MERGE_BLOCKED = "merge-blocked"
    MERGE_DIRTY = "needs-rebase"
    MERGE_UNSTABLE = "tests-failing"


class Fields:
    STORY_POINT = "customfield_10016"
    EPIC_NAME = "customfield_10011"
    EPIC_LINK = "customfield_10014"
    SPRINT = "customfield_10020"


class Project:
    INCLUDE_LABELS = ["21.10"]

    def __init__(self, server, api_key, email, project, dry_run=False):
        self._jira = JIRA(server,
                          basic_auth=(email, api_key),
                          options={"agile_rest_path": "agile"})
        self._project = project
        self.board = self._jira.boards(projectKeyOrID=project)[0]
        self.logger = Logger()
        self.dry_run = dry_run

    @property
    def all_issues(self):
        if self._all_issues is None:
            self._all_issues = self.search()
        return self._all_issues

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

    def links(self, issue):
        """Find all links for on a given issue."""
        return {link.raw["object"]["url"] for link in self._jira.remote_links(issue)}

    def sprint(self, state):
        """Return the most recent sprint of the given state, or None."""
        sprints = self._jira.sprints(self.board.id, state=state)
        sprints.sort(key=attrgetter("startDate"), reverse=True)
        return sprints[0] if sprints else None

    def _build_labels(self, pr):
        """Build a list of the appropriate labels based on PR state."""
        labels = [Labels.EXT_PR]
        if pr.review_state == "APPROVED":
            labels.append(Labels.REVIEW_ACK)
        if pr.review_state == "CHANGES_REQUESTED":
            labels.append(Labels.REVIEW_NAK)
        if pr.merge_state == "blocked":
            labels.append(Labels.MERGE_BLOCKED)
        if pr.merge_state == "dirty":
            labels.append(Labels.MERGE_DIRTY)
        if pr.merge_state == "unstable":
            labels.append(Labels.MERGE_UNSTABLE)
        return labels

    def import_external_prs(self, prs):
        """Create project issues given trello exports"""
        active_sprint = self.sprint("active")
        if not active_sprint:
            self.logger.error(f"No active sprint for {self._project}")
            return
        issues = {task.fields.summary: task
                  for task in self.search(f"labels = {Labels.EXT_PR}")}
        for pr in prs:
            jira_title = f"{pr.title} ({pr.repo_name} #{pr.number})"
            labels = self._build_labels(pr)
            if issue := issues.get(jira_title):
                self.logger.debug(f"Found existing issue {issue.key}: {jira_title}")
                if issue.fields.status.name in {Lanes.REVIEW, Lanes.DONE}:
                    self.move_to_lane(issue, Lanes.TODO)
                    self.add_comment(issue, f"Needs review: {pr.reason}")
                self.ensure_labels(issue, labels)
            else:
                issue = self.create_issue({
                    "summary": jira_title,
                    "description": pr.body,
                    "labels": labels,
                    Fields.SPRINT: active_sprint.id,
                    "issuetype": {"name": IssueTypes.TASK},
                })
                self.add_comment(issue, f"Needs review: {pr.reason}")
            self.ensure_link(issue, pr.url)

    def import_trello_issues(self, issues):
        """Create project issues given trello exports"""
        trello_issues = list(issues)
        all_issues = self.search()
        # import pprint

        # for testissue in all_issues:
        #     if "Leaked systemd units" in testissue.fields.summary:
        #         pprint.pprint(vars(testissue))
        #         for link in self._jira.remote_links(testissue.id):
        #             pprint.pprint(vars(link))
        #         return
        for issue in trello_issues:
            fields = {
                "summary": issue.name,
                "description": issue.description,
            }
            if issue.epic:
                # Epic only fields
                fields[Fields.EPIC_NAME] = issue.name
            else:
                # Story only fields
                if issue.story_points:
                    fields[fields.STORY_POINT] = float(issue.story_points)
            # Add labels
            labels = []
            for label in issue.labels:
                if label.name in self.INCLUDE_LABELS:
                    labels.append(label.name)
            if labels:
                fields["labels"] = labels

            # Update or create issue
            jira_issue = None
            for existing_issue in all_issues:
                if existing_issue.fields.summary == issue.name:
                    self.logger.debug(f"Updating existing issue: {issue.name}")
                    existing_issue.update(fields)
                    jira_issue = existing_issue
                    break
            else:
                # Create new issue
                fields["issuetype"] = {"name": "Epic" if issue.epic else "Story"}
                jira_issue = self.create_issue(fields)

            # Add links
            for attachment in issue.attachments:
                if not attachment.url:
                    # No attachement
                    continue
                if attachment.url.startswith("https://trello.com"):
                    # Jira card link
                    # these were used in the Jira workflow to simulate epics
                    continue
                self.ensure_link(jira_issue, attachment.url)

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

                fields = {Fields.EPIC_LINK: epic_key}
                jira_issue.update(fields)
                self.logger.info(f"Added {epic_key} to {jira_issue}")

    def create_issue(self, fields):
        """Create an issue with the provided fields"""
        if self.dry_run:
            self.logger.debug(f"Would create issue: {fields['summary']}")
            return
        self.logger.debug(f"Creating issue: {fields['summary']}")
        fields["project"] = {"key": self._project}
        issue = self._jira.create_issue(fields=fields)
        self.logger.debug(f"Created issue {issue.key}: {issue.fields.summary}")
        return issue

    def ensure_labels(self, issue, labels):
        """Update an existing issue with the provided fields"""
        if set(labels) == set(issue.fields.labels):
            return
        if self.dry_run:
            self.logger.debug(f"Would update labels {issue.key}:"
                              f" {issue.fields.labels} -> {labels}")
            return
        self.logger.debug(f"Updating issue {issue.key}:"
                          f" {issue.fields.labels} -> {labels}")
        issue.update({"labels": labels})

    def move_to_lane(self, issue, lane):
        """Move a given issue to a specific lane."""
        if self.dry_run:
            self.logger.debug(f"Would move issue {issue.key} to: {lane}")
            return
        self.logger.debug(f"Moving issue {issue.key} to: {lane}")
        issue.update({"status": {"name": lane}})

    def add_comment(self, issue, comment):
        """Add a comment to an issue."""
        if self.dry_run:
            # issue might be None during dry-run
            issue_key = issue.key if issue else f"{self._project}-??"
            self.logger.debug(f"Would add comment to {issue_key}: {comment}")
            return
        self.logger.debug(f"Adding comment to {issue.key}: {comment}")
        self._jira.add_comment(issue, comment, is_internal=True)

    def ensure_link(self, issue, url):
        """Add a link to an issue."""
        if issue and url in self.links(issue):  # issue might be None in dry-run
            self.logger.debug(f"Link already on issue {issue.key}: {url}")
            return
        if self.dry_run:
            # issue might be None during dry-run
            issue_key = issue.key if issue else f"{self._project}-??"
            self.logger.debug(f"Would add link to issue {issue_key}: {url}")
            return
        self.logger.debug(f"Adding link to issue {issue.key}: {url}")
        self._jira.add_simple_link(issue.id, {"title": url, "url": url})
