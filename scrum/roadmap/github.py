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
            self._repos = self._org.get_repos(type='public')
        self.logger = Logger()

    def get_unreviewed_pulls(self):
        """Return a list of all unreviewed pulls"""
        open_reviews = []
        if self._team:
            review_members = self._team.get_members()
        else:
            review_members = self._org.get_members()
        for repo in self._repos:
            if repo.private:
                self.logger.info(f"Skipping private repo: {repo}")
                continue
            self.logger.info(f"Checking: {repo}")
            pulls = repo.get_pulls()
            self.logger.debug(f"Reviewing: {[pull for pull in pulls]}")
            for pull in pulls:
                if pull.draft:
                    self.logger.debug(f"Skipping Draft: {pull}")
                    continue
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
                if team_review.commit_id != commits[0].commit.sha:
                    reason = "Commit modified"
                    self.logger.debug(f"Needs Review ({reason}): {pull}")
                    open_reviews.append(PullRequest(pull, reason))
                    continue
                self.logger.debug(f"Skipping: {pull}")
        return open_reviews


class PullRequest:
    def __init__(self, pull, reason=None):
        self.reason = reason
        self.url = pull.html_url
        self.title = pull.title
        self.body = pull.body
        self.number = pull.number
