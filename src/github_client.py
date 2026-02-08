from github import Github
import base64

class GitHubClient:
    def __init__(self, token: str, repo_name: str):
        """
        Initialize the GitHub client.
        :param token: GitHub Personal Access Token.
        :param repo_name: Repository name in 'owner/repo' format.
        """
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

    def get_file_content(self, path: str) -> str:
        """
        Get the content of a file from the repository.
        """
        file_content = self.repo.get_contents(path)
        return base64.b64decode(file_content.content).decode('utf-8')

    def update_file(self, path: str, content: str, commit_message: str):
        """
        Update a file in the repository.
        """
        try:
            # Get the current file to get its SHA
            file = self.repo.get_contents(path)
            self.repo.update_file(path, commit_message, content, file.sha)
        except Exception as e:
            # If the file doesn't exist, create it
            if "404" in str(e):
                self.repo.create_file(path, commit_message, content)
            else:
                raise e

    def list_files(self, directory: str) -> list:
        """
        List all files in a directory.
        """
        try:
            contents = self.repo.get_contents(directory)
            return [file.path for file in contents if file.type == 'file']
        except Exception as e:
            if "404" in str(e):
                return []
            raise e
