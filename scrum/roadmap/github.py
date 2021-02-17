from github import Github

from roadmap.logging import Logger


class RepoGroup:
    def __init__(self, api_key, org, team=None):
        self._github = Github(api_key)
        self._repos = []
        self._team = None
        self._org = self._github.get_organization(org)
        if team:
            self._team = self._org.get_team_by_slug(team)
            self._repos = self._team.get_repos()
        else:
            self._repos = self._org.get_repos()
        self.logger = Logger()

    def get_unreviewed_pulls(self):
        """Return a list of all unreviewed pulls"""
        open_reviews = []
        if self._team:
            review_members = self._team.get_members()
        else:
            review_members = self._org.get_members()
        for repo in self._repos:
            pulls = repo.get_pulls()
            for pull in pulls:
                reviews = pull.get_reviews().reversed
                if not reviews.totalCount:
                    reason = "No review"
                    self.logger.debug(f"Needs Review ({reason}): {pull}")
                    open_reviews.append(PullRequest(pull, reason))
                    continue
                team_review = None
                for review in reviews:
                    if review.user in review_members:
                        team_review = review
                        break
                if not team_review:
                    reason = "No team review"
                    self.logger.debug(f"Needs Review ({reason}): {pull}")
                    open_reviews.append(PullRequest(pull, reason))
                    continue
                commits = pull.get_commits().reversed
                if team_review.submitted_at < commits[0].commit.author.date:
                    reason = "New commits"
                    self.logger.debug(f"Needs Review ({reason}): {pull}")
                    open_reviews.append(PullRequest(pull, reason))
                    continue
        return open_reviews


class PullRequest:
    def __init__(self, pull, reason=None):
        self.reason = reason
        self.url = pull.html_url
        self.title = pull.title
        self.body = pull.body
