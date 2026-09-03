import httpx
import pytest
from pytest_mock import MockerFixture

from runboat.exceptions import NotFoundOnGitHub
from runboat.github import has_norunboat


@pytest.mark.asyncio
async def test_has_norunboat_true(mocker: MockerFixture) -> None:
    mocker.patch(
        "runboat.github._github_request",
        return_value={"name": "norunboat", "type": "file"},
    )
    assert await has_norunboat("oca/mis-builder", "abc123") is True


@pytest.mark.asyncio
async def test_has_norunboat_false(mocker: MockerFixture) -> None:
    mocker.patch(
        "runboat.github._github_request",
        side_effect=NotFoundOnGitHub("missing"),
    )
    assert await has_norunboat("oca/mis-builder", "abc123") is False


@pytest.mark.asyncio
async def test_has_norunboat_propagates_other_errors(mocker: MockerFixture) -> None:
    response = httpx.Response(500, request=httpx.Request("GET", "https://api.github.com"))
    mocker.patch(
        "runboat.github._github_request",
        side_effect=httpx.HTTPStatusError(
            "boom", request=response.request, response=response
        ),
    )
    with pytest.raises(httpx.HTTPStatusError):
        await has_norunboat("oca/mis-builder", "abc123")
