import datetime

import pytest
from pytest_mock import MockerFixture

from runboat.controller import Controller
from runboat.github import CommitInfo
from runboat.models import Build, BuildInitStatus, BuildStatus


def _build(
    name: str,
    *,
    repo: str = "oca/mis-builder",
    target_branch: str = "15.0",
    pr: int | None = None,
    git_commit: str = "aaaaaaa",
) -> Build:
    return Build(
        name=name,
        deployment_name=f"{name}-odoo",
        commit_info=CommitInfo(
            repo=repo,
            target_branch=target_branch,
            pr=pr,
            git_commit=git_commit,
        ),
        status=BuildStatus.stopped,
        init_status=BuildInitStatus.succeeded,
        desired_replicas=0,
        last_scaled=datetime.datetime(2021, 10, 1, 12, 0, 0),
        created=datetime.datetime(2021, 10, 1, 11, 0, 0),
    )


@pytest.mark.asyncio
async def test_deploy_commit_skips_when_norunboat(mocker: MockerFixture) -> None:
    ctrl = Controller()
    mocker.patch("runboat.controller.has_norunboat", return_value=True)
    deploy = mocker.patch("runboat.controller.Build.deploy")
    await ctrl.deploy_commit(
        CommitInfo(repo="oca/mis-builder", target_branch="15.0", pr=None, git_commit="abc")
    )
    deploy.assert_not_called()


@pytest.mark.asyncio
async def test_deploy_commit_undeploys_previous_branch_builds(
    mocker: MockerFixture,
) -> None:
    ctrl = Controller()
    old = _build("old", git_commit="oldcommit")
    ctrl.db.add(old)
    mocker.patch("runboat.controller.has_norunboat", return_value=False)
    mocker.patch("runboat.controller.Build.deploy")
    undeploy = mocker.patch.object(Build, "undeploy")
    await ctrl.deploy_commit(
        CommitInfo(
            repo="oca/mis-builder",
            target_branch="15.0",
            pr=None,
            git_commit="newcommit",
        )
    )
    undeploy.assert_awaited_once()
    assert undeploy.await_args is not None
    assert undeploy.await_args.args == ()  # called on instance


@pytest.mark.asyncio
async def test_deploy_commit_undeploys_previous_pr_builds(
    mocker: MockerFixture,
) -> None:
    ctrl = Controller()
    old = _build("old-pr", pr=12, git_commit="oldcommit")
    ctrl.db.add(old)
    mocker.patch("runboat.controller.has_norunboat", return_value=False)
    mocker.patch("runboat.controller.Build.deploy")
    undeploy = mocker.patch.object(Build, "undeploy")
    await ctrl.deploy_commit(
        CommitInfo(
            repo="oca/mis-builder",
            target_branch="15.0",
            pr=12,
            git_commit="newcommit",
        )
    )
    undeploy.assert_awaited_once()


@pytest.mark.asyncio
async def test_deploy_commit_noop_when_commit_already_deployed(
    mocker: MockerFixture,
) -> None:
    ctrl = Controller()
    existing = _build("same", git_commit="samecommit")
    ctrl.db.add(existing)
    mocker.patch("runboat.controller.has_norunboat", return_value=False)
    deploy = mocker.patch("runboat.controller.Build.deploy")
    undeploy = mocker.patch.object(Build, "undeploy")
    await ctrl.deploy_commit(
        CommitInfo(
            repo="oca/mis-builder",
            target_branch="15.0",
            pr=None,
            git_commit="samecommit",
        )
    )
    deploy.assert_not_called()
    undeploy.assert_not_called()
