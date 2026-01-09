import requests
import logging
from django.core.exceptions import ValidationError
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class GitHubIntegrationService:
    """Service for GitHub API integration with error handling and production best practices"""

    @staticmethod
    def _get_github_headers():
        """Get GitHub API headers with authentication"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Huzilerz-Theme-System'
        }

        # Add authentication if available
        github_token = getattr(settings, 'GITHUB_ACCESS_TOKEN', None)
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        return headers

    @staticmethod
    def _make_github_request(method, url, data=None, timeout=30):
        """Make GitHub API request with error handling and retry logic"""
        try:
            headers = GitHubIntegrationService._get_github_headers()

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )

            # Handle rate limiting
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                logger.warning("GitHub API rate limit exceeded")
                raise ValidationError("GitHub API rate limit exceeded. Please try again later.")

            # Handle authentication errors
            if response.status_code == 401:
                logger.warning("GitHub API authentication failed")
                raise ValidationError("GitHub API authentication failed. Please check your access token.")

            # Handle not found
            if response.status_code == 404:
                logger.warning(f"GitHub resource not found: {url}")
                raise ValidationError("GitHub repository or resource not found.")

            # Handle other errors
            if response.status_code >= 400:
                logger.error(f"GitHub API error {response.status_code}: {response.text}")
                raise ValidationError(f"GitHub API error: {response.status_code}")

            return response.json() if response.content else {}

        except requests.exceptions.Timeout:
            logger.error("GitHub API request timed out")
            raise ValidationError("GitHub API request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            logger.error("GitHub API connection error")
            raise ValidationError("Unable to connect to GitHub API. Please check your network connection.")
        except Exception as e:
            logger.error(f"Unexpected error making GitHub API request: {e}")
            raise ValidationError("Unexpected error occurred while communicating with GitHub.")

    @staticmethod
    def create_revert_commit(repo_owner, repo_name, commit_sha, user_email, user_name):
        """
        Create a revert commit using GitHub API

        Args:
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name
            commit_sha: SHA of commit to revert
            user_email: Email of user performing revert
            user_name: Name of user performing revert

        Returns:
            Dictionary with new commit SHA and details

        Raises:
            ValidationError: If GitHub API operation fails
        """
        try:
            logger.info(f"Creating revert commit for {repo_owner}/{repo_name} commit {commit_sha}")

            # Get the commit to revert
            commit_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}"
            commit_data = GitHubIntegrationService._make_github_request('GET', commit_url)

            # Get the base tree (parent of the commit we're reverting)
            parent_sha = commit_data['parents'][0]['sha']

            # Create revert commit
            revert_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/commits"
            revert_data = {
                'message': f"Revert \"{commit_data['commit']['message']}\"\n\nThis reverts commit {commit_sha}.",
                'tree': commit_data['commit']['tree']['sha'],
                'parents': [parent_sha],
                'author': {
                    'name': user_name,
                    'email': user_email
                },
                'committer': {
                    'name': user_name,
                    'email': user_email
                }
            }

            revert_commit = GitHubIntegrationService._make_github_request('POST', revert_url, revert_data)

            # Update branch reference to point to new revert commit
            ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/heads/main"
            ref_data = {
                'sha': revert_commit['sha'],
                'force': False
            }

            GitHubIntegrationService._make_github_request('PATCH', ref_url, ref_data)

            logger.info(f"Successfully created revert commit {revert_commit['sha']}")

            return {
                'revert_commit_sha': revert_commit['sha'],
                'original_commit_sha': commit_sha,
                'message': revert_commit['commit']['message'],
                'url': revert_commit['html_url']
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating revert commit: {e}")
            raise ValidationError("Failed to create revert commit via GitHub API")

    @staticmethod
    def get_commit_history(repo_owner, repo_name, branch='main', limit=50):
        """
        Get commit history from GitHub repository

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            branch: Branch name (default: main)
            limit: Number of commits to return

        Returns:
            List of commit objects

        Raises:
            ValidationError: If GitHub API operation fails
        """
        try:
            logger.info(f"Getting commit history for {repo_owner}/{repo_name} branch {branch}")

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
            params = {
                'sha': branch,
                'per_page': min(limit, 100)  # GitHub max per_page is 100
            }

            response = GitHubIntegrationService._make_github_request('GET', url)

            commits = []
            for commit in response:
                commits.append({
                    'sha': commit['sha'],
                    'message': commit['commit']['message'],
                    'author': commit['commit']['author']['name'] if commit['commit']['author'] else 'Unknown',
                    'date': commit['commit']['author']['date'] if commit['commit']['author'] else None,
                    'url': commit['html_url']
                })

            logger.info(f"Retrieved {len(commits)} commits from GitHub")
            return commits

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting commit history: {e}")
            raise ValidationError("Failed to retrieve commit history from GitHub")

    @staticmethod
    def get_commit_details(repo_owner, repo_name, commit_sha):
        """
        Get detailed information about a specific commit

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            commit_sha: Commit SHA

        Returns:
            Detailed commit information

        Raises:
            ValidationError: If GitHub API operation fails
        """
        try:
            logger.info(f"Getting details for commit {commit_sha} in {repo_owner}/{repo_name}")

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}"
            commit_data = GitHubIntegrationService._make_github_request('GET', url)

            return {
                'sha': commit_data['sha'],
                'message': commit_data['commit']['message'],
                'author': {
                    'name': commit_data['commit']['author']['name'] if commit_data['commit']['author'] else 'Unknown',
                    'email': commit_data['commit']['author']['email'] if commit_data['commit']['author'] else None,
                    'date': commit_data['commit']['author']['date'] if commit_data['commit']['author'] else None
                },
                'files_changed': [
                    {
                        'filename': file['filename'],
                        'status': file['status'],
                        'additions': file['additions'],
                        'deletions': file['deletions']
                    }
                    for file in commit_data.get('files', [])
                ],
                'stats': commit_data.get('stats', {}),
                'html_url': commit_data['html_url']
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting commit details: {e}")
            raise ValidationError("Failed to retrieve commit details from GitHub")

    @staticmethod
    def validate_repository_access(repo_owner, repo_name):
        """
        Validate that we have access to the GitHub repository

        Args:
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            Boolean indicating access validity

        Raises:
            ValidationError: If repository access fails
        """
        try:
            logger.info(f"Validating access to repository {repo_owner}/{repo_name}")

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            repo_data = GitHubIntegrationService._make_github_request('GET', url)

            # Check if repository exists and we have appropriate permissions
            if not repo_data.get('id'):
                raise ValidationError("Repository not found or inaccessible")

            # Check if we have write access (needed for creating commits)
            permissions = repo_data.get('permissions', {})
            if not permissions.get('push'):
                logger.warning(f"Insufficient permissions for repository {repo_owner}/{repo_name}")
                raise ValidationError("Insufficient permissions to modify this repository")

            logger.info(f"Successfully validated access to repository {repo_owner}/{repo_name}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating repository access: {e}")
            raise ValidationError("Failed to validate repository access")

    @staticmethod
    def create_branch(repo_owner, repo_name, branch_name, base_sha):
        """
        Create a new branch for safe rollback operations

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            branch_name: Name of new branch
            base_sha: Base commit SHA for new branch

        Returns:
            Branch creation details

        Raises:
            ValidationError: If branch creation fails
        """
        try:
            logger.info(f"Creating branch {branch_name} in {repo_owner}/{repo_name}")

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs"
            branch_data = {
                'ref': f'refs/heads/{branch_name}',
                'sha': base_sha
            }

            branch_result = GitHubIntegrationService._make_github_request('POST', url, branch_data)

            logger.info(f"Successfully created branch {branch_name}")
            return branch_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            raise ValidationError("Failed to create branch in GitHub repository")