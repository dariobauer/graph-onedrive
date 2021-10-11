import graph_onedrive


def main():
    """Interact with Microsoft Onedrive."""

    # Set config
    client_id: str = ""
    client_secret: str = ""
    tenant: str = "common"  # Optional, default set
    redirect_url: str = "http://localhost:8080"  # Optional, default set
    refresh_token: str = ""  # Optional: from last session

    # Create session instance
    onedrive = graph_onedrive.create(
        client_id, client_secret, tenant, redirect_url, refresh_token
    )

    # Complete tasks using the instance. For this example we will just display the usage
    onedrive.get_usage(verbose=True)

    # OPTIONAL: Get refresh token that can be saved somewhere to recreate session
    refresh_token = onedrive.refresh_token


if __name__ == "__main__":
    main()
