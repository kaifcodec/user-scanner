from user_scanner.core.orchestrator import generic_validate, Result


def validate_huggingface(user):
    url = f"https://huggingface.co/api/users/{user}/overview"
    show_url = f"https://huggingface.co/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                if data.get("fullname"):
                    extra["name"] = data.get("fullname").strip()
                if data.get("numModels") is not None:
                    extra["models"] = data.get("numModels")
                if data.get("numDatasets") is not None:
                    extra["datasets"] = data.get("numDatasets")
                if data.get("numSpaces") is not None:
                    extra["spaces"] = data.get("numSpaces")
                if data.get("numFollowers") is not None:
                    extra["followers"] = data.get("numFollowers")
                if data.get("numFollowing") is not None:
                    extra["following"] = data.get("numFollowing")
                if data.get("avatarUrl"):
                    avatar = data.get("avatarUrl")
                    if avatar.startswith("/"):
                        avatar = "https://huggingface.co" + avatar
                    extra["avatar"] = avatar
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)

