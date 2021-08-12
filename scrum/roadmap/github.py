from datetime import datetime, timedelta
from itertools import chain

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

    def _check_pr(self, pr, members):
        """Check whether a PR should be included or not."""
        if pr.user in members:
            return (False, "internal PR")
        if pr.draft:
            return (False, "draft")
        reviews = pr.get_reviews().reversed
        if not reviews.totalCount:
            return (True, "no reviews")
        try:
            team_review = next(review
                               for review in reviews
                               if review.user in members
                               and review.submitted_at)
        except StopIteration:
            return (True, "no team reviews")
        commits = pr.get_commits().reversed
        if team_review.submitted_at < commits[0].commit.author.date:
            return (True, "new commits")
        if team_review.commit_id != commits[0].commit.sha:
            return (True, "updated commits")
        new_comments = [c
                        for c in chain(pr.get_comments(),
                                       pr.get_issue_comments(),
                                       pr.get_review_comments())
                        if c.user not in members
                        and c.created_at > team_review.submitted_at]
        new_reviews = [r
                       for r in reviews
                       if r.user not in members
                       and r.submitted_at > team_review.submitted_at]
        if new_comments or new_reviews:
            return (True, "updated")
        if datetime.now() - team_review.submitted_at > timedelta(weeks=1):
            return (True, "follow-up")
        return (False, "reviewed")

    def _check_repo(self, repo):
        """Check whether a repo should be checked for PRs or not."""
        if repo.private:
            return (False, "private")
        if not repo.get_pulls().totalCount:
            return (False, "no PRs")
        return (True, None)

    def get_external_prs(self):
        """Return a list of all PRs submitted by external contributors."""
        open_reviews = []
        if self._team:
            members = self._team.get_members()
        else:
            members = self._org.get_members()
        for repo in self._repos:
            should_check, reason = self._check_repo(repo)
            if should_check:
                self.logger.info(f"Checking repo {repo.full_name}")
            else:
                self.logger.info(f"Skipping repo {repo.full_name}: {reason}")
                continue
            for pull in repo.get_pulls():
                should_review, reason = self._check_pr(pull, members)
                if should_review:
                    self.logger.debug(f"Needs Review ({reason}): {pull}")
                    open_reviews.append(PullRequest(pull, repo, reason))
                else:
                    self.logger.debug(f"Skipping ({reason}): {pull}")
        num_reviews = len(open_reviews)
        self.logger.debug(f"Found {num_reviews} PR{'s' if num_reviews != 1 else ''}")
        return open_reviews


class PullRequest:
    def __init__(self, pull, repo, reason):
        self.reason = reason
        self.url = pull.html_url
        self.title = pull.title
        self.body = pull.body
        self.number = pull.number
        self.status = pull.state
        self.repo_name = repo.name
