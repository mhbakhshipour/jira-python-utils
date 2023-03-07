from enum import Enum

from rest_framework.request import Request
from jira import JIRA

from django.conf import settings


class Source(Enum):
    A = "a"
    B = "b"


class Jira:
    """
    Wrapper class for the Jira API, providing methods for interacting with Jira issues, comments,
    transitions, sprints, and boards. This class implements the singleton pattern, meaning that 
    only one instance of the class will exist at a time.

    :param request: Request object containing information about the user making the API call.
    :type request: Request
    :param source: Source of the Jira instance (A or B).
    :type source: Source

    :ivar source: Source of the Jira instance.
    :ivar request: Request object containing information about the user making the API call.
    :ivar auth_jira: JIRA object representing the authenticated connection to the Jira API.
    """

    _instance = None

    def __init__(self, request: Request, source: Source) -> None:
        """
        Wrapper class for the Jira API, providing methods for interacting with Jira issues, comments,
        transitions, sprints, and boards. This class implements the singleton pattern, meaning that 
        only one instance of the class will exist at a time.

        :param request: Request object containing information about the user making the API call.
        :type request: Request
        :param source: Source of the Jira instance (A or B).
        :type source: Source

        :ivar source: Source of the Jira instance.
        :ivar request: Request object containing information about the user making the API call.
        :ivar auth_jira: JIRA object representing the authenticated connection to the Jira API.
        """

        self.source = source
        self.request = request
        self.auth_jira = self.__define_connection_source()

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern implementation to ensure only one instance of the JIRA client is created during runtime.
        """

        if not cls._instance:
            cls._instance = super(Jira, cls).__new__(cls)
        return cls._instance

    def __define_connection_source(self) -> JIRA:
        """
        Method to define the JIRA connection source based on the provided source enum.

        :raises ValueError: If an invalid source is provided.
        """

        if self.source == Source.A:
            auth_jira = self.__connect_to_a()
        elif self.source == Source.B:
            auth_jira = self.__connect_to_b()
        else:
            raise ValueError("Invalid source: {}".format(self.source))
        return auth_jira

    def __connect_to_b(self) -> JIRA:
        """
        Connects to the B JIRA instance.

        :return: JIRA object representing the authenticated connection to the B JIRA instance.
        """

        auth_jira = JIRA(
            options={
                "server": settings.B["url"],
                "verify": False,
                "headers": {"contextUser": self.request.user.username}
            },
            basic_auth=(settings.B["username"],
                        settings.B["password"])
        )
        return auth_jira

    def __connect_to_a(self) -> JIRA:
        """
        Connects to the A JIRA instance.

        :return: JIRA object representing the authenticated connection to the A JIRA instance.
        """

        auth_jira = JIRA(
            options={
                "server": settings.A["url"],
                "verify": False,
                "headers": {"contextUser": self.request.user.username}
            },
            basic_auth=(settings.A["username"], settings.A["password"])
        )
        return auth_jira

    def create_ticket(self, data: dict) -> str:
        """
        Creates a new ticket in Jira and returns its key.

        :param data: Dictionary containing information about the ticket to be created.
        :type data: dict
        :return: Key of the newly created ticket.
        :rtype: str
        """

        if self.source == Source.A:
            issue = self.__create_ticket_in_a(data)
        elif self.source == Source.B:
            issue = self.__create_ticket_in_b(data)
        else:
            raise ValueError("Invalid source: {}".format(self.source))
        return issue.key

    def __create_ticket_in_a(self, data: dict) -> str:
        """
        Creates a new ticket in Jira and returns its key.

        :param data: Dictionary containing information about the ticket to be created.
        :type data: dict
        :return: Key of the newly created ticket.
        :rtype: str
        """

        issue = self.auth_jira.create_issue(
            project={"id": data["product_id"]},
            issuetype={"id": 10001},
            summary=data["name"],
        )
        return issue.key

    def __create_ticket_in_b(self, data: dict) -> str:
        """
        Creates a new ticket in Jira and returns its key.

        :param data: Dictionary containing information about the ticket to be created.
        :type data: dict
        :return: Key of the newly created ticket.
        :rtype: str
        """

        issue = self.auth_jira.create_issue(
            project={"id": 10407},
            issuetype={"id": 16704},
            summary=data["name"],
            reporter={"name": self.request.user.username},
            customfield_23249="{} , {}, {}".format(
                data["as_a"], data["i_want"], data["so_that"]),
            customfield_23250=data["product"].get("name"),
            priority={"id": "2"} if data["is_high_priority"] else {
                "id": "4"},
        )
        return issue.key

    def add_comment(self, comment: str, issue_key: str) -> None:
        """
        Adds a comment to the specified Jira issue.

        :param comment: Text of the comment to be added.
        :type comment: str
        :param issue_key: Key of the Jira issue to add the comment to.
        :type issue_key: str
        """

        self.auth_jira.add_comment(issue_key, comment)

    def change_transition(self, transition: int, issue_key: str) -> None:
        """
        Changes the status of the specified Jira issue to the specified transition.

        :param transition: ID of the transition to change the issue status to.
        :type transition: int
        :param issue_key: Key of the Jira issue to change the status of.
        :type issue_key: str
        """

        self.auth_jira.transition_issue(issue=issue_key, transition=transition)

    def add_issues_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        """
        Adds the specified issues to the specified Jira sprint.

        :param sprint_id: ID of the sprint to add the issues to.
        :type sprint_id: int
        :param issue_keys: List of issue keys to add to the sprint.
        :type issue_keys: list[str]
        """

        self.auth_jira.add_issues_to_sprint(sprint_id, issue_keys)

    def get_first_board(self, product_id: int) -> int:
        """
        Returns the ID of the first board associated with the specified Jira project.

        :param product_id: ID of the Jira project to retrieve the first board for.
        :type product_id: int
        :return: ID of the first board associated with the project.
        :rtype: int
        """

        board_id = self.auth_jira.boards(projectKeyOrID=product_id)[0].id
        return board_id

    def get_sprints(self, board_id: int, state: str) -> list[dict]:
        """
        Returns a list of sprints for a given board.

        :param board_id: ID of the board.
        :type board_id: int
        :param state: State of the sprints to retrieve (e.g. "active", "future", "closed)
        :type state: str
        :return: List of sprints for the given board.
        :rtype: List[dict]
        """

        res = self.auth_jira.sprints(board_id, state=state)

        sprints = self.__sprint_serializer(res)

        return sprints

    def __sprint_serializer(self, data) -> list[dict]:
        sprints = []
        for s in data:
            sprint = {"id": s.id, "name": s.name, "state": s.state,
                      "startDate": s.startDate, "endDate": s.endDate}
            sprints.append(sprint)

        return sprints

    def search_issues(self, jql: str, fields: list[str], start_at: int) -> dict:
        res = self.auth_jira.search_issues(
            jql, fields=fields, json_result=True, startAt=start_at, maxResults=10)

        issues = self.__normalize_jira_issues_response(res)

        return issues

    def __normalize_jira_user_response(self, jira_response: dict) -> dict:
        data = {}
        data["username"] = jira_response["name"]
        data["email"] = jira_response["emailAddress"]
        data["avatar"] = jira_response["avatarUrls"]["48x48"]
        data["full_name"] = jira_response["displayName"]
        return data

    def __normalize_jira_issues_response(self, jira_response) -> list[dict]:
        if "expand" in jira_response:
            del jira_response["expand"]

        issues = []
        for i in jira_response["issues"]:
            issue = {}
            issue["key"] = i["key"]
            issue["summary"] = i["fields"]["summary"]
            issue["reporter"] = (
                self.__normalize_jira_user_response(
                    i["fields"]["reporter"])
                if i["fields"].get("reporter", None)
                else None
            )
            issue["status"] = i["fields"]["status"].get("name", None)
            issue["priority"] = i["fields"]["priority"].get("name", None)
            issue["created"] = i["fields"].get("created", None)

            issues.append(issue)
        return issues
